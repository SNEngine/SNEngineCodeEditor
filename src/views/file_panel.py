import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QScrollArea, QLabel, QSizePolicy
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QColor


def create_file_panel(self) -> QWidget:
    panel = QWidget()
    panel.setObjectName("FilePanelWidget") # For applying CSS style
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(5, 5, 5, 5)

    search_bar = QWidget()
    search_layout = QHBoxLayout(search_bar)
    search_layout.setContentsMargins(0, 0, 0, 0)
    self.search_input = QLineEdit()
    self.search_input.setPlaceholderText("Search files...")
    self.search_input.setStyleSheet(f"background-color: {self.STYLES['DarkTheme']['HoverColor']}; color: white; border-radius: 5px;")
    self.search_input.textChanged.connect(self.draw_file_tree)
    search_layout.addWidget(self.search_input)
    
    clear_search_btn = QPushButton("x")
    clear_search_btn.setFixedSize(20, 20)
    clear_search_btn.setStyleSheet("font-weight: bold; padding: 0;")
    clear_search_btn.clicked.connect(lambda: self.search_input.setText(""))
    search_layout.addWidget(clear_search_btn)
    
    layout.addWidget(search_bar)

    self.file_tree_content = QWidget()
    self.file_tree_layout = QVBoxLayout(self.file_tree_content)
    self.file_tree_layout.setContentsMargins(0, 0, 0, 0)
    self.file_tree_layout.setSpacing(1)
    self.file_tree_content.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

    self.file_scroll_area = QScrollArea()
    self.file_scroll_area.setWidgetResizable(True)
    self.file_scroll_area.setWidget(self.file_tree_content)
    
    layout.addWidget(self.file_scroll_area, 1)
    
    self.draw_file_tree()
    
    return panel


def clear_layout(self, layout):
    if layout is not None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                self.clear_layout(item.layout())


def draw_file_tree(self):
    self.clear_layout(self.file_tree_layout)

    root_to_display = self.root_path

    structure = self.temp_structure.get('structure', {})

    if not root_to_display or not structure or not os.path.isdir(root_to_display):
        placeholder = QLabel("Select folder via 'Open Folder...'")
        placeholder.setAlignment(Qt.AlignCenter)
        self.file_tree_layout.addWidget(placeholder)
        self.file_tree_layout.addStretch(1)
        return

    self.draw_folder_content(root_to_display, structure, 0)
    self.file_tree_layout.addStretch(1)


def get_or_set_foldout(self, path: str, default: bool = False) -> bool:
    normalized = self.file_service.normalize_path(path)
    if normalized not in self._foldouts:
        self._foldouts[normalized] = default
    return self._foldouts[normalized]


def set_foldout(self, path: str, state: bool):
    normalized = self.file_service.normalize_path(path)
    self._foldouts[normalized] = state
    self.draw_file_tree()


def check_folder_for_match_recursive(self, folder_path_normalized: str) -> bool:
    query = self.search_input.text().lower()
    if not query: return True
    if folder_path_normalized not in self.temp_structure['structure']: return False

    if any(f.lower().startswith(query) for f in self.temp_structure['structure'][folder_path_normalized]):
        return True

    path_prefix = folder_path_normalized + os.sep
    sub_folders = [k for k in self.temp_structure['structure'].keys()
                   if k.startswith(path_prefix) and
                   self.file_service.normalize_path(os.path.dirname(k)) == folder_path_normalized]

    for sub_folder_path in sorted(sub_folders):
        if self.check_folder_for_match_recursive(sub_folder_path):
            return True

    return False


def draw_folder_content(self, folder_path: str, structure: dict, level: int):
    normalized_path = self.file_service.normalize_path(folder_path)

    if normalized_path not in structure:
        return

    is_searching = bool(self.search_input.text())
    folder_matches = self.check_folder_for_match_recursive(normalized_path)

    if is_searching and not folder_matches:
        return

    folder_name = os.path.basename(folder_path)
    should_be_open = True

    should_be_open = self.get_or_set_foldout(normalized_path)


    # 1. Draw current folder/toggle button
    folder_color = self.STYLES['DarkTheme']['FolderColor']

    icon_char = '▼' if should_be_open and not (is_searching and folder_matches) else '►'

    folder_button = QPushButton(f" {icon_char} {folder_name}")
    folder_button.setFlat(True)
    folder_button.setIcon(self.icon_folder)
    folder_button.setIconSize(QSize(16, 16))  # Ensure icon size is set

    # Style for folder
    folder_button.setStyleSheet(f"""
        QPushButton {{
            text-align: left;
            border: none;
            padding: 2px 0;
            padding-left: {(level) * 15}px;
            color: {folder_color};
        }}
        QPushButton:hover {{
            background-color: {self.STYLES['DarkTheme']['FilePanelHover']};
        }}
    """)

    if not is_searching or not folder_matches:
        folder_button.clicked.connect(lambda _, path=normalized_path, state=should_be_open: self.set_foldout(path, not state))

    self.file_tree_layout.addWidget(folder_button)

    # 2. Draw files and recursive call if should_be_open
    if should_be_open or is_searching:
        files = sorted(structure.get(normalized_path, []))

        query = self.search_input.text().lower()
        filtered_files = [f for f in files if not is_searching or f.lower().startswith(query)]

        for file in filtered_files:
            full_path = os.path.join(folder_path, file)
            self._add_file_button(file, full_path, level)

        path_prefix = normalized_path + os.sep
        sub_folders = [k for k in structure.keys()
                       if k.startswith(path_prefix) and
                       self.file_service.normalize_path(os.path.dirname(k)) == normalized_path]

        for sub_folder_path in sorted(sub_folders):
            self.draw_folder_content(sub_folder_path, structure, level + 1)


def _add_file_button(self, name: str, path: str, level: int):
    normalized_path = self.file_service.normalize_path(path)
    is_selected = self.current_tab and self.file_service.normalize_path(self.current_tab.file_path) == normalized_path

    display_name = name

    open_tab = next((t for t in self.open_tabs if self.file_service.normalize_path(t.file_path) == normalized_path), None)
    if (open_tab and open_tab.is_dirty and not is_selected) or (is_selected and self.current_tab.is_dirty):
        display_name += "*"

    file_button = QPushButton(display_name)

    if name.lower().endswith(".snil"):
        file_button.setIcon(self.icon_yaml)  # Use the same icon for SNIL files
        file_button.setIconSize(QSize(16, 16))  # Ensure icon size is set

    highlight_color = self.STYLES['DarkTheme']['HighlightColor']
    hover_color = self.STYLES['DarkTheme']['FilePanelHover']

    base_style = f"text-align: left; border: none; padding: 2px 0; padding-left: {(level + 1) * 15}px;"

    if is_selected:
        style = f"""
            QPushButton {{
                {base_style}
                background-color: {highlight_color};
                color: white;
            }}
        """
    else:
        style = f"""
            QPushButton {{
                {base_style}
                color: {self.STYLES['DarkTheme']['Foreground']};
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
        """

    file_button.setStyleSheet(style)
    file_button.clicked.connect(lambda: self.try_switch_file_action(path))
    self.file_tree_layout.addWidget(file_button)
