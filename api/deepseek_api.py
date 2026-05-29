import logging
import time

import httpx

logger = logging.getLogger("DeepPenny.api")

BASE_URL = "https://api.deepseek.com"
TIMEOUT = 15.0
API_KEY_PREFIX = "sk-"
MAX_RETRIES = 3
RETRY_BACKOFF = [1, 2, 4]


def validate_api_key(api_key: str) -> str:
    stripped = api_key.strip()
    if not stripped:
        raise ValueError("API Key 不能为空")
    if not stripped.startswith(API_KEY_PREFIX):
        raise ValueError("API Key 格式错误，应以 sk- 开头")
    return stripped


class DeepSeekAPIError(Exception):
    pass


class AuthError(DeepSeekAPIError):
    pass


class DeepSeekAPI:

    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self._client = None

    def set_api_key(self, api_key: str):
        validated = validate_api_key(api_key) if api_key else ""
        self.api_key = validated
        self._build_client()

    def _build_client(self):
        if self._client:
            self._client.close()
        if not self.api_key:
            self._client = None
            return
        self._client = httpx.Client(
            timeout=TIMEOUT,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )

    def close(self):
        if self._client:
            self._client.close()
            self._client = None

    def get_balance(self) -> dict:
        if not self.api_key:
            raise DeepSeekAPIError("API Key 未设置")

        if self._client is None:
            self._build_client()

        last_error = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return self._do_request()
            except (DeepSeekAPIError, httpx.HTTPError) as e:
                if isinstance(e, AuthError):
                    raise
                if attempt == MAX_RETRIES:
                    raise
                last_error = e
                wait = RETRY_BACKOFF[attempt - 1]
                logger.warning(
                    "请求失败 (第%d次)，%.1f秒后重试: %s",
                    attempt, wait, e,
                )
                time.sleep(wait)

        raise last_error

    def _do_request(self) -> dict:
        try:
            response = self._client.get(f"{BASE_URL}/user/balance")
        except httpx.TimeoutException:
            raise DeepSeekAPIError("请求超时")
        except httpx.NetworkError as e:
            raise DeepSeekAPIError(f"网络错误: {e}")
        except httpx.HTTPError as e:
            raise DeepSeekAPIError(f"HTTP 错误: {e}")

        if response.status_code == 401:
            raise AuthError("API Key 无效 (401)")
        if response.status_code == 403:
            raise AuthError("API Key 无权限 (403)")
        if response.status_code == 429:
            raise DeepSeekAPIError("请求过于频繁 (429)")
        if not response.is_success:
            raise DeepSeekAPIError(f"API 返回错误状态码 {response.status_code}")

        try:
            data = response.json()
        except (ValueError, TypeError) as e:
            raise DeepSeekAPIError(f"响应 JSON 解析失败: {e}")

        try:
            balance_infos = data.get("balance_infos", [])
            total_balance = 0.0
            if balance_infos:
                total_balance = float(balance_infos[0].get("total_balance", "0"))
            return {
                "is_available": data.get("is_available", False),
                "balance": total_balance,
            }
        except (KeyError, ValueError, TypeError) as e:
            raise DeepSeekAPIError(f"余额数据格式异常: {e}")
