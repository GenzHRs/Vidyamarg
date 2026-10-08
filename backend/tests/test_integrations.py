import pytest
from unittest.mock import patch, MagicMock
from app.services.ai_provider import AIProviderService, AIProviderUnavailableException
from app.core.config import settings

def test_gemini_missing_key_raises_unavailable(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    service = AIProviderService()
    assert not service.is_gemini_configured()
    with pytest.raises(AIProviderUnavailableException, match="not configured"):
        service.call_gemini("test prompt")

def test_gemini_mocked_success(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-dummy-gemini-key")
    service = AIProviderService()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "Synthetic Gemini Completion"}]}}]
    }

    with patch("requests.post", return_value=mock_resp) as mock_post:
        result = service.call_gemini("test prompt")
        assert result == "Synthetic Gemini Completion"
        assert mock_post.called

def test_nvidia_missing_key_raises_unavailable(monkeypatch):
    monkeypatch.setattr(settings, "NVIDIA_API_KEY", "")
    monkeypatch.setattr(settings, "NVIDIA_API_KEY_FALLBACK", "")
    service = AIProviderService()
    assert not service.is_nvidia_configured()
    with pytest.raises(AIProviderUnavailableException, match="not configured"):
        service.call_nvidia("test prompt")

def test_nvidia_mocked_success(monkeypatch):
    monkeypatch.setattr(settings, "NVIDIA_API_KEY", "test-dummy-nvidia-key")
    service = AIProviderService()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "Synthetic NVIDIA Completion"}}]
    }

    with patch("requests.post", return_value=mock_resp) as mock_post:
        result = service.call_nvidia("test prompt")
        assert result == "Synthetic NVIDIA Completion"
        assert mock_post.called

def test_groq_missing_key_raises_unavailable(monkeypatch):
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")
    service = AIProviderService()
    assert not service.is_groq_configured()
    with pytest.raises(AIProviderUnavailableException, match="not configured"):
        service.call_groq("test prompt")

def test_groq_mocked_success(monkeypatch):
    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-dummy-groq-key")
    service = AIProviderService()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "Synthetic Groq Completion"}}]
    }

    with patch("requests.post", return_value=mock_resp) as mock_post:
        result = service.call_groq("test prompt")
        assert result == "Synthetic Groq Completion"
        assert mock_post.called

def test_ai_fallback_chain_from_gemini_to_groq(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "dummy-gemini")
    monkeypatch.setattr(settings, "NVIDIA_API_KEY", "dummy-nvidia")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "dummy-groq")
    service = AIProviderService()

    # Gemini fails, NVIDIA fails, Groq succeeds
    def mock_post(url, **kwargs):
        resp = MagicMock()
        if "generativelanguage.googleapis.com" in url:
            resp.status_code = 500
        elif "integrate.api.nvidia.com" in url:
            resp.status_code = 503
        elif "api.groq.com" in url:
            resp.status_code = 200
            resp.json.return_value = {
                "choices": [{"message": {"content": "Groq Fallback Victory"}}]
            }
        return resp

    with patch("requests.post", side_effect=mock_post):
        result = service.call_with_fallback("test fallback prompt")
        assert result == "Groq Fallback Victory"

def test_all_providers_unconfigured_raises_unavailable(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    monkeypatch.setattr(settings, "NVIDIA_API_KEY", "")
    monkeypatch.setattr(settings, "NVIDIA_API_KEY_FALLBACK", "")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")

    service = AIProviderService()
    with pytest.raises(AIProviderUnavailableException, match="No active AI provider"):
        service.call_with_fallback("prompt")
