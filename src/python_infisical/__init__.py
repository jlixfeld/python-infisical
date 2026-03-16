"""Lightweight Python client for Infisical secrets manager.

Provides a clean interface for fetching secrets from an Infisical instance
using Machine Identity authentication (Universal Auth).

Usage::

    from python_infisical import InfisicalConfig, fetch_secrets

    config = InfisicalConfig.from_env()
    secrets = fetch_secrets(
        config,
        required=["GITHUB_TOKEN", "OPENROUTER_API_KEY"],
        optional=["DEEPGRAM_API_KEY"],
    )

    # Or inject directly into os.environ:
    from python_infisical import load_secrets_into_env
    load_secrets_into_env(config, required=[...], optional=[...])
"""

from python_infisical.client import (
    InfisicalConfig,
    InfisicalError,
    fetch_secrets,
    load_secrets_into_env,
)

__all__ = ["InfisicalConfig", "InfisicalError", "fetch_secrets", "load_secrets_into_env"]
