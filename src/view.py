# src/view.py
import os
import sys
import yaml
import collections
from typing import Dict, Any, Optional

from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QSplitter
from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtWidgets import QToolBar
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QStatusBar
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QScrollArea
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QComboBox

from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QFont
from PyQt5.QtGui import QColor
from PyQt5.QtGui import QPixmap
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtCore import QSize

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QTimer
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtCore import QByteArray
from PyQt5.QtCore import QUrl
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve

from PyQt5.QtWidgets import QGraphicsOpacityEffect

# Imports for .models should be available if they are in the same src folder
from models import SNILTab
from snil_highlighter import SNILHighlighter
from validator import StructureValidator
from session_manager import SessionManager # Add this if session_manager.py is in src/
from settings_manager import SettingsManager
from file_service import FileService # Import the FileService from the new file
from views.tabs import question_message_box # Import the custom message box function

# --- UTILITY FOR CREATING QIcon FROM SVG string ---
def create_icon_from_svg(svg_content: str, size: QSize = QSize(16, 16)) -> QIcon:
    """Creates a QIcon from SVG code using a data URI."""
    svg_bytes = QByteArray(svg_content.encode('utf-8'))
    base64_data = svg_bytes.toBase64().data().decode()
    data_uri = f'data:image:svg+xml;base64,{base64_data}'
    icon = QIcon(data_uri)
    return icon

# -------------------------------------------------------------------


