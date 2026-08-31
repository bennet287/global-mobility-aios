from unittest.mock import patch

import pytest

from app.core.secrets import SecretResolutionError
from app.services.llm_client import (
    DeepSeekProvider,
    LLMProviderConfigurationError,
)


def test_deepseek_provider_resolves_configured_secret_reference():
    with patch("app.services.llm_client.settings") as mock_settings:
        mock_settings.deepseek_api_key = "legacy-key"
        mock_settings.deepseek_api_key_ref = "env://DEEPSEEK_API_KEY"
        mock_settings.deepseek_model = "deepseek-chat"
        mock_settings.deepseek_base_url = "https://api.deepseek.com"
        with patch(
            "app.services.llm_client.resolve_runtime_secret",
            return_value="resolved-key",
        ) as resolver:
            provider = DeepSeekProvider()

    assert provider.api_key == "resolved-key"
    resolver.assert_called_once_with(
        reference="env://DEEPSEEK_API_KEY",
        fallback="legacy-key",
    )


def test_provider_secret_reference_failure_is_configuration_error():
    with patch("app.services.llm_client.settings") as mock_settings:
        mock_settings.deepseek_api_key = "legacy-key"
        mock_settings.deepseek_api_key_ref = "openbao://aios/nonprod/llm/deepseek#api_key"
        mock_settings.deepseek_model = "deepseek-chat"
        mock_settings.deepseek_base_url = "https://api.deepseek.com"
        with patch(
            "app.services.llm_client.resolve_runtime_secret",
            side_effect=SecretResolutionError("backend unavailable"),
        ):
            with pytest.raises(
                LLMProviderConfigurationError,
                match="secret reference could not be resolved",
            ):
                DeepSeekProvider()


def test_explicit_provider_key_bypasses_secret_resolution():
    with patch("app.services.llm_client.resolve_runtime_secret") as resolver:
        provider = DeepSeekProvider(api_key="explicit-key", model="deepseek-chat")

    assert provider.api_key == "explicit-key"
    resolver.assert_not_called()
