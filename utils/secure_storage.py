import json
import logging
from pathlib import Path

logger = logging.getLogger("DeepPenny.secure_storage")

_SERVICE_NAME = "DeepPenny"
_KEY_USERNAME = "api_key"
_CONFIG_PATH = Path("config.json")

try:
    import keyring
    HAS_KEYRING = True
except ImportError:
    HAS_KEYRING = False
    logger.warning("keyring 库未安装，API Key 将以明文存储在 config.json 中")


def save_api_key(api_key: str):
    if HAS_KEYRING:
        try:
            keyring.set_password(_SERVICE_NAME, _KEY_USERNAME, api_key)
            logger.info("API Key 已安全存储到系统密钥链")
            _remove_key_from_config()
            return True
        except Exception as e:
            logger.warning(f"keyring 存储失败，回退到配置文件: {e}")

    _save_key_to_config(api_key)
    return True


def load_api_key() -> str:
    if HAS_KEYRING:
        try:
            stored = keyring.get_password(_SERVICE_NAME, _KEY_USERNAME)
            if stored:
                logger.info("API Key 已从系统密钥链加载")
                return stored
        except Exception as e:
            logger.warning(f"keyring 读取失败，尝试配置文件: {e}")

    return _load_key_from_config()


def delete_api_key():
    if HAS_KEYRING:
        try:
            keyring.delete_password(_SERVICE_NAME, _KEY_USERNAME)
            logger.info("API Key 已从系统密钥链删除")
        except keyring.errors.PasswordDeleteError:
            pass
        except Exception as e:
            logger.warning(f"keyring 删除失败: {e}")

    _remove_key_from_config()


def _load_key_from_config() -> str:
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config.get("api_key", "")
    except (FileNotFoundError, json.JSONDecodeError):
        return ""


def _save_key_to_config(api_key: str):
    try:
        config = {}
        if _CONFIG_PATH.exists():
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
        config["api_key"] = api_key
        with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except OSError as e:
        logger.error(f"保存 API Key 到配置文件失败: {e}")


def _remove_key_from_config():
    try:
        if not _CONFIG_PATH.exists():
            return
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
        if "api_key" in config:
            del config["api_key"]
        with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except (OSError, json.JSONDecodeError) as e:
        logger.error(f"从配置文件中移除 API Key 失败: {e}")
