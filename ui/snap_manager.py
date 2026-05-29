from PyQt6.QtWidgets import QWidget, QLabel
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPainter, QPen, QColor


class SnapZoneIndicator(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self.label = QLabel("移动到此处固定", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("color: rgba(255, 255, 255, 180); font-size: 12px;")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pen = QPen(QColor(255, 255, 255, 80))
        pen.setStyle(Qt.PenStyle.DashLine)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(QColor(255, 255, 255, 20))
        rect = self.rect().adjusted(2, 2, -2, -2)
        painter.drawRect(rect)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.label.setGeometry(self.rect())


class SnapManager:

    def __init__(self, floating_window, offset=300):
        self.window = floating_window
        self._offset = offset
        self.is_snapped = False
        self._indicator = SnapZoneIndicator()
        self._snap_threshold = 60

    def _get_taskbar_rect(self) -> QRect:
        screen = self.window.screen()
        if not screen:
            return QRect()
        full_rect = screen.geometry()
        work_rect = screen.availableGeometry()
        if work_rect.height() < full_rect.height():
            return QRect(
                full_rect.x(),
                full_rect.y() + work_rect.height(),
                full_rect.width(),
                full_rect.height() - work_rect.height(),
            )
        if work_rect.width() < full_rect.width():
            return QRect(
                full_rect.x() + work_rect.width(),
                full_rect.y(),
                full_rect.width() - work_rect.width(),
                full_rect.height(),
            )
        return QRect()

    def _is_near_taskbar(self, global_pos) -> bool:
        taskbar_rect = self._get_taskbar_rect()
        if not taskbar_rect.isValid():
            return False
        window_bottom = self.window.geometry().bottom()
        return abs(window_bottom - taskbar_rect.top()) < self._snap_threshold + 20

    def on_drag_start(self):
        pass

    def on_drag_move(self, global_pos):
        taskbar_rect = self._get_taskbar_rect()
        if not taskbar_rect.isValid():
            self._hide_indicator()
            return

        if self._is_near_taskbar(global_pos):
            self._show_indicator(taskbar_rect)
        else:
            self._hide_indicator()

    def on_drag_end(self, global_pos):
        self._hide_indicator()
        if self._is_near_taskbar(global_pos):
            self.snap()
        elif self.is_snapped:
            self.unsnap()

    def snap(self):
        self.is_snapped = True
        taskbar_rect = self._get_taskbar_rect()
        if not taskbar_rect.isValid():
            return
        win_w = self.window.width()
        win_h = self.window.height()
        snap_x = taskbar_rect.x() + taskbar_rect.width() - win_w - self._offset
        snap_y = taskbar_rect.y() + (taskbar_rect.height() - win_h) // 2
        self.window.move(snap_x, snap_y)
        self.window.set_snapped_background(True)

    def unsnap(self):
        self.is_snapped = False
        self.window.set_snapped_background(False)

    def _show_indicator(self, taskbar_rect):
        win_w = self.window.width()
        win_h = self.window.height()
        ix = taskbar_rect.x() + taskbar_rect.width() - win_w - self._offset
        iy = taskbar_rect.y() + (taskbar_rect.height() - win_h) // 2
        self._indicator.setGeometry(ix, iy, win_w, win_h)
        self._indicator.show()

    def _hide_indicator(self):
        self._indicator.hide()
