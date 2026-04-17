"""Tests for LLM provider abstraction layer."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from orion.config.providers import (
    LLMProvider,
    get_llm,
    list_available_models,
    test_connection,
    _get_ollama_llm,
    _get_lmstudio_llm,
    _list_ollama_models,
    _list_lmstudio_models,
    _test_ollama_connection,
    _test_lmstudio_connection,
)


class MockSettings:
    """Mock Settings object for testing."""
    
    def __init__(self, data: dict):
        self._data = data
    
    def get(self, key: str, default=None):
        return self._data.get(key, default)


class TestProviderEnum:
    """Test LLMProvider enum."""
    
    def test_provider_values(self):
        assert LLMProvider.OLLAMA == "ollama"
        assert LLMProvider.LMSTUDIO == "lmstudio"


class TestGetLLM:
    """Test get_llm factory function."""
    
    @patch('orion.config.providers._get_ollama_llm')
    def test_get_ollama_llm(self, mock_ollama):
        """Test factory returns Ollama LLM when provider is ollama."""
        settings = MockSettings({"llm_provider": "ollama"})
        mock_ollama.return_value = Mock()
        
        result = get_llm(settings)
        
        mock_ollama.assert_called_once_with(settings)
        assert result is not None
    
    @patch('orion.config.providers._get_lmstudio_llm')
    def test_get_lmstudio_llm(self, mock_lmstudio):
        """Test factory returns LM Studio LLM when provider is lmstudio."""
        settings = MockSettings({"llm_provider": "lmstudio"})
        mock_lmstudio.return_value = Mock()
        
        result = get_llm(settings)
        
        mock_lmstudio.assert_called_once_with(settings)
        assert result is not None
    
    @patch('orion.config.providers._get_ollama_llm')
    def test_default_provider_is_ollama(self, mock_ollama):
        """Test factory defaults to Ollama when no provider specified."""
        settings = MockSettings({})
        mock_ollama.return_value = Mock()
        
        result = get_llm(settings)
        
        mock_ollama.assert_called_once_with(settings)
    
    def test_unsupported_provider_raises_error(self):
        """Test factory raises ValueError for unsupported provider."""
        settings = MockSettings({"llm_provider": "invalid"})
        
        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            get_llm(settings)


class TestOllamaLLM:
    """Test Ollama LLM instantiation."""
    
    @patch('orion.config.providers.ChatOllama')
    def test_get_ollama_llm_with_defaults(self, mock_chat_ollama):
        """Test Ollama LLM creation with default settings."""
        settings = MockSettings({})
        mock_chat_ollama.return_value = Mock()
        
        result = _get_ollama_llm(settings)
        
        mock_chat_ollama.assert_called_once_with(
            model="qwen2.5-coder:14b",
            temperature=0.7,
            num_ctx=8192,
        )
    
    @patch('orion.config.providers.ChatOllama')
    def test_get_ollama_llm_with_custom_settings(self, mock_chat_ollama):
        """Test Ollama LLM creation with custom settings."""
        settings = MockSettings({
            "model": "llama3.2:3b",
            "model_temperature": 0.5,
            "model_context_length": 4096,
        })
        mock_chat_ollama.return_value = Mock()
        
        result = _get_ollama_llm(settings)
        
        mock_chat_ollama.assert_called_once_with(
            model="llama3.2:3b",
            temperature=0.5,
            num_ctx=4096,
        )
    
    def test_get_ollama_llm_missing_dependency(self):
        """Test Ollama LLM raises ImportError when package not installed."""
        settings = MockSettings({})
        
        with patch.dict('sys.modules', {'langchain_ollama': None}):
            with pytest.raises(ImportError, match="langchain-ollama package not installed"):
                _get_ollama_llm(settings)


class TestLMStudioLLM:
    """Test LM Studio LLM instantiation."""
    
    @patch('orion.config.providers.ChatOpenAI')
    def test_get_lmstudio_llm_with_defaults(self, mock_chat_openai):
        """Test LM Studio LLM creation with default settings."""
        settings = MockSettings({})
        mock_chat_openai.return_value = Mock()
        
        result = _get_lmstudio_llm(settings)
        
        mock_chat_openai.assert_called_once_with(
            base_url="http://localhost:1234/v1",
            api_key="lm-studio",
            model="local-model",
            temperature=0.7,
            max_tokens=8192,
        )
    
    @patch('orion.config.providers.ChatOpenAI')
    def test_get_lmstudio_llm_with_custom_settings(self, mock_chat_openai):
        """Test LM Studio LLM creation with custom settings."""
        settings = MockSettings({
            "lmstudio_base_url": "http://192.168.1.100:5000/v1",
            "lmstudio_api_key": "custom-key",
            "model": "mistral-7b",
            "model_temperature": 0.9,
            "model_context_length": 16384,
        })
        mock_chat_openai.return_value = Mock()
        
        result = _get_lmstudio_llm(settings)
        
        mock_chat_openai.assert_called_once_with(
            base_url="http://192.168.1.100:5000/v1",
            api_key="custom-key",
            model="mistral-7b",
            temperature=0.9,
            max_tokens=16384,
        )
    
    def test_get_lmstudio_llm_missing_dependency(self):
        """Test LM Studio LLM raises ImportError when package not installed."""
        settings = MockSettings({})
        
        with patch.dict('sys.modules', {'langchain_openai': None}):
            with pytest.raises(ImportError, match="langchain-openai package not installed"):
                _get_lmstudio_llm(settings)


class TestListModels:
    """Test model listing functionality."""
    
    @patch('orion.config.providers._list_ollama_models')
    def test_list_ollama_models(self, mock_list):
        """Test listing Ollama models."""
        settings = MockSettings({"llm_provider": "ollama"})
        mock_list.return_value = ["model1", "model2"]
        
        result = list_available_models(settings)
        
        assert result == ["model1", "model2"]
        mock_list.assert_called_once()
    
    @patch('orion.config.providers._list_lmstudio_models')
    def test_list_lmstudio_models(self, mock_list):
        """Test listing LM Studio models."""
        settings = MockSettings({"llm_provider": "lmstudio"})
        mock_list.return_value = ["model3", "model4"]
        
        result = list_available_models(settings)
        
        assert result == ["model3", "model4"]
        mock_list.assert_called_once_with(settings)
    
    def test_list_models_unsupported_provider(self):
        """Test listing models returns empty list for unsupported provider."""
        settings = MockSettings({"llm_provider": "invalid"})
        
        result = list_available_models(settings)
        
        assert result == []
    
    @patch('orion.config.providers.ollama')
    def test_list_ollama_models_success(self, mock_ollama):
        """Test successful Ollama model listing."""
        mock_model1 = Mock()
        mock_model1.model = "llama3.2:3b"
        mock_model2 = Mock()
        mock_model2.model = "qwen2.5-coder:7b"
        
        mock_list_response = Mock()
        mock_list_response.models = [mock_model1, mock_model2]
        mock_ollama.list.return_value = mock_list_response
        
        result = _list_ollama_models()
        
        assert result == ["llama3.2:3b", "qwen2.5-coder:7b"]
    
    @patch('orion.config.providers.ollama')
    def test_list_ollama_models_error(self, mock_ollama):
        """Test Ollama model listing handles errors gracefully."""
        mock_ollama.list.side_effect = Exception("Connection error")
        
        result = _list_ollama_models()
        
        assert result == []
    
    @patch('orion.config.providers.httpx')
    def test_list_lmstudio_models_success(self, mock_httpx):
        """Test successful LM Studio model listing."""
        settings = MockSettings({
            "lmstudio_base_url": "http://localhost:1234/v1",
            "lmstudio_api_key": "lm-studio",
        })
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {"id": "mistral-7b"},
                {"id": "llama-2-13b"},
            ]
        }
        mock_httpx.get.return_value = mock_response
        
        result = _list_lmstudio_models(settings)
        
        assert result == ["mistral-7b", "llama-2-13b"]
        mock_httpx.get.assert_called_once()
    
    @patch('orion.config.providers.httpx')
    def test_list_lmstudio_models_error(self, mock_httpx):
        """Test LM Studio model listing handles errors gracefully."""
        settings = MockSettings({})
        mock_httpx.get.side_effect = Exception("Connection error")
        
        result = _list_lmstudio_models(settings)
        
        assert result == []


class TestConnectionTest:
    """Test connection testing functionality."""
    
    @patch('orion.config.providers._test_ollama_connection')
    def test_connection_ollama(self, mock_test):
        """Test connection test for Ollama."""
        settings = MockSettings({"llm_provider": "ollama"})
        mock_test.return_value = (True, "Connected")
        
        success, message = test_connection(settings)
        
        assert success is True
        assert message == "Connected"
        mock_test.assert_called_once()
    
    @patch('orion.config.providers._test_lmstudio_connection')
    def test_connection_lmstudio(self, mock_test):
        """Test connection test for LM Studio."""
        settings = MockSettings({"llm_provider": "lmstudio"})
        mock_test.return_value = (True, "Connected to LM Studio")
        
        success, message = test_connection(settings)
        
        assert success is True
        assert message == "Connected to LM Studio"
        mock_test.assert_called_once_with(settings)
    
    def test_connection_unknown_provider(self):
        """Test connection test for unknown provider."""
        settings = MockSettings({"llm_provider": "invalid"})
        
        success, message = test_connection(settings)
        
        assert success is False
        assert "Unknown provider" in message
    
    @patch('orion.config.providers.ollama')
    def test_ollama_connection_success(self, mock_ollama):
        """Test successful Ollama connection test."""
        mock_list_response = Mock()
        mock_list_response.models = [Mock(), Mock(), Mock()]
        mock_ollama.list.return_value = mock_list_response
        
        success, message = _test_ollama_connection()
        
        assert success is True
        assert "3 models available" in message
    
    @patch('orion.config.providers.ollama')
    def test_ollama_connection_failure(self, mock_ollama):
        """Test failed Ollama connection test."""
        mock_ollama.list.side_effect = Exception("Connection refused")
        
        success, message = _test_ollama_connection()
        
        assert success is False
        assert "Cannot connect to Ollama" in message
    
    @patch('orion.config.providers.httpx')
    def test_lmstudio_connection_success(self, mock_httpx):
        """Test successful LM Studio connection test."""
        settings = MockSettings({
            "lmstudio_base_url": "http://localhost:1234/v1",
            "lmstudio_api_key": "lm-studio",
        })
        
        mock_response = Mock()
        mock_response.json.return_value = {"data": [{"id": "model1"}, {"id": "model2"}]}
        mock_httpx.get.return_value = mock_response
        
        success, message = _test_lmstudio_connection(settings)
        
        assert success is True
        assert "2 models available" in message
    
    @patch('orion.config.providers.httpx')
    def test_lmstudio_connection_timeout(self, mock_httpx):
        """Test LM Studio connection timeout."""
        settings = MockSettings({})
        mock_httpx.get.side_effect = mock_httpx.TimeoutException("Timeout")
        
        success, message = _test_lmstudio_connection(settings)
        
        assert success is False
        assert "timeout" in message.lower()
    
    @patch('orion.config.providers.httpx')
    def test_lmstudio_connection_refused(self, mock_httpx):
        """Test LM Studio connection refused."""
        settings = MockSettings({"lmstudio_base_url": "http://localhost:1234/v1"})
        mock_httpx.get.side_effect = mock_httpx.ConnectError("Connection refused")
        
        success, message = _test_lmstudio_connection(settings)
        
        assert success is False
        assert "Cannot connect" in message
        assert "http://localhost:1234/v1" in message
