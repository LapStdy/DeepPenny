import logging
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QFrame, QHBoxLayout, QLabel, QPushButton, QApplication
)
from PyQt6.QtCore import Qt, QTimer, QRect, QPoint, QEvent, QByteArray, QSize
from PyQt6.QtGui import QPixmap, QPainter, QIcon, QFont
from PyQt6.QtSvg import QSvgRenderer

from ui.settings_dialog import SettingsDialog
from api.deepseek_api import AuthError, DeepSeekAPIError

logger = logging.getLogger("DeepPenny.ui")

WINDOW_WIDTH = 240
WINDOW_HEIGHT = 50
ERROR_MAX_LENGTH = 18
STYLES_PATH = Path("resources/styles.qss")
ICON_DIR = Path("resources/icons")
ICON_REFRESH = ICON_DIR / "redo.svg"
ICON_SETTINGS = ICON_DIR / "setting-one.svg"
ICON_SIZE = 16


def _load_svg_icon(svg_path: Path, stroke_color: str) -> QIcon:
    svg_data = svg_path.read_text(encoding="utf-8")
    svg_data = svg_data.replace('#333', stroke_color)
    renderer = QSvgRenderer(QByteArray(svg_data.encode()))
    pixmap = QPixmap(ICON_SIZE, ICON_SIZE)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)


