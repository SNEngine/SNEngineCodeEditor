# src/settings_dialog.py
import sys
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QCheckBox, QLabel, QSpinBox, QPushButton,
    QComboBox, QDialogButtonBox, QGroupBox, QMessageBox
)
from PyQt5.QtCore import pyqtSignal
from settings_manager import SettingsManager


class SettingsDialog(QDialog):
    """
    Диалог настроек редактора YAML.
    Позволяет пользователю настраивать параметры редактора.
    """
    settings_changed = pyqtSignal(dict)  # Сигнал, который отправляется при изменении настроек

    def __init__(self, settings_manager: SettingsManager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setWindowTitle("Настройки редактора")
        self.setModal(True)
        self.resize(400, 300)

        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """Инициализирует пользовательский интерфейс."""
        layout = QVBoxLayout()
        
        # Группа для настроек интерфейса
        interface_group = QGroupBox("Interface")
        interface_layout = QFormLayout()

        # Чекбокс для отображения номеров строк
        self.line_numbers_checkbox = QCheckBox("Show line numbers")
        interface_layout.addRow(self.line_numbers_checkbox)

        # Чекбокс для подсветки текущей строки
        self.highlight_current_line_checkbox = QCheckBox("Highlight current line")
        interface_layout.addRow(self.highlight_current_line_checkbox)

        # Комбобокс для выбора темы
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark"])
        self.theme_combo.setItemData(0, "dark")  # Устанавливаем внутренние значения
        interface_layout.addRow("Theme:", self.theme_combo)

        # Спинбокс для размера шрифта
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(10, 24)  # Match the range used in hotkeys
        self.font_size_spin.setValue(14)
        interface_layout.addRow("Font size:", self.font_size_spin)

        # Комбобокс для выбора семейства шрифтов
        from PyQt5.QtGui import QFontDatabase
        self.font_family_combo = QComboBox()
        # Get all available font families from the OS
        font_database = QFontDatabase()
        font_families = font_database.families()
        self.font_family_combo.addItems(font_families)
        interface_layout.addRow("Font family:", self.font_family_combo)

        interface_group.setLayout(interface_layout)
        layout.addWidget(interface_group)

        # Группа для эффектов
        effects_group = QGroupBox("Effects")
        effects_layout = QFormLayout()

        # Чекбокс для частиц при печатании
        self.typing_particles_checkbox = QCheckBox("Enable typing particles")
        effects_layout.addRow(self.typing_particles_checkbox)

        effects_group.setLayout(effects_layout)
        layout.addWidget(effects_group)

        # Группа для настроек автосохранения
        auto_save_group = QGroupBox("Auto-save")
        auto_save_layout = QFormLayout()

        # Чекбокс для автосохранения
        self.auto_save_checkbox = QCheckBox("Enable auto-save")
        auto_save_layout.addRow(self.auto_save_checkbox)

        # Спинбокс для интервала автосохранения
        self.auto_save_interval_spin = QSpinBox()
        self.auto_save_interval_spin.setRange(5, 300)  # от 5 до 300 секунд
        self.auto_save_interval_spin.setValue(30)
        self.auto_save_interval_spin.setSuffix(" sec")
        auto_save_layout.addRow("Auto-save interval:", self.auto_save_interval_spin)

        auto_save_group.setLayout(auto_save_layout)
        layout.addWidget(auto_save_group)

        # Кнопки OK, Cancel и Reset
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        self.reset_button = QPushButton("Reset to Defaults")
        self.reset_button.clicked.connect(self.reset_to_defaults)

        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def reset_to_defaults(self):
        """Reset all settings to their default values."""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to their defaults?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Reset settings manager to defaults
            self.settings_manager.reset_to_defaults()

            # Reload the default values into the UI
            self.load_settings()

    def load_settings(self):
        """Loads current settings into the interface."""
        # Load interface settings
        self.line_numbers_checkbox.setChecked(self.settings_manager.show_line_numbers)
        self.highlight_current_line_checkbox.setChecked(self.settings_manager.highlight_current_line)

        theme = self.settings_manager.theme
        if theme == "dark":
            self.theme_combo.setCurrentIndex(0)
        else:
            # If theme is not "dark", set to "dark" as only option
            self.theme_combo.setCurrentIndex(0)
            # Update the settings manager to reflect the change
            self.settings_manager.theme = "dark"

        self.font_size_spin.setValue(self.settings_manager.font_size)

        font_family = self.settings_manager.font_family
        font_index = self.font_family_combo.findText(font_family)
        if font_index >= 0:
            self.font_family_combo.setCurrentIndex(font_index)
        else:
            self.font_family_combo.setCurrentText("Consolas")

        # Load effect settings
        self.typing_particles_checkbox.setChecked(self.settings_manager.typing_particles_enabled)

        # Load auto-save settings
        self.auto_save_checkbox.setChecked(self.settings_manager.auto_save_enabled)
        self.auto_save_interval_spin.setValue(self.settings_manager.auto_save_interval)

    def save_settings(self):
        """Saves settings from the interface to the settings manager."""
        # Save interface settings
        self.settings_manager.show_line_numbers = self.line_numbers_checkbox.isChecked()
        self.settings_manager.highlight_current_line = self.highlight_current_line_checkbox.isChecked()

        theme_value = self.theme_combo.itemData(self.theme_combo.currentIndex())
        self.settings_manager.theme = theme_value

        self.settings_manager.font_size = self.font_size_spin.value()
        self.settings_manager.font_family = self.font_family_combo.currentText()

        # Save effect settings
        self.settings_manager.typing_particles_enabled = self.typing_particles_checkbox.isChecked()

        # Save auto-save settings
        self.settings_manager.auto_save_enabled = self.auto_save_checkbox.isChecked()
        self.settings_manager.auto_save_interval = self.auto_save_interval_spin.value()

        # Save changes to file
        self.settings_manager.save_settings()

        # Send signal that settings changed
        current_settings = {
            'show_line_numbers': self.settings_manager.show_line_numbers,
            'highlight_current_line': self.settings_manager.highlight_current_line,
            'theme': self.settings_manager.theme,
            'font_size': self.settings_manager.font_size,
            'font_family': self.settings_manager.font_family,
            'typing_particles_enabled': self.settings_manager.typing_particles_enabled,
            'auto_save_enabled': self.settings_manager.auto_save_enabled,
            'auto_save_interval': self.settings_manager.auto_save_interval
        }
        self.settings_changed.emit(current_settings)

    def accept(self):
        """Вызывается при нажатии OK."""
        self.save_settings()
        super().accept()