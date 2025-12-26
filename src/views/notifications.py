from PyQt5.QtGui import QColor

def show_notification(self, message: str, color: QColor, duration_ms: int = 3000):
    if self._notification_label:
        self._notification_label.setText(message)
        color_hex = color.name()
        text_color = self.STYLES['DarkTheme']['NotificationTextColor']
        self._notification_label.setStyleSheet(f"background-color: {color_hex}; padding: 0 10px; color: {text_color}; border-radius: 3px;")
        self._notification_label.setVisible(True)
        self._notification_timer.start(duration_ms)


def hide_notification(self):
    if self._notification_label:
        self._notification_label.setVisible(False)
        self._notification_timer.stop()