class FloatingWindow(QWidget):

    def __init__(self, config, api, on_config_changed=None):
        super().__init__()
        self.config = config
        self.api = api
        self.snap_manager = None
        self._on_config_changed = on_config_changed
        self._dragging = False
        self._drag_pos = None
        self._hovered = False

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)

        self._setup_ui()
        self._apply_styles()
        self._setup_timer()

    def _setup_ui(self):
        self.container = QFrame(self)
        self.container.setObjectName("container")
        self.container.setAttribute(Qt.WidgetAttribute.WA_Hover)

        self.close_btn = QPushButton("✕", self)
        self.close_btn.setObjectName("closeBtn")
        self.close_btn.setFixedSize(14, 14)
        self.close_btn.move(2, 2)
        self.close_btn.installEventFilter(self)

        self.container.installEventFilter(self)

        content = QHBoxLayout(self.container)
        content.setContentsMargins(16, 4, 8, 4)
        content.setSpacing(6)

        self.drag_area = QWidget()
        self.drag_area.setObjectName("dragArea")
        self.drag_area.setFixedWidth(22)

        drag_layout = QHBoxLayout(self.drag_area)
        drag_layout.setContentsMargins(0, 3, 6, 3)
        self.drag_handle = QLabel("│")
        self.drag_handle.setObjectName("dragHandle")
        self.drag_handle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drag_layout.addWidget(self.drag_handle)

        self.balance_label = QLabel("余额: --.--")
        self.balance_label.setObjectName("balanceLabel")

        self.unit_label = QLabel("元")
        self.unit_label.setObjectName("unitLabel")

        aa_font = QFont()
        aa_font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        self.balance_label.setFont(aa_font)
        self.unit_label.setFont(aa_font)

        self.error_label = QLabel("")
        self.error_label.setObjectName("errorLabel")
        self.error_label.hide()

        COLOR_NORMAL = "#ffffff"
        COLOR_HOVER = "#ffffff"

        self._refresh_icon_normal = _load_svg_icon(ICON_REFRESH, COLOR_NORMAL)

        self.refresh_btn = QPushButton()
        self.refresh_btn.setObjectName("actionBtn")
        self.refresh_btn.setIcon(self._refresh_icon_normal)
        self.refresh_btn.setIconSize(QSize(ICON_SIZE, ICON_SIZE))
        self.refresh_btn.setFixedWidth(24)
        self.refresh_btn.setToolTip("刷新")

        self._settings_icon_normal = _load_svg_icon(ICON_SETTINGS, COLOR_NORMAL)

        self.settings_btn = QPushButton()
        self.settings_btn.setObjectName("actionBtn")
        self.settings_btn.setIcon(self._settings_icon_normal)
        self.settings_btn.setIconSize(QSize(ICON_SIZE, ICON_SIZE))
        self.settings_btn.setFixedWidth(24)
        self.settings_btn.setToolTip("设置")

        content.addWidget(self.drag_area)
        content.addWidget(self.balance_label)
        content.addWidget(self.unit_label)
        content.addStretch()
        content.addWidget(self.refresh_btn)
        content.addWidget(self.settings_btn)

        self.refresh_btn.clicked.connect(self.refresh_balance)
        self.settings_btn.clicked.connect(self._open_settings)
        self.close_btn.clicked.connect(QApplication.instance().quit)

        self.setMouseTracking(True)
        self.container.setMouseTracking(True)

        self._decoration_widgets = (
            self.drag_area, self.drag_handle, self.close_btn
        )

    def _apply_styles(self):
        try:
            with open(STYLES_PATH, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            pass

    def _setup_timer(self):
        interval = self.config.get("refresh_interval", 60)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh_balance)
        self._timer.start(interval * 1000)

    def _refresh_decoration_style(self):
        for w in self._decoration_widgets:
            w.style().unpolish(w)
            w.style().polish(w)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.container.setGeometry(self.rect())

    def eventFilter(self, obj, event):
        if obj is self.container:
            if event.type() == QEvent.Type.Enter:
                self._hovered = True
                self._set_decoration_active(True)
            elif event.type() == QEvent.Type.Leave:
                if not self._dragging:
                    self._hovered = False
                    self._set_decoration_active(False)
        elif obj is self.close_btn:
            if event.type() == QEvent.Type.Enter:
                self._set_decoration_active(True)
            elif event.type() == QEvent.Type.Leave:
                if not self._hovered:
                    self._set_decoration_active(False)
        return super().eventFilter(obj, event)

    def _set_decoration_active(self, active: bool):
        for w in self._decoration_widgets:
            w.setProperty("active", active)
        self._refresh_decoration_style()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            drag_origin = self.drag_area.mapToGlobal(QPoint(0, 0))
            drag_rect = QRect(drag_origin, self.drag_area.size())
            if drag_rect.contains(event.globalPosition().toPoint()):
                self._dragging = True
                self._drag_pos = (
                    event.globalPosition().toPoint()
                    - self.frameGeometry().topLeft()
                )
                if self.snap_manager:
                    self.snap_manager.on_drag_start()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging:
            global_pos = event.globalPosition().toPoint()
            self.move(global_pos - self._drag_pos)
            if self.snap_manager:
                self.snap_manager.on_drag_move(global_pos)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._dragging:
            self._dragging = False
            global_pos = event.globalPosition().toPoint()
            if self.snap_manager:
                self.snap_manager.on_drag_end(global_pos)
            if not self._hovered:
                self._set_decoration_active(False)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def set_snapped_background(self, snapped: bool):
        self.container.setProperty("snapped", snapped)
        self.container.style().unpolish(self.container)
        self.container.style().polish(self.container)

    def refresh_balance(self):
        self.error_label.hide()
        self.balance_label.setText("余额: --.--")

        if not self.api.api_key:
            self._show_error("请设置 API Key")
            return

        try:
            data = self.api.get_balance()
            balance = data.get("balance", 0)
            self.balance_label.setText(f"余额: {balance:.2f}")
            logger.info("余额刷新成功: %.2f 元", balance)
        except AuthError as e:
            logger.warning("认证失败: %s", e)
            self._show_error(str(e))
        except DeepSeekAPIError as e:
            logger.warning("API 错误: %s", e)
            self._show_error(str(e))
        except Exception as e:
            logger.error("未知错误: %s", e)
            self._show_error(f"请求失败: {e}")

    def _show_error(self, msg: str):
        display = msg if len(msg) <= ERROR_MAX_LENGTH else msg[:ERROR_MAX_LENGTH - 2] + ".."
        self.error_label.setText(display)
        self.error_label.show()
        QTimer.singleShot(3000, self.error_label.hide)

    def _open_settings(self):
        current_interval = self.config.get("refresh_interval", 60)
        dialog = SettingsDialog(
            current_key=self.api.api_key,
            current_interval=current_interval,
            parent=self,
        )
        if dialog.exec() == SettingsDialog.DialogCode.Accepted:
            new_key = dialog.get_api_key()
            new_interval = dialog.get_refresh_interval()
            self.api.set_api_key(new_key)
            self.config["api_key"] = new_key
            self.config["refresh_interval"] = new_interval
            self._restart_timer(new_interval)
            if self._on_config_changed:
                self._on_config_changed(self.config)
            self.refresh_balance()

    def _restart_timer(self, interval_seconds: int):
        self._timer.stop()
        self._timer.start(interval_seconds * 1000)
        logger.info("刷新间隔已更新为 %d 秒", interval_seconds)
