from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import httpx

from app.core.config import settings


@dataclass
class LLMResponse:
    content: str
    provider: str
    model: str
    finish_reason: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    raw_response: dict[str, Any] = field(default_factory=dict, repr=False)

    @property
    def estimated_cost_usd(self) -> float | None:
        """Return a rough cost estimate based on known per-token pricing."""
        if self.total_tokens is None:
            return None
        # Gemini may execute on free or paid tiers and this response does not carry
        # billing-tier identity. Do not fabricate a paid/free cost estimate.
        if self.provider == "gemini":
            return None
        rates = {
            # DeepSeek pricing (per 1M tokens, approximate)
            ("deepseek", "deepseek-chat"): 0.00027,
            ("deepseek", "deepseek-reasoner"): 0.00110,
            # Moonshot pricing (per 1M tokens, approximate)
            ("moonshot", "kimi-k1-5"): 0.00600,
            ("moonshot", "kimi-k1"): 0.01200,
            ("moonshot", "moonshot-v1-8k"): 0.00600,
            ("moonshot", "moonshot-v1-32k"): 0.01200,
            ("moonshot", "moonshot-v1-128k"): 0.02400,
        }
        rate = rates.get((self.provider, self.model))
        if rate is None:
            # Fallback averages
            rate = 0.00100 if self.provider == "deepseek" else 0.01000
        return round(self.total_tokens * rate / 1_000_000, 6)


class LLMProviderError(Exception):
    pass


class LLMProviderConfigurationError(LLMProviderError):
    """Provider execution cannot start because local/provider configuration is invalid."""


class LLMProviderTransportError(LLMProviderError):
    """Provider request reached the external execution boundary but transport/service failed."""


class LLMProviderResponseContractError(LLMProviderError):
    """Provider returned a response that cannot satisfy the adapter response contract."""


class LLMProvider(ABC):
    name: str

    @abstractmethod
    def complete(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        response_format: dict[str, Any] | None = None,
    ) -> LLMResponse:
        raise NotImplementedError


class _OpenAICompatibleProvider(LLMProvider):
    """Base for hosted providers exposing OpenAI-compatible chat-completion endpoints."""

    name: str
    base_url: str
    api_key: str
    default_model: str

    def __init__(self, api_key: str, default_model: str, base_url: str | None = None):
        self.api_key = api_key
        self.default_model = default_model
        self.base_url = (base_url or self.base_url).rstrip("/")

    def complete(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        response_format: dict[str, Any] | None = None,
    ) -> LLMResponse:
        if not self.api_key:
            raise LLMProviderConfigurationError(
                f"{self.name} API key is not configured."
            )

        payload_messages = [{"role": "system", "content": system_prompt}]
        payload_messages.extend(messages)

        payload: dict[str, Any] = {
            "model": self.default_model,
            "messages": payload_messages,
            "temperature": settings.llm_temperature,
        }
        if response_format:
            payload["response_format"] = response_format

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=settings.llm_timeout_seconds) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise LLMProviderTransportError(
                f"{self.name} API returned {exc.response.status_code}: {exc.response.text}"
            ) from exc
        except httpx.RequestError as exc:
            raise LLMProviderTransportError(
                f"{self.name} API request failed: {exc}"
            ) from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise LLMProviderResponseContractError(
                f"Unexpected {self.name} response body: invalid JSON"
            ) from exc

        try:
            choice = data["choices"][0]
            message = choice["message"]
            content = message.get("content", "")
            finish_reason = choice.get("finish_reason")
            model = data.get("model", self.default_model)
            usage = data.get("usage", {})
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMProviderResponseContractError(
                f"Unexpected {self.name} response structure: {json.dumps(data, default=str)[:500]}"
            ) from exc

        return LLMResponse(
            content=content,
            provider=self.name,
            model=model,
            finish_reason=finish_reason,
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            total_tokens=usage.get("total_tokens"),
            raw_response=data,
        )


class DeepSeekProvider(_OpenAICompatibleProvider):
    name = "deepseek"
    base_url = "https://api.deepseek.com"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ):
        super().__init__(
            api_key=settings.deepseek_api_key if api_key is None else api_key,
            default_model=settings.deepseek_model if model is None else model,
            base_url=settings.deepseek_base_url if base_url is None else base_url,
        )


class MoonshotProvider(_OpenAICompatibleProvider):
    name = "moonshot"
    base_url = "https://api.moonshot.cn/v1"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ):
        super().__init__(
            api_key=settings.moonshot_api_key if api_key is None else api_key,
            default_model=settings.moonshot_model if model is None else model,
            base_url=settings.moonshot_base_url if base_url is None else base_url,
        )


class GeminiProvider(_OpenAICompatibleProvider):
    """Google Gemini through the documented OpenAI-compatible chat endpoint."""

    name = "gemini"
    base_url = "https://generativelanguage.googleapis.com/v1beta/openai"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ):
        super().__init__(
            api_key=settings.gemini_api_key if api_key is None else api_key,
            default_model=settings.gemini_model if model is None else model,
            base_url=settings.gemini_base_url if base_url is None else base_url,
        )

    def complete(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        response_format: dict[str, Any] | None = None,
    ) -> LLMResponse:
        # Controlled agents require machine-readable JSON. The existing controlled-agent
        # caller only requests json_object explicitly for the historical providers, so
        # Gemini enforces the same contract at its adapter boundary rather than relying
        # on prompt-only JSON compliance.
        return super().complete(
            system_prompt=system_prompt,
            messages=messages,
            response_format=response_format or {"type": "json_object"},
        )


class LLMProviderFactory:
    _providers: dict[str, type[LLMProvider]] = {
        "deepseek": DeepSeekProvider,
        "gemini": GeminiProvider,
        "moonshot": MoonshotProvider,
    }

    @classmethod
    def get_provider(cls, name: str | None = None) -> LLMProvider:
        name = (name or settings.llm_provider or "").lower().strip()
        if not name:
            raise LLMProviderConfigurationError("No LLM provider configured.")
        provider_cls = cls._providers.get(name)
        if provider_cls is None:
            raise LLMProviderConfigurationError(
                f"Unknown LLM provider: {name}. Available: {list(cls._providers)}"
            )
        return provider_cls()

    @classmethod
    def available_providers(cls) -> list[str]:
        return sorted(cls._providers.keys())

    @classmethod
    def active_provider_name(cls) -> str | None:
        name = settings.llm_provider or ""
        name = name.lower().strip()
        return name if name in cls._providers else None


def is_llm_enabled() -> bool:
    return bool(settings.llm_provider and settings.llm_provider.strip())
