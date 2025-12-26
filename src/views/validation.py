"""Validation functions for SNIL and file structure."""
from PyQt5.QtGui import QColor


def validate_structure(self):
    """Validate current SNIL structure."""
    is_valid = self.validator.validate_structure(self.temp_structure)
    if is_valid:
        self.status_bar.showMessage("Structure validation passed.", 3000)
    else:
        color = QColor(self.STYLES['DarkTheme']['NotificationError'])
        self.show_notification(f"Structure validation failed: {self.validator.get_last_error()}", color, duration_ms=5000)
