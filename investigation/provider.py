"""Minimal, injectable external-model boundary for investigation proposals."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Protocol, runtime_checkable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InvestigationProviderError(RuntimeError):
    """Raised when an external investigation provider cannot supply a proposal."""


@runtime_checkable
class InvestigationLLMClient(Protocol):
    """Return a parsed, structured proposal for a grounded investigation prompt."""

    def propose(self, prompt: str) -> dict[str, object]:
        """Request one structured proposal without executing any experiment."""


@dataclass(frozen=True)
class ProviderProposal:
    """Strictly parsed provider output, before canonical action construction."""

    stop: bool
    rationale: str
    challenge_type: str | None = None
    parameters: dict[str, object] | None = None


def parse_provider_proposal(payload: dict[str, object]) -> ProviderProposal:
    """Accept only the explicit action or stop JSON shapes used by ModelShield."""
    if not isinstance(payload, dict):
        raise InvestigationProviderError("provider response must be a JSON object")
    stop = payload.get("stop")
    rationale = payload.get("rationale")
    if not isinstance(stop, bool):
        raise InvestigationProviderError("provider response field 'stop' must be boolean")
    if not isinstance(rationale, str) or not rationale.strip():
        raise InvestigationProviderError("provider response field 'rationale' must be a non-empty string")
    if stop:
        return ProviderProposal(stop=True, rationale=rationale.strip())

    challenge_type = payload.get("challenge_type")
    parameters = payload.get("parameters")
    if not isinstance(challenge_type, str) or not challenge_type.strip():
        raise InvestigationProviderError("action response requires non-empty string 'challenge_type'")
    if not isinstance(parameters, dict):
        raise InvestigationProviderError("action response requires object 'parameters'")
    try:
        # Preserve JSON values exactly while rejecting non-JSON fake-client data.
        normalized = json.loads(json.dumps(parameters, sort_keys=True))
    except (TypeError, ValueError) as exc:
        raise InvestigationProviderError("action parameters must be JSON-serializable") from exc
    return ProviderProposal(False, rationale.strip(), challenge_type.strip(), normalized)


class OpenAICompatibleHTTPClient:
    """Small chat-completions client configured entirely through environment values."""

    def __init__(self, *, base_url: str, api_key: str, model: str, timeout: float = 10.0) -> None:
        if not isinstance(base_url, str) or not base_url.strip():
            raise InvestigationProviderError("MODELSHIELD_LLM_BASE_URL is required")
        if not isinstance(api_key, str) or not api_key.strip():
            raise InvestigationProviderError("MODELSHIELD_LLM_API_KEY is required")
        if not isinstance(model, str) or not model.strip():
            raise InvestigationProviderError("MODELSHIELD_LLM_MODEL is required")
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout <= 0:
            raise ValueError("timeout must be positive")
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = float(timeout)

    @classmethod
    def from_environment(cls, *, timeout: float = 10.0) -> "OpenAICompatibleHTTPClient":
        """Build a client from uncommitted environment configuration."""
        return cls(
            base_url=os.environ.get("MODELSHIELD_LLM_BASE_URL", ""),
            api_key=os.environ.get("MODELSHIELD_LLM_API_KEY", ""),
            model=os.environ.get("MODELSHIELD_LLM_MODEL", ""),
            timeout=timeout,
        )

    def propose(self, prompt: str) -> dict[str, object]:
        """Call a chat-completions endpoint and parse JSON-only assistant content."""
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be a non-empty string")
        body = json.dumps(
            {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
                "response_format": {"type": "json_object"},
            }
        ).encode("utf-8")
        request = Request(
            self._endpoint(),
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "ModelShield/1.0",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:  # nosec B310 - explicit configured endpoint
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = self._http_error_detail(exc)
            raise InvestigationProviderError(f"LLM request failed: HTTP {exc.code}: {exc.reason}{detail}") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise InvestigationProviderError(f"LLM request failed: {exc}") from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise InvestigationProviderError("LLM response was not valid JSON") from exc
        content = self._assistant_content(payload)
        try:
            proposal = json.loads(content)
        except json.JSONDecodeError as exc:
            raise InvestigationProviderError("LLM assistant content must be JSON only") from exc
        if not isinstance(proposal, dict):
            raise InvestigationProviderError("LLM assistant content must decode to a JSON object")
        return proposal

    def _endpoint(self) -> str:
        suffix = "/chat/completions"
        return self.base_url if self.base_url.endswith(suffix) else f"{self.base_url}{suffix}"

    def _http_error_detail(self, error: HTTPError) -> str:
        """Return a short provider body while never exposing configured credentials."""
        try:
            body = error.read().decode("utf-8", errors="replace")
        except OSError:
            return ""
        body = " ".join(body.split()).replace(self.api_key, "[REDACTED]")
        return f" - {body[:500]}" if body else ""

    @staticmethod
    def _assistant_content(payload: object) -> str:
        if not isinstance(payload, dict):
            raise InvestigationProviderError("LLM response payload must be an object")
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
            raise InvestigationProviderError("LLM response contains no assistant choice")
        message = choices[0].get("message")
        if not isinstance(message, dict):
            raise InvestigationProviderError("LLM response contains no assistant message")
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise InvestigationProviderError("LLM assistant content is empty")
        return content
