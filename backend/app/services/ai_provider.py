"""Unified External AI Providers Interface with explicit timeouts, retries, and fallback chaining."""
import logging
import os
import requests
from typing import Optional, List, Dict, Any, Union
from app.core.config import settings

logger = logging.getLogger("app.ai_provider")


class AIProviderUnavailableException(Exception):
    """Raised when an AI provider is unconfigured, unreachable, or times out."""
    pass


class AIProviderService:
    def __init__(self):
        self.default_timeout = 25
        self.max_retries = 2

    def is_gemini_configured(self) -> bool:
        key = getattr(settings, "GEMINI_API_KEY", "")
        return bool(key and str(key).strip().lower() not in {"", "none", "null"})

    def is_nvidia_configured(self) -> bool:
        key = getattr(settings, "NVIDIA_API_KEY", "") or getattr(settings, "NVIDIA_API_KEY_FALLBACK", "")
        return bool(key and str(key).strip().lower() not in {"", "none", "null"})

    def is_groq_configured(self) -> bool:
        key = getattr(settings, "GROQ_API_KEY", "")
        return bool(key and str(key).strip().lower() not in {"", "none", "null"})

    def call_gemini(
        self,
        prompt: str,
        json_mode: bool = False,
        pdf_bytes: Optional[bytes] = None,
        model: str = "gemini-2.5-flash",
        timeout: Optional[int] = None
    ) -> str:
        if not self.is_gemini_configured():
            raise AIProviderUnavailableException("Gemini provider is not configured")

        import base64
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={settings.GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}

        parts = []
        if pdf_bytes:
            encoded_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
            parts.append({"inlineData": {"mimeType": "application/pdf", "data": encoded_pdf}})
        parts.append({"text": prompt})

        payload: Dict[str, Any] = {"contents": [{"parts": parts}]}
        if json_mode:
            payload["generationConfig"] = {"responseMimeType": "application/json", "maxOutputTokens": 8192}

        timeout_val = timeout or self.default_timeout
        for attempt in range(self.max_retries):
            try:
                res = requests.post(url, headers=headers, json=payload, timeout=timeout_val)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts_out = candidates[0]["content"].get("parts", [])
                        if parts_out and "text" in parts_out[0]:
                            return parts_out[0]["text"]
                logger.warning(f"Gemini API returned status {res.status_code} (attempt {attempt + 1})")
            except requests.exceptions.RequestException as e:
                logger.warning(f"Gemini request exception on attempt {attempt + 1}: {type(e).__name__}")

        raise AIProviderUnavailableException(f"Gemini API failed after {self.max_retries} attempts")

    def call_nvidia(
        self,
        messages: Union[str, List[Dict[str, str]]],
        json_mode: bool = False,
        model: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> str:
        if not self.is_nvidia_configured():
            raise AIProviderUnavailableException("NVIDIA provider is not configured")

        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]

        keys_to_try = [k for k in [settings.NVIDIA_API_KEY, settings.NVIDIA_API_KEY_FALLBACK] if k]
        chosen_model = model or getattr(settings, "NVIDIA_MODEL", "meta/llama-3.3-70b-instruct")

        timeout_val = timeout or self.default_timeout
        for key in keys_to_try:
            url = "https://integrate.api.nvidia.com/v1/chat/completions"
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
            payload = {
                "model": chosen_model,
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 4096
            }
            try:
                res = requests.post(url, headers=headers, json=payload, timeout=timeout_val)
                if res.status_code == 200:
                    data = res.json()
                    choices = data.get("choices", [])
                    if choices and "message" in choices[0]:
                        return choices[0]["message"].get("content", "")
                logger.warning(f"NVIDIA API returned status {res.status_code}")
            except requests.exceptions.RequestException as e:
                logger.warning(f"NVIDIA request exception: {type(e).__name__}")

        raise AIProviderUnavailableException("NVIDIA API failed across all configured keys")

    def call_groq(
        self,
        messages: Union[str, List[Dict[str, str]]],
        json_mode: bool = False,
        model: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> str:
        if not self.is_groq_configured():
            raise AIProviderUnavailableException("Groq provider is not configured")

        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]

        chosen_model = model or getattr(settings, "GROQ_MODEL", "llama-3.3-70b-versatile")
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {settings.GROQ_API_KEY}"}
        payload: Dict[str, Any] = {
            "model": chosen_model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 4096
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        timeout_val = timeout or self.default_timeout
        for attempt in range(self.max_retries):
            try:
                res = requests.post(url, headers=headers, json=payload, timeout=timeout_val)
                if res.status_code == 200:
                    data = res.json()
                    choices = data.get("choices", [])
                    if choices and "message" in choices[0]:
                        return choices[0]["message"].get("content", "")
                logger.warning(f"Groq API returned status {res.status_code} (attempt {attempt + 1})")
            except requests.exceptions.RequestException as e:
                logger.warning(f"Groq request exception: {type(e).__name__}")

        raise AIProviderUnavailableException(f"Groq API failed after {self.max_retries} attempts")

    def call_with_fallback(
        self,
        prompt_or_messages: Union[str, List[Dict[str, str]]],
        json_mode: bool = False,
        pdf_bytes: Optional[bytes] = None
    ) -> str:
        """
        Attempts configured providers in priority order: Gemini -> NVIDIA -> Groq.
        Returns the first successful response, or raises AIProviderUnavailableException.
        """
        prompt_str = prompt_or_messages if isinstance(prompt_or_messages, str) else "\n".join([m.get("content", "") for m in prompt_or_messages])

        # 1. Try Gemini
        if self.is_gemini_configured():
            try:
                return self.call_gemini(prompt_str, json_mode=json_mode, pdf_bytes=pdf_bytes)
            except AIProviderUnavailableException as e:
                logger.warning(f"Falling back from Gemini: {e}")

        # 2. Try NVIDIA
        if self.is_nvidia_configured():
            try:
                return self.call_nvidia(prompt_or_messages, json_mode=json_mode)
            except AIProviderUnavailableException as e:
                logger.warning(f"Falling back from NVIDIA: {e}")

        # 3. Try Groq
        if self.is_groq_configured():
            try:
                return self.call_groq(prompt_or_messages, json_mode=json_mode)
            except AIProviderUnavailableException as e:
                logger.warning(f"Falling back from Groq: {e}")

        raise AIProviderUnavailableException("No active AI provider could satisfy the request")


ai_provider_service = AIProviderService()
