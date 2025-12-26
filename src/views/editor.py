from PyQt5.QtWidgets import QWidget, QVBoxLayout, QToolBar, QLabel, QSizePolicy, QAction, QMenu
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from views.search import create_search_widget
from .code_editor import CodeEditor


def create_editor_area(self) -> QWidget:
    area = QWidget()
    layout = QVBoxLayout(area)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    
    self.tab_placeholder = QToolBar("TabPlaceholder")
    self.tab_placeholder.setFixedHeight(30)
    self.draw_tabs_placeholder()
    layout.addWidget(self.tab_placeholder)

    editor_widget = QWidget()
    editor_layout = QVBoxLayout(editor_widget)
    editor_layout.setContentsMargins(5, 5, 5, 5)
    editor_layout.setSpacing(5)

    self.editor_toolbar = QToolBar("Editor Toolbar")
    self.editor_toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
    self.create_editor_toolbar()
    editor_layout.addWidget(self.editor_toolbar)

    # search widget (hidden by default)
    try:
        self.editor_search_widget = create_search_widget(self)
        editor_layout.addWidget(self.editor_search_widget)
    except Exception:
        # if search module unavailable, continue without it
        pass

    self.text_edit = CodeEditor(styles=self.STYLES, settings_manager=self.settings_manager)
    # Update font from settings manager instead of using theme font
    self.text_edit.update_font_from_settings()
    # Update line numbers visibility from settings
    self.text_edit.update_line_numbers_visibility()
    self.text_edit.setPlainText(self.current_tab.snil_text if self.current_tab else "")
    self.text_edit.textChanged.connect(self.handle_text_change)
    
    self.highlighter = None
    try:
        from snil_highlighter import SNILHighlighter
        # Подготовим цвета для подсветчика на основе текущей темы
        highlighter_colors = {
            'directive_color': self.STYLES['DarkTheme'].get('SyntaxKeyColor', '#E06C75'),
            'dialogue_color': self.STYLES['DarkTheme'].get('SyntaxStringColor', '#ABB2BF'),
            'comment_color': self.STYLES['DarkTheme'].get('SyntaxCommentColor', '#608B4E'),
            'keyword_color': self.STYLES['DarkTheme'].get('SyntaxKeywordColor', '#AF55C4'),
            'function_color': self.STYLES['DarkTheme'].get('SyntaxFunctionColor', '#56B6C2'),
            'parameter_color': self.STYLES['DarkTheme'].get('SyntaxParameterColor', '#FFD700'),
            'default_color': self.STYLES['DarkTheme'].get('SyntaxDefaultColor', '#CCCCCC')
        }
        self.highlighter = SNILHighlighter(self.text_edit.document(), highlighter_colors)
        # Устанавливаем атрибут подсветчика в основном окне, чтобы к нему можно было получить доступ извне
        if hasattr(self, 'text_edit'):
            self.text_edit.document().highlighter = self.highlighter
    except Exception as e:
        print(f"Error creating highlighter: {e}")
        pass
    
    editor_layout.addWidget(self.text_edit)

    # Apply modern thin rounded scrollbar styling via QSS using theme values
    try:
        sb_width = self.STYLES['DarkTheme'].get('ScrollbarWidth', 10)
        sb_bg = self.STYLES['DarkTheme'].get('ScrollbarBackground', 'transparent')
        sb_handle = self.STYLES['DarkTheme'].get('ScrollbarHandle', '#3A3A3A')
        sb_handle_hover = self.STYLES['DarkTheme'].get('ScrollbarHandleHover', '#5A5A5A')
        sb_radius = self.STYLES['DarkTheme'].get('ScrollbarRadius', 6)

        qss = f"""
        QPlainTextEdit {{
            background: {self.STYLES['DarkTheme'].get('EditorBackground', '#1F1F1F')};
            color: {self.STYLES['DarkTheme'].get('Foreground', '#E8E8E8')};
            border: 1px solid {self.STYLES['DarkTheme'].get('ActiveHighlightColor', '#C84B31')};
        }}
        QScrollBar:vertical {{
            background: {sb_bg};
            width: {sb_width}px;
            margin: 0px 2px 0px 2px;
        }}
        QScrollBar::handle:vertical {{
            background: {sb_handle};
            min-height: 20px;
            border-radius: {sb_radius}px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {sb_handle_hover};
        }}
        QScrollBar::add-line, QScrollBar::sub-line {{
            height: 0px;
            subcontrol-origin: margin;
        }}
        QScrollBar::add-page, QScrollBar::sub-page {{
            background: none;
        }}
        QScrollBar:horizontal {{
            background: {sb_bg};
            height: {sb_width}px;
        }}
        QScrollBar::handle:horizontal {{
            background: {sb_handle};
            min-width: 20px;
            border-radius: {sb_radius}px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: {sb_handle_hover};
        }}
        """

        # Apply stylesheet to the text edit so its scrollbars get the style
        self.text_edit.setStyleSheet(qss)
    except Exception:
        # don't crash if theme keys missing
        pass
    
    layout.addWidget(editor_widget)
    
    self.text_edit.setContextMenuPolicy(Qt.CustomContextMenu)
    self.text_edit.customContextMenuRequested.connect(self.show_text_edit_context_menu)

    return area


def create_editor_toolbar(self):
    # Reload
    reload_action = QAction("Reload", self)
    reload_action.triggered.connect(self.reload_file_action)
    self.editor_toolbar.addAction(reload_action)
    
    # Save
    save_action = QAction("Save (Ctrl+S)", self)
    save_action.setShortcut("Ctrl+S")
    save_action.triggered.connect(lambda: self.save_file_action(self.current_tab))
    self.editor_toolbar.addAction(save_action)
    
    self.editor_toolbar.addSeparator()

    # Undo
    self.undo_action = QAction("Undo (Ctrl+Z)", self)
    self.undo_action.setShortcut("Ctrl+Z")
    self.undo_action.triggered.connect(self.handle_undo)
    self.editor_toolbar.addAction(self.undo_action)
    
    # Redo
    self.redo_action = QAction("Redo (Ctrl+Y)", self)
    self.redo_action.setShortcut("Ctrl+Y")
    self.redo_action.triggered.connect(self.handle_redo)
    self.editor_toolbar.addAction(self.redo_action)
    
    spacer = QWidget()
    spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    self.editor_toolbar.addWidget(spacer)
