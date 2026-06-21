from uuid import uuid4

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwk, jwt

from todo_app.contexts.users.infrastructure.auth.cognito import (
    CognitoAuthenticator,
    InvalidTokenError,
)

REGION = "us-east-1"
POOL = "us-east-1_test"
CLIENT = "client123"
ISSUER = f"https://cognito-idp.{REGION}.amazonaws.com/{POOL}"


@pytest.fixture(scope="module")
def keypair():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    pub_pem = (
        key.public_key()
        .public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode()
    )
    jwk_dict = jwk.construct(pub_pem, "RS256").to_dict()
    jwk_dict.update({"kid": "test-kid", "use": "sig", "alg": "RS256"})
    return priv_pem, {"keys": [jwk_dict]}


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _FakeHttp:
    def __init__(self, jwks):
        self._jwks = jwks
        self.calls = 0

    async def get(self, url):
        self.calls += 1
        return _FakeResponse(self._jwks)


def _make_token(priv_pem, **overrides):
    claims = {
        "sub": str(uuid4()),
        "aud": CLIENT,
        "iss": ISSUER,
        "custom:tenant_id": str(uuid4()),
        "cognito:groups": ["Admin"],
        "email": "a@b.com",
    }
    claims.update(overrides)
    return jwt.encode(claims, priv_pem, algorithm="RS256", headers={"kid": "test-kid"})


def _authenticator(jwks):
    return CognitoAuthenticator(
        region=REGION,
        user_pool_id=POOL,
        app_client_id=CLIENT,
        http_client=_FakeHttp(jwks),
    )


pytestmark = pytest.mark.asyncio


async def test_verify_valid_token(keypair):
    priv, jwks = keypair
    tenant = str(uuid4())
    token = _make_token(priv, **{"custom:tenant_id": tenant})
    claims = await _authenticator(jwks).verify(token)
    assert str(claims.tenant_id) == tenant
    assert "admin" in claims.roles
    assert claims.email == "a@b.com"


async def test_jwks_is_cached(keypair):
    priv, jwks = keypair
    auth = _authenticator(jwks)
    await auth.verify(_make_token(priv))
    await auth.verify(_make_token(priv))
    assert auth._http.calls == 1


async def test_missing_tenant_claim_rejected(keypair):
    priv, jwks = keypair
    token = _make_token(priv, **{"custom:tenant_id": ""})
    with pytest.raises(InvalidTokenError):
        await _authenticator(jwks).verify(token)


async def test_wrong_audience_rejected(keypair):
    priv, jwks = keypair
    token = _make_token(priv, aud="someone-else")
    with pytest.raises(InvalidTokenError):
        await _authenticator(jwks).verify(token)


async def test_unknown_kid_rejected(keypair):
    priv, jwks = keypair
    token = jwt.encode(
        {"sub": str(uuid4()), "aud": CLIENT, "iss": ISSUER, "custom:tenant_id": str(uuid4())},
        priv,
        algorithm="RS256",
        headers={"kid": "other-kid"},
    )
    with pytest.raises(InvalidTokenError):
        await _authenticator(jwks).verify(token)


async def test_malformed_tenant_uuid_rejected(keypair):
    priv, jwks = keypair
    token = _make_token(priv, **{"custom:tenant_id": "not-a-uuid"})
    with pytest.raises(InvalidTokenError):
        await _authenticator(jwks).verify(token)
