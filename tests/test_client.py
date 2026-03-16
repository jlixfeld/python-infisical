"""Unit tests for the python-infisical client."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from python_infisical.client import (
    InfisicalConfig,
    InfisicalError,
    fetch_secrets,
    load_secrets_into_env,
)


class TestInfisicalConfig:
    def test_from_env_returns_none_when_not_configured(self):
        with patch.dict(os.environ, {}, clear=True):
            assert InfisicalConfig.from_env() is None

    def test_from_env_returns_none_when_partial(self):
        with patch.dict(os.environ, {"INFISICAL_CLIENT_ID": "id"}, clear=True):
            assert InfisicalConfig.from_env() is None

    def test_from_env_returns_config_when_fully_set(self):
        env = {
            "INFISICAL_CLIENT_ID": "cid",
            "INFISICAL_CLIENT_SECRET": "csec",
            "INFISICAL_HOST": "https://infisical.example.com",
            "INFISICAL_PROJECT_ID": "proj",
            "INFISICAL_ENVIRONMENT": "staging",
        }
        with patch.dict(os.environ, env, clear=True):
            config = InfisicalConfig.from_env()
            assert config is not None
            assert config.client_id == "cid"
            assert config.client_secret == "csec"
            assert config.host == "https://infisical.example.com"
            assert config.project_id == "proj"
            assert config.environment == "staging"

    def test_from_env_uses_defaults(self):
        env = {
            "INFISICAL_CLIENT_ID": "cid",
            "INFISICAL_CLIENT_SECRET": "csec",
        }
        with patch.dict(os.environ, env, clear=True):
            config = InfisicalConfig.from_env()
            assert config is not None
            assert config.host == "http://localhost:8080"
            assert config.environment == "prod"

    def test_is_configured_true(self):
        config = InfisicalConfig(
            host="http://localhost",
            client_id="cid",
            client_secret="csec",
            project_id="proj",
        )
        assert config.is_configured() is True

    def test_is_configured_false_missing_project(self):
        config = InfisicalConfig(
            host="http://localhost",
            client_id="cid",
            client_secret="csec",
            project_id="",
        )
        assert config.is_configured() is False


class TestFetchSecrets:
    def test_raises_when_sdk_not_installed(self):
        config = InfisicalConfig(
            host="http://localhost",
            client_id="cid",
            client_secret="csec",
            project_id="proj",
        )
        with (
            patch.dict("sys.modules", {"infisical_sdk": None}),
            pytest.raises(InfisicalError, match="infisicalsdk"),
        ):
            fetch_secrets(config, required=["FOO"])

    def test_fetches_required_and_optional(self):
        mock_sdk_class = MagicMock()
        mock_client = MagicMock()
        mock_sdk_class.return_value = mock_client

        def make_secret(value):
            s = MagicMock()
            s.secretValue = value
            return s

        mock_client.secrets.get_secret_by_name.side_effect = [
            make_secret("token_value"),
            make_secret("optional_value"),
        ]

        mock_module = MagicMock()
        mock_module.InfisicalSDKClient = mock_sdk_class

        config = InfisicalConfig(
            host="http://localhost",
            client_id="cid",
            client_secret="csec",
            project_id="proj",
        )

        with patch.dict("sys.modules", {"infisical_sdk": mock_module}):
            result = fetch_secrets(config, required=["TOKEN"], optional=["OPT"])

        assert result == {"TOKEN": "token_value", "OPT": "optional_value"}

    def test_raises_on_missing_required(self):
        mock_sdk_class = MagicMock()
        mock_client = MagicMock()
        mock_sdk_class.return_value = mock_client
        mock_client.secrets.get_secret_by_name.side_effect = Exception("not found")

        mock_module = MagicMock()
        mock_module.InfisicalSDKClient = mock_sdk_class

        config = InfisicalConfig(
            host="http://localhost",
            client_id="cid",
            client_secret="csec",
            project_id="proj",
        )

        with (
            patch.dict("sys.modules", {"infisical_sdk": mock_module}),
            pytest.raises(InfisicalError, match="REQUIRED_SECRET"),
        ):
            fetch_secrets(config, required=["REQUIRED_SECRET"])

    def test_optional_missing_does_not_raise(self):
        mock_sdk_class = MagicMock()
        mock_client = MagicMock()
        mock_sdk_class.return_value = mock_client
        mock_client.secrets.get_secret_by_name.side_effect = Exception("not found")

        mock_module = MagicMock()
        mock_module.InfisicalSDKClient = mock_sdk_class

        config = InfisicalConfig(
            host="http://localhost",
            client_id="cid",
            client_secret="csec",
            project_id="proj",
        )

        with patch.dict("sys.modules", {"infisical_sdk": mock_module}):
            result = fetch_secrets(config, optional=["OPT_SECRET"])
            assert result == {}


class TestLoadSecretsIntoEnv:
    def test_injects_into_environ(self):
        mock_sdk_class = MagicMock()
        mock_client = MagicMock()
        mock_sdk_class.return_value = mock_client

        secret = MagicMock()
        secret.secretValue = "my_token"
        mock_client.secrets.get_secret_by_name.return_value = secret

        mock_module = MagicMock()
        mock_module.InfisicalSDKClient = mock_sdk_class

        config = InfisicalConfig(
            host="http://localhost",
            client_id="cid",
            client_secret="csec",
            project_id="proj",
        )

        with (
            patch.dict("sys.modules", {"infisical_sdk": mock_module}),
            patch.dict(os.environ, {}, clear=False),
        ):
            load_secrets_into_env(config, required=["MY_SECRET"])
            assert os.environ["MY_SECRET"] == "my_token"
