{{/*
Expand the name of the chart.
*/}}
{{- define "todo-app.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this
(by the DNS naming spec).
*/}}
{{- define "todo-app.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "todo-app.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "todo-app.labels" -}}
helm.sh/chart: {{ include "todo-app.chart" . }}
{{ include "todo-app.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: todo-app
{{- end }}

{{/*
Selector labels
*/}}
{{- define "todo-app.selectorLabels" -}}
app.kubernetes.io/name: {{ include "todo-app.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
API component selector labels (used by the Deployment + Service).
*/}}
{{- define "todo-app.api.selectorLabels" -}}
{{ include "todo-app.selectorLabels" . }}
app.kubernetes.io/component: api
{{- end }}

{{/*
ServiceAccount names: each workload (api, ai, db-init) has its own SA.
*/}}
{{- define "todo-app.serviceAccountName.api" -}}
{{- default (printf "%s-api" (include "todo-app.fullname" .)) .Values.serviceAccounts.api.name }}
{{- end }}

{{- define "todo-app.serviceAccountName.ai" -}}
{{- default (printf "%s-ai" (include "todo-app.fullname" .)) .Values.serviceAccounts.ai.name }}
{{- end }}

{{- define "todo-app.serviceAccountName.dbInit" -}}
{{- default (printf "%s-db-init" (include "todo-app.fullname" .)) .Values.serviceAccounts.dbInit.name }}
{{- end }}

{{/*
Resource names.
*/}}
{{- define "todo-app.configMapName" -}}
{{- printf "%s-config" (include "todo-app.fullname" .) }}
{{- end }}

{{- define "todo-app.secretName" -}}
{{- printf "%s-secret" (include "todo-app.fullname" .) }}
{{- end }}
