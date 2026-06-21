"""API authentication, authorization, and tenant resolution."""

from collections.abc import AsyncIterator, Callable
from uuid import UUID, uuid4

from fastapi import Depends, Header, HTTPException, Request, status

from todo_app.contexts.shared.application.request_context import (
    RequestContext,
    bind_context,
)
from todo_app.contexts.shared.domain.exceptions import AuthenticationError
from todo_app.core.config import Settings
from todo_app.core.di.container import ApplicationContainer


def get_container(request: Request) -> ApplicationContainer:
    return request.app.state.container


def get_settings_dep(request: Request) -> Settings:
    return request.app.state.settings


def _bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    return token if scheme.lower() == "bearer" and token else None


async def get_request_context(
    request: Request,
    authorization: str | None = Header(default=None),
    x_dev_tenant: str | None = Header(default=None),
    x_dev_roles: str | None = Header(default=None),
    container: ApplicationContainer = Depends(get_container),
    settings: Settings = Depends(get_settings_dep),
) -> AsyncIterator[RequestContext]:
    """Resolve the verified identity into a bound RequestContext for the request."""
    ctx: RequestContext | None = None

    token = _bearer_token(authorization)
    if token:
        authenticator = container.users.cognito_authenticator()
        try:
            claims = await authenticator.verify(token)
        except AuthenticationError as exc:
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {exc}"
            ) from exc
        ctx = RequestContext(tenant_id=claims.tenant_id, user_id=claims.subject, roles=claims.roles)
    elif settings.debug and x_dev_tenant:
        roles = frozenset(r.strip() for r in (x_dev_roles or "").split(",") if r.strip())
        ctx = RequestContext(
            tenant_id=UUID(x_dev_tenant), user_id=uuid4(), roles=roles or frozenset({"member"})
        )

    if ctx is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid credentials")

    with bind_context(ctx):
        yield ctx


def require_role(role: str) -> Callable[..., RequestContext]:
    """Authorization dependency factory — gates on a Cognito group/role claim."""

    def _checker(ctx: RequestContext = Depends(get_request_context)) -> RequestContext:
        if not ctx.has_role(role):
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail=f"Requires role: {role}")
        return ctx

    return _checker
