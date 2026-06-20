"""Cognito pre-token-generation Lambda.

Injects the user's tenant_id custom attribute and Cognito group memberships into
the JWT as custom claims so downstream services (API + RLS, AI context) can
enforce multi-tenant isolation and RBAC without an extra lookup.

Wired as the ``PreTokenGeneration`` trigger on the User Pool. The handler returns
the event with ``response.claimsOverrideDetails`` populated; Cognito merges those
into the issued ID/access token.
"""

import os


def handler(event, context):
    user_attributes = event.get("request", {}).get("userAttributes", {}) or {}
    groups = (
        event.get("request", {})
        .get("groupConfiguration", {})
        .get("groupsToOverride", [])
        or []
    )

    # tenant_id is stored as a Cognito custom attribute (custom:tenant_id).
    tenant_id = user_attributes.get("custom:tenant_id", "")

    # Primary role tier: derive from the highest-privilege group present.
    role = "member"
    if "admin" in groups:
        role = "admin"

    claims_to_add = {
        "tenant_id": tenant_id,
        "role": role,
        # Space-delimited group list keeps the claim compact and JWT-friendly.
        "groups": " ".join(groups),
    }

    # Allow operators to inject a fixed audience/issuer-scoped namespace if set.
    claim_prefix = os.environ.get("CLAIM_PREFIX", "")
    if claim_prefix:
        claims_to_add = {f"{claim_prefix}{k}": v for k, v in claims_to_add.items()}

    event["response"] = {
        "claimsOverrideDetails": {
            "claimsToAddOrOverride": claims_to_add,
            "groupOverrideDetails": {
                "groupsToOverride": groups,
            },
        }
    }

    return event
