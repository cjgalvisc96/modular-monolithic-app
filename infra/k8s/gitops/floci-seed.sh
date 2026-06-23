#!/usr/bin/env bash
# Seed this app's floci (local AWS) state: the SSM parameters its ExternalSecret
# reads and the ECR repository its image is pushed to. The app OWNS this — the
# local-gitops platform stays app-agnostic and just runs each registered app's
# floci-seed.sh during bootstrap.
#
# Idempotent (every put is --overwrite). Endpoint + profile are overridable so
# it works against either floci instance:
#   - local-gitops floci : AWS_ENDPOINT_URL=http://localhost:4566 (default)
#   - docker-compose floci: AWS_ENDPOINT_URL=http://localhost:4576
#
# Keys mirror infra/k8s/helm/values.yaml externalSecrets.keys, under the
# parameterPrefix /gitops/<env>/todo-app. REDIS_PASSWORD matches the password
# the in-namespace Redis (infra/k8s/dependencies/base/redis.yaml) requires.
set -euo pipefail

ENDPOINT="${AWS_ENDPOINT_URL:-http://localhost:4566}"
export AWS_PROFILE="${AWS_PROFILE:-floci}"
export AWS_REGION="${AWS_REGION:-us-east-1}"
ECR_REPO="gitops/todo-app"

if ! command -v aws >/dev/null 2>&1; then
  echo "aws CLI not found; cannot seed floci" >&2
  exit 1
fi

put() { aws --endpoint-url "$ENDPOINT" ssm put-parameter --overwrite "$@" >/dev/null; }

for env in dev prod; do
  pfx="/gitops/${env}/todo-app"
  put --name "${pfx}/DB_USER"        --type String       --value "todo"
  put --name "${pfx}/DB_PASSWORD"    --type SecureString  --value "todo"
  put --name "${pfx}/REDIS_PASSWORD" --type SecureString  --value "redispass"
  echo "ssm: ${pfx}/{DB_USER,DB_PASSWORD,REDIS_PASSWORD}"
done

aws --endpoint-url "$ENDPOINT" ecr create-repository --repository-name "$ECR_REPO" \
  >/dev/null 2>&1 && echo "ecr: ${ECR_REPO}" || echo "ecr: ${ECR_REPO} (exists)"
