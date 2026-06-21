"""AWS Cognito JWT verification — the single source of truth for authentication."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from uuid import UUID

import httpx
from jose import jwt
from jose.exceptions import JWTError

from todo_app.contexts.shared.domain.exceptions import AuthenticationError


class InvalidTokenError(AuthenticationError): ...


@dataclass(frozen=True, slots=True)
class CognitoClaims:
    subject: UUID
    tenant_id: UUID
    email: str | None
    roles: frozenset[str] = field(default_factory=frozenset)


class CognitoAuthenticator:
    def __init__(
        self,
        *,
        region: str,
        user_pool_id: str,
        app_client_id: str,
        jwks_ttl: int = 3600,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._region = region
        self._user_pool_id = user_pool_id
        self._app_client_id = app_client_id
        self._issuer = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"
        self._jwks_url = f"{self._issuer}/.well-known/jwks.json"
        self._jwks_ttl = jwks_ttl
        self._http = http_client
        self._jwks: dict | None = None
        self._jwks_fetched_at: float = 0.0

    async def _get_jwks(self) -> dict:
        now = time.monotonic()
        if self._jwks is not None and (now - self._jwks_fetched_at) < self._jwks_ttl:
            return self._jwks
        client = self._http or httpx.AsyncClient(timeout=5.0)
        try:
            response = await client.get(self._jwks_url)
            response.raise_for_status()
            jwks: dict = response.json()
        finally:
            if self._http is None:
                await client.aclose()
        self._jwks = jwks
        self._jwks_fetched_at = now
        return jwks

    async def verify(self, token: str) -> CognitoClaims:
        try:
            headers = jwt.get_unverified_header(token)
            jwks = await self._get_jwks()
            key = self._find_key(jwks, headers.get("kid"))
            claims = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                audience=self._app_client_id,
                issuer=self._issuer,
            )
        except (JWTError, KeyError, ValueError) as exc:
            raise InvalidTokenError(str(exc)) from exc

        return self._to_claims(claims)

    @staticmethod
    def _find_key(jwks: dict, kid: str | None) -> dict:
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                return key
        raise InvalidTokenError("Signing key not found in JWKS")

    @staticmethod
    def _to_claims(claims: dict) -> CognitoClaims:
        raw_tenant = claims.get("custom:tenant_id")
        if not raw_tenant:
            raise InvalidTokenError("Missing custom:tenant_id claim")
        groups = claims.get("cognito:groups") or []
        try:
            tenant_id = UUID(str(raw_tenant))
            subject = UUID(str(claims["sub"]))
        except (ValueError, KeyError) as exc:
            raise InvalidTokenError(f"Malformed identity claim: {exc}") from exc
        return CognitoClaims(
            subject=subject,
            tenant_id=tenant_id,
            email=claims.get("email"),
            roles=frozenset(str(g).lower() for g in groups),
        )
