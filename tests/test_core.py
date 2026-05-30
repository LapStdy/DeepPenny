import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest

from api.deepseek_api import (
    validate_api_key,
    DeepSeekAPI,
    DeepSeekAPIError,
    AuthError,
    MAX_RETRIES,
)


class TestValidateApiKey:

    def test_valid_key(self):
        result = validate_api_key("sk-1234567890abcdef")
        assert result == "sk-1234567890abcdef"

    def test_valid_key_with_whitespace(self):
        result = validate_api_key("  sk-1234567890abcdef  ")
        assert result == "sk-1234567890abcdef"

    def test_empty_key(self):
        with pytest.raises(ValueError, match="API Key 不能为空"):
            validate_api_key("")

    def test_blank_key(self):
        with pytest.raises(ValueError, match="API Key 不能为空"):
            validate_api_key("   ")

    def test_invalid_prefix(self):
        with pytest.raises(ValueError, match="API Key 格式错误"):
            validate_api_key("ak-1234567890abcdef")

    def test_no_prefix(self):
        with pytest.raises(ValueError, match="API Key 格式错误"):
            validate_api_key("1234567890abcdef")


class TestDeepSeekAPIBalanceParsing:

    def _make_api(self, mock_response_data: dict, status_code: int = 200):
        api = DeepSeekAPI(api_key="sk-test")
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.is_success = status_code < 400
        mock_response.json.return_value = mock_response_data
        mock_client.get.return_value = mock_response
        api._client = mock_client
        return api

    def test_normal_balance(self):
        api = self._make_api({
            "is_available": True,
            "balance_infos": [
                {"total_balance": "12.50"}
            ]
        })
        result = api.get_balance()
        assert result["is_available"] is True
        assert result["balance"] == 12.50

    def test_balance_zero(self):
        api = self._make_api({
            "is_available": True,
            "balance_infos": [
                {"total_balance": "0.00"}
            ]
        })
        result = api.get_balance()
        assert result["balance"] == 0.0

    def test_empty_balance_infos(self):
        api = self._make_api({
            "is_available": False,
            "balance_infos": []
        })
        result = api.get_balance()
        assert result["balance"] == 0.0
        assert result["is_available"] is False

    def test_missing_balance_infos(self):
        api = self._make_api({"is_available": True})
        result = api.get_balance()
        assert result["balance"] == 0.0

    def test_balance_as_number(self):
        api = self._make_api({
            "is_available": True,
            "balance_infos": [
                {"total_balance": 25.30}
            ]
        })
        result = api.get_balance()
        assert result["balance"] == 25.30

    def test_invalid_json_response(self):
        api = self._make_api({})
        mock_response = MagicMock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.status_code = 200
        mock_response.is_success = True
        api._client.get.return_value = mock_response
        with pytest.raises(DeepSeekAPIError, match="JSON 解析失败"):
            api.get_balance()

    def test_401_auth_error(self):
        api = self._make_api({}, status_code=401)
        with pytest.raises(AuthError, match="API Key 无效"):
            api.get_balance()

    def test_403_auth_error(self):
        api = self._make_api({}, status_code=403)
        with pytest.raises(AuthError, match="API Key 无权限"):
            api.get_balance()

    def test_429_rate_limit(self):
        api = self._make_api({}, status_code=429)
        with pytest.raises(DeepSeekAPIError, match="请求过于频繁"):
            api.get_balance()

    def test_no_api_key(self):
        api = DeepSeekAPI(api_key="")
        with pytest.raises(DeepSeekAPIError, match="API Key 未设置"):
            api.get_balance()

    def test_network_error_retries_then_fails(self):
        api = DeepSeekAPI(api_key="sk-test")
        api._client = MagicMock()
        api._client.get.side_effect = httpx.NetworkError("connection refused")

        with pytest.raises(DeepSeekAPIError, match="网络错误"):
            api.get_balance()
        assert api._client.get.call_count == MAX_RETRIES

    def test_timeout_retries_then_fails(self):
        api = DeepSeekAPI(api_key="sk-test")
        api._client = MagicMock()
        api._client.get.side_effect = httpx.TimeoutException("timeout")

        with pytest.raises(DeepSeekAPIError, match="请求超时"):
            api.get_balance()
        assert api._client.get.call_count == MAX_RETRIES

    def test_auth_error_not_retried(self):
        api = DeepSeekAPI(api_key="sk-test")
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.is_success = False
        api._client = MagicMock()
        api._client.get.return_value = mock_response

        with pytest.raises(AuthError):
            api.get_balance()
        assert api._client.get.call_count == 1


class TestDeepSeekAPIManagement:

    def test_set_api_key_valid(self):
        api = DeepSeekAPI()
        api.set_api_key("sk-validkey")
        assert api.api_key == "sk-validkey"
        assert api._client is not None

    def test_set_api_key_empty(self):
        api = DeepSeekAPI(api_key="sk-old")
        api.set_api_key("")
        assert api.api_key == ""
        assert api._client is None

    def test_close(self):
        api = DeepSeekAPI(api_key="sk-test")
        assert api._client is not None
        api.close()
        assert api._client is None

    def test_init_with_key(self):
        api = DeepSeekAPI(api_key="sk-init")
        assert api.api_key == "sk-init"


class TestSecureStorage:

    @pytest.fixture
    def temp_config(self, monkeypatch):
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        )
        tmp.write(json.dumps({"refresh_interval": 60}))
        tmp.close()
        test_path = Path(tmp.name)

        import utils.secure_storage as ss
        monkeypatch.setattr(ss, "_CONFIG_PATH", test_path)
        yield test_path
        test_path.unlink(missing_ok=True)

    def test_save_and_load_from_config(self, temp_config, monkeypatch):
        import utils.secure_storage as ss
        monkeypatch.setattr(ss, "HAS_KEYRING", False)

        ss.save_api_key("sk-stored-key")
        loaded = ss.load_api_key()
        assert loaded == "sk-stored-key"

        with open(temp_config, "r", encoding="utf-8") as f:
            config = json.load(f)
        assert config.get("api_key") == "sk-stored-key"

    def test_delete_from_config(self, temp_config, monkeypatch):
        import utils.secure_storage as ss
        monkeypatch.setattr(ss, "HAS_KEYRING", False)

        ss.save_api_key("sk-to-delete")
        ss.delete_api_key()
        loaded = ss.load_api_key()
        assert loaded == ""

        with open(temp_config, "r", encoding="utf-8") as f:
            config = json.load(f)
        assert "api_key" not in config


class TestLogger:

    def test_logger_creation(self):
        import logging
        from utils.logger import setup_logger

        logger = setup_logger("test-logger")
        assert logger.name == "test-logger"
        assert logger.level == logging.DEBUG


