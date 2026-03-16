"""Infisical secrets client.

Provides a clean interface for fetching secrets from an Infisical instance
using Machine Identity authentication (Universal Auth).

Dependencies: ``infisicalsdk`` (pip install infisicalsdk).
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

log = logging.getLogger("python_infisical")


class InfisicalError(Exception):
    """Raised when required secrets cannot be fetched."""


@dataclass(frozen=True)
class InfisicalConfig:
    """Configuration for connecting to an Infisical instance.

    All fields can be populated from environment variables via ``from_env()``.
    """

    host: str
    client_id: str
    client_secret: str
    project_id: str
    environment: str = "prod"
    secret_path: str = "/"

    @classmethod
    def from_env(cls) -> InfisicalConfig | None:
        """Build config from environment variables.

        Returns ``None`` if the required credentials are not set, allowing
        callers to skip Infisical gracefully when running without it.

        Required env vars:
          - INFISICAL_CLIENT_ID
          - INFISICAL_CLIENT_SECRET

        Also reads:
          - INFISICAL_HOST (default: http://localhost:8080)
          - INFISICAL_PROJECT_ID
          - INFISICAL_ENVIRONMENT (default: prod)
        """
        client_id = os.environ.get("INFISICAL_CLIENT_ID", "")
        client_secret = os.environ.get("INFISICAL_CLIENT_SECRET", "")

        if not client_id or not client_secret:
            return None

        return cls(
            host=os.environ.get("INFISICAL_HOST", "http://localhost:8080"),
            client_id=client_id,
            client_secret=client_secret,
            project_id=os.environ.get("INFISICAL_PROJECT_ID", ""),
            environment=os.environ.get("INFISICAL_ENVIRONMENT", "prod"),
        )

    def is_configured(self) -> bool:
        """Return True if all required fields are present."""
        return bool(self.host and self.client_id and self.client_secret and self.project_id)


def fetch_secrets(
    config: InfisicalConfig,
    required: list[str] | None = None,
    optional: list[str] | None = None,
) -> dict[str, str]:
    """Fetch secrets from Infisical and return them as a dict.

    Parameters
    ----------
    config:
        Connection configuration for the Infisical instance.
    required:
        Secret names that must be present.  Raises ``InfisicalError`` if any
        are missing or empty.
    optional:
        Secret names that are fetched but do not cause failure if absent.

    Returns
    -------
    dict[str, str]
        Mapping of secret name to secret value for all successfully fetched
        secrets (both required and optional).
    """
    try:
        from infisical_sdk import InfisicalSDKClient
    except ImportError as exc:
        raise InfisicalError(
            "infisicalsdk package not installed. Install it with: pip install infisicalsdk"
        ) from exc

    required = required or []
    optional = optional or []

    client = InfisicalSDKClient(host=config.host)
    client.auth.universal_auth.login(
        client_id=config.client_id,
        client_secret=config.client_secret,
    )

    secrets: dict[str, str] = {}
    missing_required: list[str] = []
    missing_optional: list[str] = []

    for name in required + optional:
        try:
            secret = client.secrets.get_secret_by_name(
                secret_name=name,
                project_id=config.project_id,
                environment_slug=config.environment,
                secret_path=config.secret_path,
            )
        except Exception as exc:
            if name in required:
                missing_required.append(name)
            else:
                missing_optional.append(name)
                log.warning("Infisical lookup failed for optional secret %s: %s", name, exc)
            continue

        if not secret or not secret.secretValue:
            if name in required:
                missing_required.append(name)
            else:
                missing_optional.append(name)
        else:
            secrets[name] = secret.secretValue

    if missing_optional:
        log.warning(
            "Optional secrets not found in Infisical (features disabled): %s",
            ", ".join(missing_optional),
        )

    if missing_required:
        raise InfisicalError(
            f"Required secrets missing from Infisical: {', '.join(missing_required)}"
        )

    return secrets


def load_secrets_into_env(
    config: InfisicalConfig,
    required: list[str] | None = None,
    optional: list[str] | None = None,
) -> dict[str, str]:
    """Fetch secrets from Infisical and inject them into ``os.environ``.

    This is the primary entry point for application startup -- it replaces
    the shell-based secret fetching previously done in ``entrypoint.sh``.

    Parameters
    ----------
    config:
        Connection configuration for the Infisical instance.
    required:
        Secret names that must be present.  Raises ``InfisicalError`` if any
        are missing or empty.
    optional:
        Secret names that are fetched but do not cause failure if absent.

    Returns
    -------
    dict[str, str]
        The fetched secrets (same as ``fetch_secrets``).
    """
    secrets = fetch_secrets(config, required=required, optional=optional)

    for name, value in secrets.items():
        os.environ[name] = value

    log.info("Loaded %d secrets from Infisical into environment", len(secrets))
    return secrets
