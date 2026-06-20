// Package test contains the "floci" infra unit tests for the todo-app Helm
// chart. These tests render the chart with Terratest's helm.RenderTemplate
// (no live cluster required) and assert the architectural invariants:
//
//   - the API Deployment exists and serves on port 8000 with /health probes;
//   - each workload ServiceAccount carries its own IRSA role-arn annotation
//     (no shared role);
//   - the Atlas DB-init Job is a Helm pre-install hook, decoupled from the
//     API Deployment (so migrations never race across replicas).
package test

import (
	"path/filepath"
	"strings"
	"testing"

	"github.com/gruntwork-io/terratest/modules/helm"
	"github.com/stretchr/testify/require"
	appsv1 "k8s.io/api/apps/v1"
	batchv1 "k8s.io/api/batch/v1"
	corev1 "k8s.io/api/core/v1"
)

// chartPath resolves the chart relative to this test file (infra/tests/terratest
// -> infra/k8s/helm).
func chartPath(t *testing.T) string {
	p, err := filepath.Abs("../../k8s/helm")
	require.NoError(t, err)
	return p
}

func devOptions() *helm.Options {
	return &helm.Options{
		ValuesFiles: []string{"values-dev.yaml"},
		SetValues: map[string]string{
			"serviceAccounts.api.roleArn":    "arn:aws:iam::123456789012:role/todo-app-dev-api",
			"serviceAccounts.ai.roleArn":     "arn:aws:iam::123456789012:role/todo-app-dev-ai",
			"serviceAccounts.dbInit.roleArn": "arn:aws:iam::123456789012:role/todo-app-dev-db-init",
		},
	}
}

// TestDeploymentRendered asserts the API Deployment exists, runs the expected
// image on port 8000, and probes /health.
func TestDeploymentRendered(t *testing.T) {
	t.Parallel()
	out := helm.RenderTemplate(t, devOptions(), chartPath(t), "todo-app",
		[]string{"templates/deployment.yaml"})

	var dep appsv1.Deployment
	helm.UnmarshalK8SYaml(t, out, &dep)

	require.Equal(t, "Deployment", dep.Kind)
	require.Len(t, dep.Spec.Template.Spec.Containers, 1)

	c := dep.Spec.Template.Spec.Containers[0]
	require.True(t, strings.HasPrefix(c.Image, "local/todo-app:"),
		"image should be the local/todo-app repo, got %q", c.Image)

	require.Len(t, c.Ports, 1)
	require.Equal(t, int32(8000), c.Ports[0].ContainerPort)

	require.NotNil(t, c.ReadinessProbe)
	require.NotNil(t, c.ReadinessProbe.HTTPGet)
	require.Equal(t, "/health", c.ReadinessProbe.HTTPGet.Path)
	require.NotNil(t, c.LivenessProbe)
	require.Equal(t, "/health", c.LivenessProbe.HTTPGet.Path)

	// API pod must use the API ServiceAccount (IRSA binding).
	require.Equal(t, "todo-app-api", dep.Spec.Template.Spec.ServiceAccountName)
}

// TestServiceAccountsHaveIRSA asserts all three workload ServiceAccounts carry
// their own distinct eks.amazonaws.com/role-arn annotation (no shared role).
func TestServiceAccountsHaveIRSA(t *testing.T) {
	t.Parallel()
	out := helm.RenderTemplate(t, devOptions(), chartPath(t), "todo-app",
		[]string{"templates/service-account.yaml"})

	const annotation = "eks.amazonaws.com/role-arn"
	seenRoles := map[string]string{} // saName -> roleArn

	for _, doc := range splitYAML(out) {
		if !strings.Contains(doc, "kind: ServiceAccount") {
			continue
		}
		var sa corev1.ServiceAccount
		helm.UnmarshalK8SYaml(t, doc, &sa)
		role, ok := sa.Annotations[annotation]
		require.Truef(t, ok, "ServiceAccount %q is missing IRSA annotation %s",
			sa.Name, annotation)
		require.NotEmpty(t, role, "ServiceAccount %q has empty role-arn", sa.Name)
		seenRoles[sa.Name] = role
	}

	require.Contains(t, seenRoles, "todo-app-api")
	require.Contains(t, seenRoles, "todo-app-ai")
	require.Contains(t, seenRoles, "todo-app-db-init")

	// No shared role: the three role ARNs must be distinct.
	require.NotEqual(t, seenRoles["todo-app-api"], seenRoles["todo-app-ai"])
	require.NotEqual(t, seenRoles["todo-app-api"], seenRoles["todo-app-db-init"])
	require.NotEqual(t, seenRoles["todo-app-ai"], seenRoles["todo-app-db-init"])
}

// TestDBInitJobIsPreInstallHook asserts the Atlas migration Job is a Helm
// pre-install/pre-upgrade hook (separate from the Deployment).
func TestDBInitJobIsPreInstallHook(t *testing.T) {
	t.Parallel()
	out := helm.RenderTemplate(t, devOptions(), chartPath(t), "todo-app",
		[]string{"templates/job-db-init.yaml"})

	var job batchv1.Job
	helm.UnmarshalK8SYaml(t, out, &job)

	require.Equal(t, "Job", job.Kind)
	require.Equal(t, "todo-app-db-init", job.Name)

	hook, ok := job.Annotations["helm.sh/hook"]
	require.True(t, ok, "DB-init Job must carry a helm.sh/hook annotation")
	require.Contains(t, hook, "pre-install")
	require.Contains(t, hook, "pre-upgrade")

	require.Contains(t, job.Annotations, "helm.sh/hook-weight")
	require.Contains(t, job.Annotations, "helm.sh/hook-delete-policy")

	// Decoupled from the API: the Job uses the db-init SA, not the API SA.
	require.Equal(t, "todo-app-db-init", job.Spec.Template.Spec.ServiceAccountName)

	// It runs Atlas migrations.
	require.Len(t, job.Spec.Template.Spec.Containers, 1)
	c := job.Spec.Template.Spec.Containers[0]
	require.Equal(t, "atlas", c.Command[0])
	require.Contains(t, strings.Join(c.Args, " "), "migrate apply")
}

// TestDeploymentHasNoMigrationContainer guards the decoupling: the API
// Deployment must not embed an Atlas migration container/initContainer.
func TestDeploymentHasNoMigrationContainer(t *testing.T) {
	t.Parallel()
	out := helm.RenderTemplate(t, devOptions(), chartPath(t), "todo-app",
		[]string{"templates/deployment.yaml"})
	require.NotContains(t, out, "atlas",
		"the API Deployment must not run Atlas migrations; that belongs to the DB-init hook Job")
}

// splitYAML splits a multi-document YAML stream into individual documents.
func splitYAML(s string) []string {
	parts := strings.Split(s, "\n---")
	docs := make([]string, 0, len(parts))
	for _, p := range parts {
		if strings.TrimSpace(p) != "" {
			docs = append(docs, p)
		}
	}
	return docs
}
