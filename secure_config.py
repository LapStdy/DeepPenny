import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

CONFIG_PATH = Path("config.json")
KEYRING_SERVICE = "DeepPenny"
KEYRING_KEY = "api_key"

try:
    import keyring
    HAS_KEYRING = True
except ImportError:
    HAS_KEYRING = False
    logger.info("keyring 库未安装，API Key 将以明文存储在 config.json 中")


def _load_config_file() -> dict:
    defaults = {
        "api_key": "",
        "refresh_interval": 60,
        "window_position": {"x": None, "y": None},
        "always_on_top": True,
    }
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return defaults

    for key, value in defaults.items():
        config.setdefault(key, value)
    if isinstance(config.get("window_position"), dict):
        config["window_position"].setdefault("x", None)
        config["window_position"].setdefault("y", None)
    else:
        config["window_position"] = {"x": None, "y": None}
    return config


def _save_config_file(config: dict):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except OSError as e:
        logger.error(f"保存配置文件失败: {e}")


def get_api_key() -> str:
    if HAS_KEYRING:
        try:
            key = keyring.get_password(KEYRING_SERVICE, KEYRING_KEY)
            if