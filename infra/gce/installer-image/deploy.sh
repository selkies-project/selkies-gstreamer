#!/bin/bash

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

set -e

export RED='\033[1;31m'
export CYAN='\033[1;36m'
export GREEN='\033[1;32m'
export NC='\033[0m' # No Color
function log_red() { echo -e "${RED}$@${NC}"; }
function log_cyan() { echo -e "${CYAN}$@${NC}"; }
function log_green() { echo -e "${GREEN}$@${NC}"; }

# Fetch any Secret Manager secrets named selkies-tfvars* and same them to .auto.tfvars files.
for secret in $(gcloud -q secrets list --filter=name~${TF_VAR_name}-tfvars- --format="value(name)"); do
    latest=$(gcloud secrets versions list ${secret} --sort-by=created --format='value(name)' --filter='STATE=enabled' --limit=1)
    [[ -z "${latest}" ]] && log_red "WARN: no enabled versions found for secret ${secret}" && continue
    dest="${secret/${TF_VAR_name}-tfvars-/}.auto.tfvars"
    log_cyan "Creating ${dest} from secret: ${secret}"
    gcloud -q secrets versions access ${latest} --secret ${secret} > ${dest}
done

# Fetch any Secret Manager secrets named ${TF_VAR_name}-${TF_VAR_region}-tfvars* and same them to .auto.tfvars files.
for secret in $(gcloud -q secrets list --filter=name~${TF_VAR_name}-${TF_VAR_region}-tfvars- --format="value(name)"); do
    latest=$(gcloud secrets versions list ${secret} --sort-by=created --format='value(name)' --filter='STATE=enabled' --limit=1)
    [[ -z "${latest}" ]] && log_red "WARN: no enabled versions found for secret ${secret}" && continue
    dest="${secret/${TF_VAR_name}-${TF_VAR_region}-tfvars-/}.auto.tfvars"
    log_cyan "Creating ${dest} from secret: ${secret}"
    gcloud -q secrets versions access ${latest} --secret ${secret} > ${dest}
done

# Fetch any Secret Manager secrets named ${TF_VAR_name}-${TF_VAR_region}-override-* and same them to *_override.tf files.
for secret in $(gcloud -q secrets list --filter=name~${TF_VAR_name}-${TF_VAR_region}-override- --format="value(name)"); do
    latest=$(gcloud secrets versions list ${secret} --sort-by=created --format='value(name)' --filter='STATE=enabled' --limit=1)
    [[ -z "${latest}" ]] && log_red "WARN: no enabled versions found for secret ${secret}" && continue
    dest="${secret/${TF_VAR_name}-${TF_VAR_region}-override-/}_override.tf"
    log_cyan "Creating ${dest} from secret: ${secret}"
    gcloud -q secrets versions access ${latest} --secret ${secret} > ${dest}
done

export TF_IN_AUTOMATION=1

# Set default project for google provider.
export GOOGLE_PROJECT=${TF_VAR_project_id?}

# Initialize backend and select workspace
terraform init -upgrade=true -input=false \
    -backend-config="bucket=${TF_VAR_project_id?}-${TF_VAR_name?}-tf-state" \
    -backend-config="prefix=${TF_VAR_name?}" || true
terraform workspace select ${TERRAFORM_WORKSPACE_NAME?} || terraform workspace new ${TERRAFORM_WORKSPACE_NAME?}
terraform init -input=false \
    -backend-config="bucket=${TF_VAR_project_id?}-${TF_VAR_name?}-tf-state" \
    -backend-config="prefix=${TF_VAR_name?}" || true

if [ "${ACTION?}" = "destroy" ]; then
    log_cyan "Running terraform destroy..."
    terraform destroy -auto-approve -input=false
elif [ "${ACTION?}" = "plan" ]; then
    log_cyan "Running terraform plan..."
    terraform plan -out terraform.tfplan -input=false
elif [ "${ACTION?}" = "apply" ]; then
    log_cyan "Running terraform plan..."
    terraform plan -out terraform.tfplan -input=false

    log_cyan "Running terraform apply..."
    terraform apply -input=false terraform.tfplan
fi

log_green "Done"