from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QLabel, QSpinBox, QFormLayout, QGroupBox,
)
from PyQt6.QtCore import Qt

from api.deepseek_api import validate_api_key


class SettingsDialog(QDialog):

    def __init__(self, current_key: str = "", current_interval: int = 60, parent=None):
        super().__init__(parent)
        self.setWindowTitle("DeepSeek 设置")
        self.setFixedSize(440, 280)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowStaysOnTopHint
        )

        self.api_key = current_key
        self.interval = current_interval

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)

        api_group = QGroupBox("API 密钥")
        api_layout = QVBoxLayout(api_group)

        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        self.key_input.setText(current_key)
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        api_layout.addWidget(self.key_input)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #ff6b6b; font-size: 11px;")
        self.error_label.hide()
        api_layout.addWidget(self.error_label)

        main_layout.addWidget(api_group)

        refresh_group = QGroupBox("刷新设置")
        refresh_layout = QFormLayout(refresh_group)

        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(10, 3600)
        self.interval_spin.setValue(current_interval)
        self.interval_spin.setSuffix(" 秒")
        self.interval_spin.setSingleStep(10)
        refresh_layout.addRow("刷新间隔：", self.interval_spin)

        main_layout.addWidget(refresh_group)

        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("保存")
        self.cancel_btn = QPushButton("取消")
        btn_layout.addStretch()
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        main_layout.addLayout(btn_layout)

        self.save_btn.clicked.connect(self._on_save)
        self.cancel_btn.clicked.connect(self.reject)

    def _on_save(self):
        key = self.key_input.text()
        try:
            self.api_key = validate_api_key(key)
        except ValueError as e:
            self.error_label.setText(str(e))
            self.error_label.show()
            return
        self.interval = self.interval_spin.value()
        self.accept()

    def get_api_key(self) -> str:
        return self.api_key

    def get_refresh_interval(self) -> int:
        return self.interval
