import json
from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.services.llm_client import (
    DeepSeekProvider,
    LLMProviderError,
    LLMProviderFactory,
    MoonshotProvider,
    is_llm_enabled,
)


SAMPLE_CHAT_RESPONSE = {
    "id": "chatcmpl-test",
    "object": "chat.completion",
    "model": "deepseek-chat",
    "choices": [
        {
            "index": 0,
            "message": {"role": "assistant", "content": '{"summary": "test"}'},
            "finish_reason": "stop",
        }
    ],
    "usage": {
        "prompt_tokens": 100,
        "completion_tokens": 20,
        "total_tokens": 120,
    },
}


def test_llm_provider_factory_returns_deepseek():
    with patch("app.services.llm_client.settings") as mock_settings:
        mock_settings.llm_provider = "deepseek"
        mock_settings.deepseek_api_key = "ds-key"
        mock_settings.deepseek_model = "deepseek-chat"
        mock_settings.deepseek_base_url = "https://api.deepseek.com"
        mock_settings.llm_temperature = 0.2
        mock_settings.llm_timeout_seconds = 30

        provider = LLMProviderFactory.get_provider()
        assert isinstance(provider, DeepSeekProvider)


def test_llm_provider_factory_returns_moonshot():
    with patch("app.services.llm_client.settings") as mock_settings:
        mock_settings.llm_provider = "moonshot"
        mock_settings.moonshot_api_key = "mk-key"
        mock_settings.moonshot_model = "kimi-k1-5"
        mock_settings.moonshot_base_url = "https://api.moonshot.cn/v1"
        mock_settings.llm_temperature = 0.2
        mock_settings.llm_timeout_seconds = 30

        provider = LLMProviderFactory.get_provider()
        assert isinstance(provider, MoonshotProvider)


def test_llm_provider_factory_raises_when_unconfigured():
    with patch("app.services.llm_client.settings") as mock_settings:
        mock_settings.llm_provider = ""
        with pytest.raises(LLMProviderError, match="No LLM provider configured"):
            LLMProviderFactory.get_provider()


def test_llm_provider_factory_raises_for_unknown_provider():
    with patch("app.services.llm_client.settings") as mock_settings:
        mock_settings.llm_provider = "openai"
        with pytest.raises(LLMProviderError, match="Unknown LLM provider"):
            LLMProviderFactory.get_provider()


def _make_fake_client(response_data):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = json.dumps(response_data)
    mock_response.json.return_value = response_data
    mock_response.raise_for_status.return_value = None

    fake_client = MagicMock()
    fake_client.post.return_value = mock_response
    fake_client.__enter__ = MagicMock(return_value=fake_client)
    fake_client.__exit__ = MagicMock(return_value=False)
    return fake_client


def test_deepseek_provider_success():
    provider = DeepSeekProvider(api_key="ds-key", model="deepseek-chat")
    fake_client = _make_fake_client(SAMPLE_CHAT_RESPONSE)

    with patch("httpx.Client", return_value=fake_client):
        resp = provider.complete("You are a test assistant.", [{"role": "user", "content": "hi"}])

    assert resp.provider == "deepseek"
    assert resp.model == "deepseek-chat"
    assert resp.content == '{"summary": "test"}'
    assert resp.total_tokens == 120
    assert resp.estimated_cost_usd is not None


def test_deepseek_provider_missing_key():
    provider = DeepSeekProvider(api_key="", model="deepseek-chat")
    with pytest.raises(LLMProviderError, match="API key is not configured"):
        provider.complete("system", [{"role": "user", "content": "hi"}])


def test_deepseek_provider_http_error():
    provider = DeepSeekProvider(api_key="ds-key", model="deepseek-chat")

    fake_response = MagicMock()
    fake_response.status_code = 401
    fake_response.text = "Unauthorized"
    request = httpx.Request("POST", "https://api.deepseek.com/chat/completions")
    fake_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Unauthorized", request=request, response=fake_response
    )

    fake_client = MagicMock()
    fake_client.post.return_value = fake_response
    fake_client.__enter__ = MagicMock(return_value=fake_client)
    fake_client.__exit__ = MagicMock(return_value=False)

    with patch("httpx.Client", return_value=fake_client):
        with pytest.raises(LLMProviderError, match="API returned"):
            provider.complete("system", [{"role": "user", "content": "hi"}])


def test_is_llm_enabled():
    with patch("app.services.llm_client.settings") as mock_settings:
        mock_settings.llm_provider = "deepseek"
        assert is_llm_enabled() is True

        mock_settings.llm_provider = ""
        assert is_llm_enabled() is False

        mock_settings.llm_provider = "   "
        assert is_llm_enabled() is False