class SNILEditorWindow(QMainWindow):

    def _load_folder_icon(self) -> str:
        """Loads the folder SVG icon from file, fallback to default if not found."""
        try:
            icon_path = self._get_resource_path('icons/folder.svg')
            with open(icon_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            # Fallback to default colored icon if file not found
            folder_color = self.STYLES['DarkTheme'].get('FolderIconColor', '#E06C75')
            return f"""
<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">
  <path fill="{folder_color}" d="M14 6H8.5L7 4.5H2a1 1 0 0 0-1 1V11a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V7a1 1 0 0 0-1-1zM2 5h4.5l1 1h6.5v4H2V5z"/>
</svg>
"""

    def _load_yaml_file_icon(self) -> str:
        """Loads the YAML file SVG icon from file, fallback to default if not found."""
        try:
            icon_path = self._get_resource_path('icons/yaml_file.svg')
            with open(icon_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            # Fallback to default colored icon if file not found
            yaml_color = self.STYLES['DarkTheme'].get('YamlFileIconColor', '#CCCCCC')
            return f"""
<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">
  <path fill="{yaml_color}" d="M4 1h8a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1zM4 2v12h8V2H4z"/>
  <text x="8" y="10" font-family="Arial, sans-serif" font-size="8" font-weight="bold" fill="#007bff" text-anchor="middle">
    Y
  </text>
</svg>
"""

    def _load_android_icon(self) -> str:
        """Loads the Android SVG icon from file, fallback to default if not found."""
        try:
            icon_path = self._get_resource_path('icons/android.svg')
            with open(icon_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            # Fallback to default Android icon if file not found
            android_color = self.STYLES['DarkTheme'].get('HighlightColor', '#C84B31')
            return f"""
<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24">
  <path fill="{android_color}" d="M17.66,11.2C17.43,10.9 17.15,10.64 16.89,10.38C16.22,9.78 15.46,9.3 14.82,8.96C14.71,8.9 14.59,8.85 14.47,8.8C12.55,7.84 10.45,7.84 8.53,8.8C8.41,8.85 8.29,8.9 8.18,8.96C7.54,9.3 6.78,9.78 6.11,10.38C5.85,10.64 5.57,10.9 5.34,11.2C5.25,11.33 5.17,11.46 5.1,11.6C4.92,11.95 4.79,12.32 4.72,12.7C4.65,13.08 4.63,13.47 4.65,13.86C4.67,14.25 4.74,14.63 4.85,15C5.04,15.66 5.36,16.26 5.76,16.77C6.16,17.28 6.64,17.69 7.17,18C7.6,18.23 8.05,18.4 8.51,18.5C8.97,18.6 9.44,18.64 9.91,18.61C10.38,18.58 10.84,18.48 11.27,18.32C11.7,18.16 12.09,17.94 12.44,17.66C12.79,17.94 13.18,18.16 13.61,18.32C14.04,18.48 14.5,18.58 14.97,18.61C15.44,18.64 15.91,18.6 16.37,18.5C16.83,18.4 17.28,18.23 17.68,18C18.21,17.69 18.69,17.28 19.09,16.77C19.49,16.26 19.81,15.66 20,15C20.11,14.63 20.18,14.25 20.2,13.86C20.22,13.47 20.2,13.08 20.13,12.7C20.06,12.32 19.93,11.95 19.75,11.6C19.68,11.46 19.6,11.33 19.51,11.2C19.28,10.9 19,10.64 18.74,10.38C18.48,10.12 18.22,9.86 17.96,9.6C17.89,9.54 17.81,9.48 17.73,9.42C17.66,9.36 17.59,9.3 17.52,9.24C17.72,9.6 17.82,9.99 17.82,10.38C17.82,10.64 17.78,10.89 17.66,11.2Z"/>
  <path fill="{android_color}" d="M9,16.75C8.31,16.75 7.75,16.19 7.75,15.5C7.75,14.81 8.31,14.25 9,14.25C9.69,14.25 10.25,14.81 10.25,15.5C10.25,16.19 9.69,16.75 9,16.75Z"/>
  <path fill="{android_color}" d="M15,16.75C14.31,16.75 13.75,16.19 13.75,15.5C13.75,14.81 14.31,14.25 15,14.25C15.69,14.25 16.25,14.81 16.25,15.5C16.25,16.19 15.69,16.75 15,16.75Z"/>
</svg>
"""

    def _update_svg_colors(self, svg_content: str, folder_color: str = None, yaml_color: str = None, excel_color: str = None) -> str:
        """Updates colors in SVG content based on current styles, replacing white with the specified color."""

        # For folder icon: if it contains the folder path and folder_color is specified, replace white with folder_color
        if folder_color and 'M2 4.5A1.5 1.5 0 0 1 3.5 3h3.086a1.5 1.5 0 0 1 1.06.44L8.56 4.354A1.5 1.5 0 0 0 9.62 4.8H12.5A1.5 1.5 0 0 1 14 6.3v5.2A1.5 1.5 0 0 1 12.5 13h-9A1.5 1.5 0 0 1 2 11.5v-7z' in svg_content:
            # Replace 'white' with the specified folder color in both the svg tag and path tags
            svg_content = svg_content.replace('fill="white"', f'fill="{folder_color}"')

        # For YAML file icon: if it contains the document path and yaml_color is specified, replace white with yaml_color
        if yaml_color and 'M4 2h5.5L13 5.5V13a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V3a1 1 0 0 1 1-1z' in svg_content:
            # Replace 'white' with the specified YAML color in all fill attributes
            svg_content = svg_content.replace('fill="white"', f'fill="{yaml_color}"')

        return svg_content

    def _create_icon_from_svg_content(self, svg_content: str, is_folder: bool = False, is_yaml: bool = False) -> QIcon:
        """Creates a QIcon from SVG content using QSvgRenderer for better compatibility."""
        try:
            # Create a pixmap with the desired size
            pixmap = QPixmap(16, 16)
            pixmap.fill(Qt.transparent)  # Make background transparent

            # Create a painter to draw on the pixmap
            from PyQt5.QtGui import QPainter
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

            # Create an SVG renderer and render to the painter
            from PyQt5.QtCore import QByteArray
            svg_bytes = QByteArray(svg_content.encode('utf-8'))
            renderer = QSvgRenderer(svg_bytes)
            renderer.render(painter)

            painter.end()

            # Return QIcon from the pixmap
            return QIcon(pixmap)
        except Exception:
            # Fallback to the original method if SVG rendering fails
            return create_icon_from_svg(svg_content)

    def __init__(self):
        super().__init__()

        # --- Styles Initialization ---
        self.STYLES = self._load_styles()
        self.CSS_STYLES = self._generate_css(self.STYLES)

        self.setWindowTitle("SNIL Editor")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet(self.CSS_STYLES) # Apply generated styles

        # --- Icons Initialization ---
        folder_icon_color = self.STYLES['DarkTheme'].get('FolderIconColor', '#E06C75')
        yaml_icon_color = self.STYLES['DarkTheme'].get('YamlFileIconColor', '#CCCCCC')

        # Load SVG contents
        folder_svg_content = self._load_folder_icon()
        yaml_svg_content = self._load_yaml_file_icon()
        android_svg_content = self._load_android_icon()

        # Apply color updates based on loaded styles
        folder_svg_content = self._update_svg_colors(folder_svg_content, folder_color=folder_icon_color)
        yaml_svg_content = self._update_svg_colors(yaml_svg_content, yaml_color=yaml_icon_color)
        # Android icon will use the highlight color from theme

        # Create icons with applied colors
        self.icon_folder = self._create_icon_from_svg_content(folder_svg_content)
        self.icon_yaml = self._create_icon_from_svg_content(yaml_svg_content)
        self.icon_android = self._create_icon_from_svg_content(android_svg_content, is_folder=False, is_yaml=False)
        self._last_open_dir: str = os.path.expanduser("~")

        # --- Model/Services ---
        self.file_service = FileService()
        self.validator = StructureValidator() # <-- VALIDATOR INITIALIZATION
        self.temp_structure = {'root_path': None, 'structure': {}}
        self.open_tabs: list[SNILTab] = []
        self.current_tab_index = -1
        self.current_tab: SNILTab | None = None

        # UI Variables (like in C#)
        self.root_path: str | None = None
        self._notification_timer = QTimer(self)
        self._notification_timer.timeout.connect(self.hide_notification)
        self._notification_label: QLabel | None = None
        self._current_font_size = 14
        self._foldouts: Dict[str, bool] = {} # For storing folder states

        # Устанавливаем иконку для главного окна
        icon_path = self._get_resource_path('icons/app.svg')
        try:
            # Загружаем SVG иконку и устанавливаем как иконку окна
            with open(icon_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()
            # Создаем иконку из SVG
            icon = self._create_icon_from_svg_content(svg_content)
            if icon:
                self.setWindowIcon(icon)
        except Exception:
            # Если не удалось загрузить SVG иконку, используем стандартную иконку
            pass

        self.settings_manager = SettingsManager()

        # Initialize file system watcher for dialog files
        self.dialogue_watcher = None
        self.dialogue_watch_path = None

        # Initialize timer for delayed rescan to avoid multiple rapid scans
        self.rescan_timer = QTimer()
        self.rescan_timer.setSingleShot(True)
        self.rescan_timer.timeout.connect(self.rescan_dialogues)

        # Initialize signal object for rescan requests from other threads
        from PyQt5.QtCore import QObject, pyqtSignal
        class RescanSignalObject(QObject):
            rescan_signal = pyqtSignal()

        self.rescan_signal_obj = RescanSignalObject()
        self.rescan_signal_obj.rescan_signal.connect(self._schedule_rescan)

        # Load SNIL syntax commands once at startup
        self.snil_commands = self._load_snil_syntax_commands()

        self.init_ui()
        self.update_status_bar()

        self.session_manager = SessionManager(self)
        self.session_manager.restore_session() # Restore session on startup

        # Initialize auto-save timer
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self.perform_auto_save)
        self._setup_auto_save_timer()

    def closeEvent(self, event):
        """
        Intercepts the window close event.
        First checks for unsaved changes, then saves the session.
        """

        # Check if there are tabs with unsaved changes
        dirty_tab = next((t for t in self.open_tabs if t.is_dirty), None)

        if dirty_tab:
            reply = question_message_box(self, 'Unsaved Changes',
                "You have unsaved changes. Do you want to save all files before quitting?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel, QMessageBox.Cancel)

            if reply == QMessageBox.Save:
                # Attempt to save all unsaved files
                for tab in [t for t in self.open_tabs if t.is_dirty]:
                    self.save_file_action(tab)

                # If there are still unsaved changes after attempting to save (e.g., due to YAML syntax error), cancel close.
                if any(t.is_dirty for t in self.open_tabs):
                    event.ignore()
                    return

            elif reply == QMessageBox.Cancel:
                event.ignore() # Cancel close
                return

        # Stop the file watcher before closing
        self.stop_watching_dialogues()

        # If closing is allowed (no unsaved changes or user pressed Discard/Save)
        self.session_manager.save_session() # Save session state

        event.accept()

    def _setup_auto_save_timer(self):
        """Setup the auto-save timer based on current settings"""
        # Stop the timer if it's running
        self.auto_save_timer.stop()

        # Check if auto-save is enabled
        if self.settings_manager.auto_save_enabled:
            # Set the interval from settings (convert from seconds to milliseconds)
            interval_ms = self.settings_manager.auto_save_interval * 1000
            self.auto_save_timer.setInterval(interval_ms)
            self.auto_save_timer.start()

    def perform_auto_save(self):
        """Perform auto-save of all dirty tabs"""
        if not self.settings_manager.auto_save_enabled:
            return

        # Save all open tabs that have unsaved changes
        dirty_tabs = [t for t in self.open_tabs if t.is_dirty and t.file_path]
        if dirty_tabs:
            for tab in dirty_tabs:
                try:
                    with open(tab.file_path, 'w', encoding='utf-8') as f:
                        f.write(tab.snil_text)
                    tab.is_dirty = False  # Mark as saved

                    # Update the UI to reflect the saved state
                    self.update_status_bar()
                except Exception as e:
                    print(f"Auto-save failed for {tab.file_path}: {e}")
                    # Don't stop auto-saving other files if one fails
                    continue

    def _get_resource_path(self, relative_path: str) -> str:
        """
        Gets the path to a resource.
        In EXE mode, the file structure is based on PyInstaller --add-data specification.
        """
        if getattr(sys, 'frozen', False):
            # In PyInstaller (EXE) mode
            base_path = os.path.dirname(sys.executable)

            # Check in executable directory (where --add-data puts files)
            full_path = os.path.join(base_path, relative_path)
            if os.path.exists(full_path):
                return full_path

            # Check in PyInstaller temp directory
            try:
                temp_path = sys._MEIPASS
                temp_full_path = os.path.join(temp_path, relative_path)
                if os.path.exists(temp_full_path):
                    return temp_full_path
            except AttributeError:
                # _MEIPASS not available, skip this check
                pass

            # If neither worked, default to base path
            return full_path
        else:
            # In development mode: styles.yaml is next to view.py (in the src folder)
            base_path = os.path.dirname(os.path.abspath(__file__))
            return os.path.join(base_path, relative_path)

    def _load_styles(self) -> Dict[str, Any]:
        """Loads styles from styles.yaml or uses backups."""

        # KEY CHANGE: Use _get_resource_path to access the file
        # Since in PyInstaller we specified --add-data "src/styles.yaml;src",
        # the file will be available in the 'src' folder relative to the PyInstaller base path.
        # But since view.py itself is in 'src' in development mode,
        # we just need to access the 'styles.yaml' file in our folder.

        # If view.py is in src/, and styles.yaml is next to it:

        # OLD CODE:
        # style_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'styles.yaml')

        # NEW CODE (Uses a path that works in PyInstaller and in development)
        style_file = self._get_resource_path('styles.yaml')

        # --- BACKUP STYLES (Updated for red-black theme) ---
        default_styles = {
            # ... (Your styles) ...
            'DarkTheme': {
                'Background': "#1A1A1A", 'Foreground': "#E8E8E8", 'SecondaryBackground': "#2A2A2A",
                'EditorBackground': "#1F1F1F", 'BorderColor': "#3A3A3A", 'HighlightColor': "#C84B31",
                'HoverColor': "#3A3A3A", 'FilePanelBackground': "#181818", 'FilePanelHover': "#2D2D2D",
                'FolderColor': "#E06C75", 'StatusDefault': "#999999", 'NotificationSuccess': "#6BA878",
                'NotificationError': "#D9685A",
                'NotificationWarning': "#E8C56B",
                'FolderIconColor': "#E06C75",  # Color for the folder icon
                'YamlFileIconColor': "#CCCCCC"  # Color for YAML file icon
            }
        }

        # ... (Rest of file loading logic) ...
        try:
            if os.path.exists(style_file):
                 # ... (Rest of loading logic) ...
                with open(style_file, 'r', encoding='utf-8') as f:
                    styles = yaml.safe_load(f)
                    # ... (Key check and return) ...
                    if styles and 'DarkTheme' in styles:
                        return styles
                    else:
                        print("Warning: styles.yaml found, but missing 'DarkTheme' key. Using default styles.")
                        return default_styles
            else:
                 print(f"Warning: styles.yaml not found at {style_file}. Using default styles.")
                 return default_styles
        except Exception as e:
            print(f"Error loading styles.yaml ({e}). Using default styles.")
            return default_styles

    # ... (Rest of _generate_css) ...
    def _generate_css(self, styles: Dict[str, Any]) -> str:
        """Generates a CSS string based on loaded styles."""
        theme = styles.get('DarkTheme', {})

        css = f"""
        QMainWindow, QWidget {{ background-color: {theme.get('Background')}; color: {theme.get('Foreground')}; }}
        QSplitter::handle {{ background-color: {theme.get('Background')}; }}

        /* TOOLBAR & ACTIONS (Fixed visual bugs of QAction buttons) */
        QToolBar {{
            background-color: {theme.get('SecondaryBackground')};
            spacing: 5px;
            border-bottom: 1px solid {theme.get('Background')};
        }}
        QToolButton {{
            color: {theme.get('Foreground')};
            background-color: {theme.get('SecondaryBackground')};
            border: 1px solid {theme.get('SecondaryBackground')};
            padding: 3px 6px;
        }}
        QToolButton:hover {{ background-color: {theme.get('HoverColor')}; border: 1px solid {theme.get('HoverColor')}; }}
        QToolButton:pressed {{ background-color: {theme.get('Background')}; }}

        /* File Panel */
        QWidget#FilePanelWidget {{ background-color: {theme.get('FilePanelBackground')}; }}
        QScrollArea {{ border: none; }}

        QPushButton {{ color: {theme.get('Foreground')}; background-color: {theme.get('FilePanelBackground')}; border: none; }}
        QPushButton:hover {{ background-color: {theme.get('FilePanelHover')}; }}

        /* Editor */
        QLineEdit {{
            background-color: {theme.get('EditorBackground')};
            color: {theme.get('Foreground')};
            border: 1px solid {theme.get('BorderColor')};
            padding: 2px;
        }}
        QTextEdit {{
            background-color: {theme.get('EditorBackground')};
            color: {theme.get('Foreground')};
            border: 1px solid {theme.get('NotificationError')};
            padding: 2px;
        }}

        /* Tab Bar */
        QToolBar#TabPlaceholder {{ background-color: {theme.get('Background')}; border: none; }}

        /* Status Bar */
        QStatusBar {{
            background-color: {theme.get('SecondaryBackground')};
            border-top: 1px solid {theme.get('Background')};
            color: {theme.get('StatusDefault')};
        }}

        /* Context Menu */
        QMenu {{
            background-color: {theme.get('SecondaryBackground')};
            color: {theme.get('Foreground')};
            border: 1px solid {theme.get('NotificationError')};
            border-radius: 4px;
        }}
        QMenu::item {{
            padding: 5px 15px 5px 25px; /* Add padding for better spacing */
            background-color: transparent;
        }}
        QMenu::item:selected {{
            background-color: {theme.get('HoverColor')};
            color: {theme.get('HighlightColor')};
        }}
        QMenu::separator {{
            height: 1px;
            background-color: {theme.get('BorderColor')};
            margin: 4px 5px;
        }}
        """
        return css

    def init_ui(self):
        # ... (init_ui code) ...
        self.create_main_toolbar()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.splitter = QSplitter(Qt.Horizontal)

        self.file_panel = self.create_file_panel()
        self.splitter.addWidget(self.file_panel)

        # Create a new splitter for the editor and dialogue map
        self.editor_splitter = QSplitter(Qt.Horizontal)

        self.editor_area = self.create_editor_area()
        self.editor_splitter.addWidget(self.editor_area)

        # Add dialogue map panel (restoring original functionality)
        from views.dialogue_map import DialogueMapPanel
        self.dialogue_map_panel = DialogueMapPanel(styles=self.STYLES)
        self.dialogue_map_panel.dialogue_clicked.connect(self.go_to_line)
        # Set reference to the main window for toggle functionality
        self.dialogue_map_panel.main_window = self
        self.editor_splitter.addWidget(self.dialogue_map_panel)

        # Set initial sizes (editor gets more space than dialogue map)
        self.editor_splitter.setSizes([700, 250])

        # Store the original sizes for toggle functionality
        self.dialogue_map_expanded_size = 250
        self.dialogue_map_collapsed = False

        self.splitter.addWidget(self.editor_splitter)

        self.splitter.setSizes([250, 700])

        main_layout.addWidget(self.splitter)

        self.create_status_bar()



    def create_main_toolbar(self):
        from views.toolbar import create_main_toolbar as _create_main_toolbar
        return _create_main_toolbar(self)



    def open_file_dialog(self):
        """Opens a dialog for selecting a single SNIL file."""
        initial_dir = self._last_open_dir if self._last_open_dir and os.path.isdir(self._last_open_dir) else os.path.expanduser("~")
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open SNIL File",
            initial_dir,
            "SNIL Files (*.snil);;All Files (*)"
        )

        if file_path:
            self._last_open_dir = os.path.dirname(file_path)
            # Load the single file directly
            self.load_file(file_path)

    def open_folder_dialog(self):
        """Opens a dialog for selecting a root folder."""
        initial_dir = self._last_open_dir if self._last_open_dir and os.path.isdir(self._last_open_dir) else os.path.expanduser("~")
        folder_path = QFileDialog.getExistingDirectory(self, "Select Root Folder", initial_dir)

        if folder_path:
            self._last_open_dir = folder_path
            self.root_path = folder_path # Store the root path
            self.reload_structure(folder_path)

    def open_project_dialog(self):
        """Opens a dialog for selecting a project folder and scans for dialog files."""
        initial_dir = self._last_open_dir if self._last_open_dir and os.path.isdir(self._last_open_dir) else os.path.expanduser("~")
        folder_path = QFileDialog.getExistingDirectory(self, "Select Project Folder", initial_dir)

        if folder_path:
            self._last_open_dir = folder_path
            self.root_path = folder_path # Store the root path

            # Scan for dialog files in the project
            self.scan_dialog_files(folder_path)

            # Start watching the dialogues directory for changes
            self.start_watching_dialogues(folder_path)

            self.reload_structure(folder_path)

    def scan_dialog_files(self, project_path: str):
        """Scan the project for dialog files and cache their names."""
        # Initialize dialog cache
        self.dialog_cache = []

        # Look for the dialogues folder in the expected location
        dialogues_path = os.path.join(project_path, "Assets", "SNEngine", "Source", "SNEngine", "Resources", "Dialogues")

        if os.path.exists(dialogues_path):
            # Scan for .snil and .asset files in the dialogues directory
            for root, dirs, files in os.walk(dialogues_path):
                for file in files:
                    if file.lower().endswith(('.snil', '.asset')):
                        file_path = os.path.join(root, file)
                        # Extract dialog names from the file
                        dialog_names = self.extract_dialog_names_from_file(file_path)
                        self.dialog_cache.extend(dialog_names)
        else:
            # If the specific path doesn't exist, scan the entire project for .snil and .asset files
            for root, dirs, files in os.walk(project_path):
                for file in files:
                    if file.lower().endswith(('.snil', '.asset')):
                        file_path = os.path.join(root, file)
                        # Extract dialog names from the file
                        dialog_names = self.extract_dialog_names_from_file(file_path)
                        self.dialog_cache.extend(dialog_names)

        # Remove duplicates while preserving order
        seen = set()
        unique_dialogs = []
        for dialog in self.dialog_cache:
            if dialog not in seen:
                seen.add(dialog)
                unique_dialogs.append(dialog)

        self.dialog_cache = unique_dialogs

        # Print the found dialog names for debugging
        print(f"Found {len(self.dialog_cache)} dialog names in project:")
        for i, dialog_name in enumerate(self.dialog_cache, 1):
            print(f"  {i}. {dialog_name}")

        # Also scan for characters
        self.scan_character_files(project_path)

    def scan_character_files(self, project_path: str):
        """Scan the project for character files and cache their names."""
        # Initialize character cache
        self.character_cache = []

        # Look for the characters folder in the expected location
        characters_path = os.path.join(project_path, "Assets", "SNEngine", "Source", "SNEngine", "Resources", "Characters")

        if os.path.exists(characters_path):
            # Scan for character files in the characters directory
            for root, dirs, files in os.walk(characters_path):
                for file in files:
                    if file.lower().endswith('.asset'):
                        file_path = os.path.join(root, file)
                        # Extract character name from the file content
                        char_name = self._extract_character_name_from_file(file_path)
                        if char_name and char_name not in self.character_cache:
                            self.character_cache.append(char_name)
        else:
            # If the specific path doesn't exist, scan the entire project for character-related files
            for root, dirs, files in os.walk(project_path):
                for file in files:
                    # Look for asset files that might contain character information
                    if file.lower().endswith('.asset'):
                        # Check if the file path contains "character" or similar
                        if 'character' in root.lower() or 'characters' in root.lower():
                            file_path = os.path.join(root, file)
                            # Extract character name from the file content
                            char_name = self._extract_character_name_from_file(file_path)
                            if char_name and char_name not in self.character_cache:
                                self.character_cache.append(char_name)

        # Print the found character names for debugging
        print(f"Found {len(self.character_cache)} character names in project:")
        for i, char_name in enumerate(self.character_cache, 1):
            print(f"  {i}. {char_name}")

    def _extract_character_name_from_file(self, file_path: str) -> str:
        """Extract character name from a Unity asset file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Look for the _name field in the asset file
            import re
            # Pattern to match '_name: <character_name>' (case-sensitive as it appears in Unity assets)
            pattern = r'^\s*_name:\s*(.+)$'

            for line in content.splitlines():
                match = re.match(pattern, line, re.MULTILINE)
                if match:
                    char_name = match.group(1).strip()
                    # Remove quotes if present
                    char_name = char_name.strip('"\'')
                    if char_name:
                        return char_name
        except Exception as e:
            print(f"Error reading character file {file_path}: {e}")

        return None


    def extract_dialog_names_from_file(self, file_path: str) -> list:
        """Extract dialog names from a SNIL or Unity asset file."""
        dialog_names = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            import re

            # Check if it's a Unity asset file (contains YAML Unity format)
            if "--- !u!" in content and "m_Name:" in content:
                # For Unity asset files, look for the main dialogue object
                # The main dialogue object typically has a specific script GUID and is the main asset object
                lines = content.splitlines()

                # Look for the main asset object (has &11400000 or similar reference)
                # The main dialogue object is the one that has the 'nodes:' field after m_Name
                for i, line in enumerate(lines):
                    if "--- !u!114 &" in line and "MonoBehaviour:" in lines[i+1] if i+1 < len(lines) else False:
                        # This looks like a MonoBehaviour object, look for m_Name and nodes: in the next few lines
                        m_name_line = -1
                        has_nodes_field = False
                        name_value = ""

                        for j in range(i+1, min(i+30, len(lines))):
                            if "m_Name:" in lines[j]:
                                match = re.search(r'm_Name:\s*(.+)', lines[j])
                                if match:
                                    name_value = match.group(1).strip()
                                    m_name_line = j
                            elif "nodes:" in lines[j]:
                                has_nodes_field = True
                                # This confirms it's the main dialogue object
                                break
                            # Stop if we encounter another object
                            elif "--- !u!" in lines[j] and j > i:
                                break

                        # If we found both m_Name and nodes field, this is the main dialogue object
                        if m_name_line != -1 and has_nodes_field:
                            # Remove quotes if present
                            dialog_name = name_value.strip('"\'')
                            # Only add if it's not an empty name
                            if dialog_name:
                                dialog_names.append(dialog_name)
                            break  # Only add the main dialogue name, not other objects
            else:
                # For SNIL files, look for 'name: <dialogue_name>' patterns
                # Pattern to match 'name: <dialogue_name>' (case-insensitive)
                pattern = r'^\s*name\s*:\s*(.+)$'

                for line_num, line in enumerate(content.splitlines(), 1):
                    match = re.match(pattern, line, re.IGNORECASE)
                    if match:
                        dialog_name = match.group(1).strip()
                        if dialog_name:  # Only add non-empty dialog names
                            dialog_names.append(dialog_name)
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")

        return dialog_names


    def reload_structure(self, folder_path: str):
        """Reloads file structure from the selected folder."""

        dirty_tab = next((t for t in self.open_tabs if t.is_dirty), None)

        if dirty_tab:
            reply = question_message_box(self, 'Unsaved Changes',
                f"Do you want to save changes to file '{os.path.basename(dirty_tab.file_path)}' before reloading the structure? Changes will be lost for other unsaved files.",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel, QMessageBox.Cancel)

            if reply == QMessageBox.Save:
                for tab in [t for t in self.open_tabs if t.is_dirty]:
                    self.save_file_action(tab)
            elif reply == QMessageBox.Cancel:
                return

        # Hide autocomplete popup if it's visible
        if hasattr(self, 'text_edit') and self.text_edit and hasattr(self.text_edit, 'autocomplete_popup'):
            if self.text_edit.autocomplete_popup and self.text_edit.autocomplete_popup.isVisible():
                self.text_edit.autocomplete_popup.hide_popup()
                self.text_edit.is_autocomplete_active = False

        # Clear open tabs (always when structure is reloaded)
        self.open_tabs.clear()
        self.current_tab_index = -1
        self.current_tab = None

        # Clear the text editor
        if hasattr(self, 'text_edit') and self.text_edit:
            self.text_edit.setPlainText("")
            if hasattr(self.text_edit, 'document'):
                self.text_edit.document().clearUndoRedoStacks()

        # Load the structure from the selected folder
        self.temp_structure = self.file_service.get_file_structure_from_path(folder_path)
        self.root_path = self.temp_structure.get('root_path')

        # --- VALIDATION CHECK ---
        if not self.validator.validate_structure(self.temp_structure):
            self.temp_structure = {'root_path': None, 'structure': {}}
            self.root_path = None
            self.draw_file_tree()
            self.draw_tabs_placeholder()
            self.update_status_bar()
            color = QColor(self.STYLES['DarkTheme']['NotificationError'])
            error_msg = self.validator.get_last_error()
            self.show_notification(f"Validation failed for {os.path.basename(folder_path)}: {error_msg}", color, duration_ms=5000)
            return

        # If valid
        if self.root_path and self.temp_structure.get('structure'):
            self.draw_file_tree()
            self.draw_tabs_placeholder()
            self.update_status_bar()
            color = QColor(self.STYLES['DarkTheme']['NotificationSuccess'])
            self.show_notification(f"Structure loaded and validated from: {os.path.basename(folder_path)}", color)
        else:
            self.draw_file_tree()
            self.draw_tabs_placeholder()
            color = QColor(self.STYLES['DarkTheme']['NotificationError'])
            self.show_notification("Failed to load structure. Folder not found or empty.", color)

    # --- Validation ---
    def validate_structure(self):
        from views.validation import validate_structure as _validate_struct
        return _validate_struct(self)

    # ... (Rest of File Panel: create_file_panel, clear_layout, draw_file_tree, foldout methods) ...
    def create_file_panel(self) -> QWidget:
        from views.file_panel import create_file_panel as _create_file_panel
        return _create_file_panel(self)

    def clear_layout(self, layout):
        from views.file_panel import clear_layout as _clear_layout
        return _clear_layout(self, layout)

    def draw_file_tree(self):
        from views.file_panel import draw_file_tree as _draw_file_tree
        return _draw_file_tree(self)

    def get_or_set_foldout(self, path: str, default: bool = False) -> bool:
        from views.file_panel import get_or_set_foldout as _get_or_set_foldout
        return _get_or_set_foldout(self, path, default)

    def set_foldout(self, path: str, state: bool):
        from views.file_panel import set_foldout as _set_foldout
        return _set_foldout(self, path, state)

    def check_folder_for_match_recursive(self, folder_path_normalized: str) -> bool:
        from views.file_panel import check_folder_for_match_recursive as _check
        return _check(self, folder_path_normalized)

    def draw_folder_content(self, folder_path: str, structure: dict, level: int):
        from views.file_panel import draw_folder_content as _draw_folder_content
        return _draw_folder_content(self, folder_path, structure, level)


    def _add_file_button(self, name: str, path: str, level: int):
        from views.file_panel import _add_file_button as _add_btn
        return _add_btn(self, name, path, level)

    def load_file(self, file_path: str):
        from views.file_ops import load_file as _load
        return _load(self, file_path)

    def try_switch_file_action(self, new_file_path: str):
        from views.file_ops import try_switch_file_action as _try_switch
        return _try_switch(self, new_file_path)


    def create_editor_area(self) -> QWidget:
        from views.editor import create_editor_area as _create_editor_area
        return _create_editor_area(self)

    def create_editor_toolbar(self):
        from views.editor import create_editor_toolbar as _create_editor_toolbar
        return _create_editor_toolbar(self)


    def create_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("Ready.")
        self.status_bar.addWidget(self.status_label)


        # Add font size label to status bar
        # Use settings manager value if available, otherwise default
        initial_font_size = 14
        if hasattr(self, 'settings_manager') and self.settings_manager:
            initial_font_size = self.settings_manager.font_size
        self.font_size_label = QLabel(f"Font Size: {initial_font_size} (Ctrl+↑/↓)")
        self.status_bar.addPermanentWidget(self.font_size_label)

        self._notification_label = QLabel()
        self._notification_label.setVisible(False)
        self.status_bar.addPermanentWidget(self._notification_label)

    def show_notification(self, message: str, color: QColor, duration_ms: int = 3000):
        from views.notifications import show_notification as _show
        return _show(self, message, color, duration_ms)

    def hide_notification(self):
        from views.notifications import hide_notification as _hide
        return _hide(self)


    def draw_tabs_placeholder(self):
        from views.tabs import draw_tabs_placeholder as _draw_tabs
        return _draw_tabs(self)


    def switch_tab_action(self, index):
        from views.tabs import switch_tab_action as _switch
        return _switch(self, index)

    def handle_text_change(self):
        from views.tabs import handle_text_change as _handle
        _handle(self)

        # Update dialogue map when text changes
        if hasattr(self, 'dialogue_map_panel') and self.dialogue_map_panel:
            current_text = self.text_edit.toPlainText() if hasattr(self, 'text_edit') and self.text_edit else ""
            self.dialogue_map_panel.update_dialogue_map(current_text)

        # Update script graph window if it's open
        if hasattr(self, 'script_graph_window') and self.script_graph_window:
            current_text = self.text_edit.toPlainText() if hasattr(self, 'text_edit') and self.text_edit else ""
            self.script_graph_window.parse_script_content(current_text)

    def go_to_line(self, line_number: int):
        """Navigate the editor to the specified line number"""
        if hasattr(self, 'text_edit') and self.text_edit:
            # Debug: print the line number being passed
            print(f"Attempting to go to line: {line_number}")

            # Make sure line_number is valid
            if line_number < 1:
                print("Invalid line number")
                return

            # Get document and block count
            doc = self.text_edit.document()
            block_count = doc.blockCount()
            print(f"Document has {block_count} blocks, trying to go to line {line_number}")

            if line_number > block_count:
                print(f"Line number {line_number} exceeds block count {block_count}")
                return

            # Get the block for the target line (0-based index)
            block = doc.findBlockByNumber(line_number - 1)  # 0-based index

            if block.isValid():
                # Create cursor and position it at the block
                cursor = self.text_edit.textCursor()
                cursor.setPosition(block.position())  # Position at the start of the block

                # Set the cursor position and ensure the line is visible
                self.text_edit.setTextCursor(cursor)
                self.text_edit.ensureCursorVisible()

                # Scroll to make sure the line is centered if possible
                self.text_edit.centerCursor()

                print(f"Successfully moved to line {line_number}")
            else:
                print(f"Block for line {line_number} is not valid")

    def toggle_dialogue_map(self):
        """Toggle the visibility of the dialogue map panel"""
        if not hasattr(self, 'dialogue_map_panel') or not self.dialogue_map_panel:
            return

        # Get current sizes of the editor splitter
        current_sizes = self.editor_splitter.sizes()
        total_size = sum(current_sizes)

        if self.dialogue_map_collapsed:
            # Expand the dialogue map
            editor_size = total_size - self.dialogue_map_expanded_size
            self.editor_splitter.setSizes([editor_size, self.dialogue_map_expanded_size])

            # Show the scroll area and update the toggle button text
            self.dialogue_map_panel.scroll_area.show()
            self.dialogue_map_panel.toggle_button.setText("◀")
            self.dialogue_map_panel.title_label.setText("Dialogue Map")

            self.dialogue_map_collapsed = False
        else:
            # Collapse the dialogue map - hide the scroll area but keep the toggle button accessible
            # Store current editor size for restoration
            editor_size = current_sizes[0]
            self.dialogue_map_expanded_size = current_sizes[1]  # Store current dialogue map size

            # Hide the scroll area completely to prevent content from showing
            self.dialogue_map_panel.scroll_area.hide()

            # Set dialogue map to minimal visible size so the toggle button remains accessible
            # This will make it very narrow but the toggle button will still be clickable
            self.editor_splitter.setSizes([editor_size + self.dialogue_map_expanded_size - 30, 30])

            # Update the toggle button text
            self.dialogue_map_panel.toggle_button.setText("▶")
            self.dialogue_map_panel.title_label.setText("")  # Hide title when collapsed

            self.dialogue_map_collapsed = True

    def split_current_file(self):
        """Split the current file into separate dialogue files based on '---' separators"""
        from views.file_splitter import split_current_file_with_dialog
        split_current_file_with_dialog(self)

    def show_script_graph(self):
        """Show the script graph visualization window"""
        # Check if the script graph window is already created
        if hasattr(self, 'script_graph_window') and self.script_graph_window:
            # Check if the window is hidden (closed but not destroyed)
            if not self.script_graph_window.isVisible():
                # Window was hidden, just show it again with updated content
                current_text = self.text_edit.toPlainText() if hasattr(self, 'text_edit') and self.text_edit else ""
                self.script_graph_window.parse_script_content(current_text)
                self.script_graph_window.show()
            # Bring existing window to front
            self.script_graph_window.raise_()
            self.script_graph_window.activateWindow()
        else:
            # Create new window
            from views.graph.script_graph import ScriptGraphWindow
            self.script_graph_window = ScriptGraphWindow(self)

            # Parse current content and show in the window
            current_text = self.text_edit.toPlainText() if hasattr(self, 'text_edit') and self.text_edit else ""
            self.script_graph_window.parse_script_content(current_text)

            # Show the window
            self.script_graph_window.show()


    def try_close_tab(self, index: int):
        """
        Handles request to close a tab by index,
        checking for unsaved changes and updating QTextEdit content.

        FIX: Ensures that after tab deletion, the input field
        is updated with the content of the new active tab or cleared.
        """

        from views.tabs import try_close_tab as _try_close
        return _try_close(self, index)

    def update_status_bar(self):
        # ... (update_status_bar code) ...
        status = "Ready."
        if self.current_tab and self.current_tab.is_dirty:
            status = f"Unsaved changes in {os.path.basename(self.current_tab.file_path)}*"
        self.status_label.setText(status)

    def update_undo_redo_ui(self):
        from views.tabs import update_undo_redo_ui as _update
        return _update(self)


    def save_file_action(self, tab_to_save):
        from views.file_ops import save_file_action as _save
        return _save(self, tab_to_save)

    def reload_file_action(self):
        from views.file_ops import reload_file_action as _reload
        return _reload(self)


    def reload_structure_action(self):
        if self.root_path:
            self.reload_structure(self.root_path)
        else:
            color = QColor(self.STYLES['DarkTheme']['NotificationWarning'])
            self.show_notification("No folder open to reload.", color)

    def new_file_action(self):
        """Create a new file. If in directory mode, save to the current directory. If in single file mode, prompt for location."""
        import os
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        from models import SNILTab

        # Check if we're in directory mode (root_path is set) or single file mode
        if self.root_path and os.path.isdir(self.root_path):
            # We're in directory mode, create file in the root directory
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Create New SNIL File",
                self.root_path,  # Start in the current root directory
                "SNIL Files (*.snil);;All Files (*)"
            )

            if file_path:
                # If the file doesn't end with .snil, add it
                if not file_path.lower().endswith('.snil'):
                    file_path += '.snil'

                # Create the new file with empty content if it doesn't exist
                if not os.path.exists(file_path):
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write("")

                # Load the new file into a tab
                self.load_file(file_path)

                color = QColor(self.STYLES['DarkTheme']['NotificationSuccess'])
                self.show_notification(f"New file created: {os.path.basename(file_path)}", color)
        else:
            # We're in single file mode or no directory is open
            # Prompt user for location to save the new file
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Create New SNIL File",
                self._last_open_dir if self._last_open_dir and os.path.isdir(self._last_open_dir) else os.path.expanduser("~"),
                "SNIL Files (*.snil);;All Files (*)"
            )

            if file_path:
                # If the file doesn't end with .snil, add it
                if not file_path.lower().endswith('.snil'):
                    file_path += '.snil'

                # Create the new file with empty content if it doesn't exist
                if not os.path.exists(file_path):
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write("")

                # Load the new file into a tab
                self.load_file(file_path)

                # Update the last open directory for future use
                self._last_open_dir = os.path.dirname(file_path)

                color = QColor(self.STYLES['DarkTheme']['NotificationSuccess'])
                self.show_notification(f"New file created: {os.path.basename(file_path)}", color)

    def handle_undo(self):
        from views.shortcuts import handle_undo as _undo
        return _undo(self)

    def handle_redo(self):
        from views.shortcuts import handle_redo as _redo
        return _redo(self)


    def keyPressEvent(self, event):
        from views.shortcuts import keyPressEvent as _key
        return _key(self, event)


    def open_styles_editor(self):
        """Открывает редактор стилей"""
        from views.styles_editor import StylesEditorDialog

        def on_styles_changed(styles):
            # Delegate to helper so tests can call it directly
            self._apply_style_update(styles)

        dialog = StylesEditorDialog(self, self._get_resource_path('styles.yaml'))
        dialog.styles_changed.connect(on_styles_changed)
        dialog.exec_()


    def open_settings_dialog(self):
        """Opens the editor settings dialog"""
        from settings_dialog import SettingsDialog

        def on_settings_changed(settings):
            # Update settings in the main window
            # Check if the line numbers option changed
            if 'show_line_numbers' in settings:
                # Can update line numbers display in the future
                pass

            # Check if font settings changed
            if 'font_family' in settings or 'font_size' in settings:
                # Update the font in the current text editor if it exists
                if hasattr(self, 'text_edit') and self.text_edit:
                    try:
                        # Update font from settings
                        self.text_edit.update_font_from_settings()
                    except Exception as e:
                        print(f"Error updating font from settings: {e}")

                # Update font size label in status bar if font size changed
                if 'font_size' in settings:
                    if hasattr(self, 'font_size_label') and self.font_size_label:
                        self.font_size_label.setText(f"Font Size: {self.settings_manager.font_size} (Ctrl+↑/↓)")

            # Check if auto-save settings changed
            if 'auto_save_enabled' in settings or 'auto_save_interval' in settings:
                # Reconfigure the auto-save timer
                self._setup_auto_save_timer()

            # Check if line numbers setting changed
            if 'show_line_numbers' in settings:
                # Update the visibility of line numbers in the current text editor if it exists
                if hasattr(self, 'text_edit') and self.text_edit:
                    try:
                        # Update line numbers visibility from settings
                        self.text_edit.update_line_numbers_visibility()
                    except Exception as e:
                        print(f"Error updating line numbers visibility from settings: {e}")

            # Check if highlight current line setting changed
            if 'highlight_current_line' in settings:
                # Update the current line highlighting in the text editor if it exists
                if hasattr(self, 'text_edit') and self.text_edit:
                    try:
                        # Call the method to update the highlighting setting
                        self.text_edit.update_highlight_current_line_setting()
                    except Exception as e:
                        print(f"Error updating line highlighting from settings: {e}")

        dialog = SettingsDialog(self.settings_manager, self)
        dialog.settings_changed.connect(on_settings_changed)
        dialog.exec_()

    def _apply_style_update(self, styles):
        """Apply a partial styles dict by merging with existing theme and updating UI elements."""
        if 'DarkTheme' not in self.STYLES:
            self.STYLES = {'DarkTheme': {}}
        # Merge keys
        self.STYLES['DarkTheme'].update(styles)

        # Regenerate CSS and apply
        self.CSS_STYLES = self._generate_css(self.STYLES)
        self.setStyleSheet(self.CSS_STYLES)

        # Update icons/colors
        folder_icon_color = self.STYLES['DarkTheme'].get('FolderIconColor', '#E06C75')
        yaml_icon_color = self.STYLES['DarkTheme'].get('YamlFileIconColor', '#CCCCCC')

        folder_svg_content = self._load_folder_icon()
        yaml_svg_content = self._load_yaml_file_icon()
        android_svg_content = self._load_android_icon()

        folder_svg_content = self._update_svg_colors(folder_svg_content, folder_color=folder_icon_color)
        yaml_svg_content = self._update_svg_colors(yaml_svg_content, yaml_color=yaml_icon_color)

        self.icon_folder = self._create_icon_from_svg_content(folder_svg_content)
        self.icon_yaml = self._create_icon_from_svg_content(yaml_svg_content)
        self.icon_android = self._create_icon_from_svg_content(android_svg_content, is_folder=False, is_yaml=False)

        # Update syntax highlighter colors (pass the merged DarkTheme dict)
        highlighter_colors = {
            'directive_color': self.STYLES['DarkTheme'].get('SyntaxKeyColor', '#E06C75'),
            'dialogue_color': self.STYLES['DarkTheme'].get('SyntaxStringColor', '#ABB2BF'),
            'comment_color': self.STYLES['DarkTheme'].get('SyntaxCommentColor', '#608B4E'),
            'keyword_color': self.STYLES['DarkTheme'].get('SyntaxKeywordColor', '#FFB86C'),
            'function_color': self.STYLES['DarkTheme'].get('SyntaxFunctionColor', '#56B6C2'),
            'parameter_color': self.STYLES['DarkTheme'].get('SyntaxParameterColor', '#FFD700'),
            'default_color': self.STYLES['DarkTheme'].get('SyntaxDefaultColor', '#FFFFFF')
        }

        if hasattr(self, 'text_edit') and self.text_edit:
            if hasattr(self, 'highlighter') and self.highlighter:
                self.highlighter.update_colors(highlighter_colors)
                # Force re-highlighting of the entire document to apply new colors
                doc = self.text_edit.document()
                self.highlighter.setDocument(None)
                self.highlighter.setDocument(doc)

        # Обновить также цвета для нумерации строк
        if hasattr(self, 'text_edit') and self.text_edit:
            self.text_edit.styles = {'DarkTheme': self.STYLES['DarkTheme']}
            # Обновить стили панели нумерации строк
            if hasattr(self.text_edit, 'update_line_number_styles'):
                self.text_edit.update_line_number_styles()
            # Перерисовать панель нумерации строк
            self.text_edit.line_numbers.update()

        # Update dialogue map styles if it exists
        if hasattr(self, 'dialogue_map_panel') and self.dialogue_map_panel:
            self.dialogue_map_panel.update_styles({'DarkTheme': self.STYLES['DarkTheme']})

    def update_highlighter_colors(self, styles):
        """Update syntax highlighter colors in the current editor and all open tabs"""
        # Обновляем подсветку синтаксиса, если редактор существует
        if hasattr(self, 'text_edit') and self.text_edit:
            if hasattr(self, 'highlighter') and self.highlighter:
                # Обновляем цвета подсветчика с использованием стилей из темы
                highlighter_colors = {
                    'directive_color': styles.get('SyntaxKeyColor', '#E06C75'),
                    'dialogue_color': styles.get('SyntaxStringColor', '#ABB2BF'),
                    'comment_color': styles.get('SyntaxCommentColor', '#608B4E'),
                    'keyword_color': styles.get('SyntaxKeywordColor', '#FFB86C'),
                    'function_color': styles.get('SyntaxFunctionColor', '#56B6C2'),
                    'parameter_color': styles.get('SyntaxParameterColor', '#FFD700'),
                    'default_color': styles.get('SyntaxDefaultColor', '#FFFFFF')
                }
                self.highlighter.update_colors(highlighter_colors)

                # Force re-highlighting of the entire document to apply new colors
                doc = self.text_edit.document()
                self.highlighter.setDocument(None)
                self.highlighter.setDocument(doc)

        # Обновить также цвета для нумерации строк
        if hasattr(self, 'text_edit') and self.text_edit:
            self.text_edit.styles = {'DarkTheme': styles}
            # Обновить стили панели нумерации строк
            if hasattr(self.text_edit, 'update_line_number_styles'):
                self.text_edit.update_line_number_styles()
            # Перерисовать панель нумерации строк
            self.text_edit.line_numbers.update()

        # Update dialogue map styles if it exists
        if hasattr(self, 'dialogue_map_panel') and self.dialogue_map_panel:
            self.dialogue_map_panel.update_styles({'DarkTheme': styles})
    def change_font_size(self, change):
        from views.shortcuts import change_font_size as _resize
        return _resize(self, change)

    def show_text_edit_context_menu(self, pos):
        menu = QMenu(self)

        # Add animation
        effect = QGraphicsOpacityEffect(menu)
        effect.setOpacity(0)
        menu.setGraphicsEffect(effect)

        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(150)  # milliseconds
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.InQuad)
        animation.start(QPropertyAnimation.DeleteWhenStopped)

        cut_action = QAction("Cut", self)
        cut_action.triggered.connect(self.text_edit.cut)
        menu.addAction(cut_action)

        copy_action = QAction("Copy", self)
        copy_action.triggered.connect(self.text_edit.copy)
        menu.addAction(copy_action)

        paste_action = QAction("Paste", self)
        paste_action.triggered.connect(self.text_edit.paste)
        menu.addAction(paste_action)

        menu.addSeparator()

        select_all_action = QAction("Select All", self)
        select_all_action.triggered.connect(self.text_edit.selectAll)
        menu.addAction(select_all_action)

        menu.exec_(self.text_edit.mapToGlobal(pos))

    def start_watching_dialogues(self, project_path: str):
        """Start watching the dialogues and characters directories for file changes."""
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler

            # Define the event handler
            class DialogueFileHandler(FileSystemEventHandler):
                def __init__(self, parent):
                    super().__init__()
                    self.parent = parent

                def on_modified(self, event):
                    if not event.is_directory and self._is_dialogue_or_character_file(event.src_path):
                        print(f"Dialogue/Character file modified: {event.src_path}")
                        # Emit signal to trigger rescan in the GUI thread
                        self.parent.rescan_signal_obj.rescan_signal.emit()

                def on_created(self, event):
                    if not event.is_directory and self._is_dialogue_or_character_file(event.src_path):
                        print(f"Dialogue/Character file created: {event.src_path}")
                        # Emit signal to trigger rescan in the GUI thread
                        self.parent.rescan_signal_obj.rescan_signal.emit()

                def on_deleted(self, event):
                    if not event.is_directory and self._is_dialogue_or_character_file(event.src_path):
                        print(f"Dialogue/Character file deleted: {event.src_path}")
                        # Emit signal to trigger rescan in the GUI thread
                        self.parent.rescan_signal_obj.rescan_signal.emit()

                def on_moved(self, event):
                    # Check if the moved file is a dialogue or character file
                    if self._is_dialogue_or_character_file(event.src_path) or self._is_dialogue_or_character_file(event.dest_path):
                        print(f"Dialogue/Character file moved: {event.src_path} -> {event.dest_path}")
                        # Emit signal to trigger rescan in the GUI thread
                        self.parent.rescan_signal_obj.rescan_signal.emit()

                def _is_dialogue_or_character_file(self, file_path):
                    """Check if the file is a dialogue or character file (.snil or .asset)"""
                    return file_path.lower().endswith(('.snil', '.asset'))

            # Stop any existing watcher
            self.stop_watching_dialogues()

            # Look for the dialogues folder in the expected location
            dialogues_path = os.path.join(project_path, "Assets", "SNEngine", "Source", "SNEngine", "Resources", "Dialogues")
            characters_path = os.path.join(project_path, "Assets", "SNEngine", "Source", "SNEngine", "Resources", "Characters")

            # Create and start the observer
            self.dialogue_watcher = Observer()
            event_handler = DialogueFileHandler(self)

            # Watch both dialogues and characters directories
            if os.path.exists(dialogues_path):
                self.dialogue_watcher.schedule(event_handler, dialogues_path, recursive=True)
                print(f"Started watching dialogues directory: {dialogues_path}")

            if os.path.exists(characters_path):
                self.dialogue_watcher.schedule(event_handler, characters_path, recursive=True)
                print(f"Started watching characters directory: {characters_path}")

            # If neither specific path exists, watch the entire project for .snil and .asset files
            if not os.path.exists(dialogues_path) and not os.path.exists(characters_path):
                self.dialogue_watcher.schedule(event_handler, project_path, recursive=True)
                print(f"Started watching project directory for dialogue/character files: {project_path}")

            self.dialogue_watcher.start()
            # Store both paths for stopping
            self.dialogue_watch_path = [dialogues_path, characters_path] if os.path.exists(dialogues_path) or os.path.exists(characters_path) else project_path

        except ImportError:
            print("watchdog library not available. File system watching disabled.")
            print("To enable file watching, install watchdog: pip install watchdog")
        except Exception as e:
            print(f"Error starting dialogue/character file watcher: {e}")

    def stop_watching_dialogues(self):
        """Stop watching the dialogues directory."""
        if self.dialogue_watcher:
            try:
                self.dialogue_watcher.stop()
                self.dialogue_watcher.join()
                if isinstance(self.dialogue_watch_path, list):
                    for path in self.dialogue_watch_path:
                        if os.path.exists(path):
                            print(f"Stopped watching directory: {path}")
                else:
                    print(f"Stopped watching directory: {self.dialogue_watch_path}")
            except Exception as e:
                print(f"Error stopping dialogue file watcher: {e}")
            finally:
                self.dialogue_watcher = None
                self.dialogue_watch_path = None

    def _schedule_rescan(self):
        """Schedule a rescan to avoid multiple rapid scans."""
        # Restart the timer to delay the rescan by 500ms
        self.rescan_timer.stop()
        self.rescan_timer.start(500)

    def _load_snil_syntax_commands(self):
        """Load SNIL syntax commands from snil_syntax.json."""
        import json
        import os

        commands = []
        try:
            syntax_file_path = os.path.join(os.path.dirname(__file__), 'snil_syntax.json')
            if os.path.exists(syntax_file_path):
                with open(syntax_file_path, 'r', encoding='utf-8') as f:
                    syntax_data = json.load(f)

                # Extract command names from the syntax data
                for key, value in syntax_data.items():
                    # Add the command text (value) to the commands list
                    commands.append(value)
        except Exception as e:
            print(f"Error loading SNIL syntax commands: {e}")

        return commands

    def rescan_dialogues(self):
        """Rescan dialogue files and update cache."""
        if self.root_path:
            print("Rescanning dialogue files...")
            self.scan_dialog_files(self.root_path)
            print("Dialogue files rescanned and cache updated.")