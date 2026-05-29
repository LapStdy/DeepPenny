import json
import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from api.deepseek_api import DeepSeekAPI
from ui.floating_window import FloatingWindow
from ui.snap_manager import SnapManager
from utils.secure_storage import save_api_key, load_api_key
from utils.logger import setup_logger

logger = setup_logger()

CONFIG_PATH = Path("config.json")


def load_config() -> dict:
    defaults = {
        "api_key": "",
        "refresh_interval": 60,
        "snap_offset": 300,
    }
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logger.info("配置文件不存在或格式错误，使用默认配置")
        return defaults

    for key, value in defaults.items():
        config.setdefault(key, value)

    api_key = load_api_key()
    if api_key:
        config["api_key"] = api_key
    return config


def save_config(config: dict):
    if config.get("api_key"):
        save_api_key(config["api_key"])
    safe_config = {k: v for k, v in config.items() if k != "api_key"}
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(safe_config, f, ensure_ascii=False, indent=2)
        logger.debug("配置文件已保存")
    except OSError as e:
        logger.error("保存配置文件失败: %s", e)


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    config = load_config()
    api = DeepSeekAPI(api_key=config.get("api_key", ""))

    window = FloatingWindow(
        config, api,
        on_config_changed=save_config,
    )
    snap_manager = SnapManager(window, offset=config.get("snap_offset", 300))
    window.snap_manager = snap_manager

    window.show()
    snap_manager.snap()
    logger.info("DeepPenny 启动完成")

    if not config.get("api_key"):
        window._open_settings()

    window.refresh_balance()

    def _on_quit():
        save_config(config)
        api.close()
        logger.info("DeepPenny 已正常退出")

    app.aboutToQuit.connect(_on_quit)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
