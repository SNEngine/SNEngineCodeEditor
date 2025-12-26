from PyQt5.QtWidgets import QToolBar, QLabel, QAction, QWidget, QSizePolicy, QComboBox
from PyQt5.QtCore import Qt, QSize


def create_main_toolbar(self):
    """Create the main toolbar (moved out from view.py)."""
    main_toolbar = QToolBar("Main Toolbar")
    main_toolbar.setIconSize(QSize(18, 18))
    self.addToolBar(Qt.TopToolBarArea, main_toolbar)

    main_toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

    # --- OPEN FILE BUTTON ---
    open_file_action = QAction(self.icon_folder, "Open File...", self)
    open_file_action.triggered.connect(self.open_file_dialog)
    main_toolbar.addAction(open_file_action)

    # --- OPEN FOLDER BUTTON ---
    open_folder_action = QAction(self.icon_folder, "Open Folder...", self)
    open_folder_action.triggered.connect(self.open_folder_dialog)
    main_toolbar.addAction(open_folder_action)

    # New File Button
    new_file_action = QAction(self.icon_yaml, "New File", self)
    new_file_action.triggered.connect(self.new_file_action)
    main_toolbar.addAction(new_file_action)

    main_toolbar.addSeparator()

    # Reload Structure
    reload_action = QAction("Reload Structure", self)
    reload_action.triggered.connect(self.reload_structure_action)
    main_toolbar.addAction(reload_action)

    main_toolbar.addSeparator()

    # Removed: Flag + label for language selection
    # self.flag_label = QLabel()
    # self.flag_label.setFixedSize(24, 16)
    # self.flag_label.setScaledContents(True)
    # main_toolbar.addWidget(self.flag_label)

    # self.language_label = QLabel("Language: N/A") # Removed
    # main_toolbar.addWidget(self.language_label) # Removed

    # Placeholder for Font Size (Removed)
    # self.font_size_label = QLabel(f"Font Size: {self._current_font_size} (Ctrl+↑/↓)")
    # main_toolbar.addWidget(self.font_size_label)

    # Flexible space
    main_toolbar.addSeparator()
    spacer = QWidget()
    spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    main_toolbar.addWidget(spacer)

    # Styles Editor Button
    styles_action = QAction("Styles Editor", self)
    styles_action.triggered.connect(self.open_styles_editor)
    main_toolbar.addAction(styles_action)


    # Settings Button
    settings_action = QAction("Settings", self)
    settings_action.triggered.connect(self.open_settings_dialog)
    main_toolbar.addAction(settings_action)

    # Split File Button
    split_action = QAction("Split File", self)
    split_action.triggered.connect(lambda: self.split_current_file())
    main_toolbar.addAction(split_action)

    # Script Graph Button
    graph_action = QAction("Script Graph", self)
    graph_action.triggered.connect(lambda: self.show_script_graph())
    main_toolbar.addAction(graph_action)

    return main_toolbar
