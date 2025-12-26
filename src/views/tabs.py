import os
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout
from PyQt5.QtCore import QSize, Qt, QTimer, QPoint
from PyQt5.QtCore import QVariantAnimation
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QFrame
from PyQt5.QtWidgets import QGraphicsOpacityEffect
from PyQt5.QtCore import QPropertyAnimation
from PyQt5.QtCore import QEasingCurve
from PyQt5.QtWidgets import QMenu, QMessageBox
from PyQt5.QtGui import QPalette


def draw_tabs_placeholder(self):
    self.tab_placeholder.clear()
    if not self.open_tabs:
        return

    highlight_color = self.STYLES['DarkTheme']['HighlightColor']
    bg_color = self.STYLES['DarkTheme']['Background']
    editor_bg = self.STYLES['DarkTheme']['EditorBackground']
    hover_bg = self.STYLES['DarkTheme']['FilePanelHover']
    
    close_icon_color = self.STYLES['DarkTheme']['EditorCloseButtonColor']

    for i, tab in enumerate(self.open_tabs):
        tab_name = os.path.basename(tab.file_path)
        if tab.is_dirty:
            tab_name += "*"
        
        tab_container = QWidget()
        tab_layout = QHBoxLayout(tab_container)
        tab_layout.setContentsMargins(5, 0, 2, 0)
        tab_layout.setSpacing(4)
        
        tab_label = QLabel(tab_name)
        tab_layout.addWidget(tab_label)

        close_button = QPushButton("×")
        close_button.setFixedSize(QSize(20, 20))
        close_button.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                margin: 0;
                padding: 0;
                color: {close_icon_color};
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{ background: transparent; }}
        """)
        close_button.setCursor(Qt.PointingHandCursor)
        close_button.clicked.connect(lambda checked, idx=i: close_tab_with_animation(self, idx))
        tab_layout.addWidget(close_button)

        def _tab_mouse_event(event, index=i, container=tab_container):
            if event.button() == Qt.LeftButton:
                self.switch_tab_action(index)
            elif event.button() == Qt.RightButton:
                # show animated context menu
                try:
                    show_tab_context_menu(self, container.mapToGlobal(event.pos()), index)
                except Exception:
                    pass

        # store file path on the widget for lookup when animating
        try:
            tab_container.setProperty('file_path', tab.file_path)
        except Exception:
            pass

        tab_container.mousePressEvent = _tab_mouse_event
        tab_container.setCursor(Qt.PointingHandCursor)

        is_active = i == self.current_tab_index
        style_sheet = f"""
            QWidget {{ padding: 4px 10px; margin: 0 1px; border-bottom: 2px solid transparent; background-color: {bg_color};}}
        """
        if is_active:
            style_sheet += f"""
                QWidget {{ background-color: {editor_bg}; color: white; border-bottom: 2px solid {highlight_color}; }}
            """
        else:
            style_sheet += f"""
                QWidget:hover {{ background-color: {hover_bg}; }}
            """

        tab_container.setStyleSheet(style_sheet)
        self.tab_placeholder.addWidget(tab_container)

    spacer = QWidget()
    spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    self.tab_placeholder.addWidget(spacer)
    
    # Right-aligned brand label
    try:
        brand_color = self.STYLES['DarkTheme'].get('BrandTextColor', self.STYLES['DarkTheme'].get('HighlightColor'))
    except Exception:
        brand_color = self.STYLES['DarkTheme'].get('HighlightColor', '#C84B31')
    try:
        brand_label = QLabel("SNEngine")
        # larger text, no background, soft weight
        brand_label.setStyleSheet(f"color: {brand_color}; background: transparent; font-weight: 700; font-size: 14pt; padding-right:12px;")
        brand_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.tab_placeholder.addWidget(brand_label)

        # animated color shimmer: interpolate between brand_color and a lighter variant
        try:
            base_col = QColor(brand_color)
            light_col = QColor(base_col).lighter(140)

            # forward animation (base -> light)
            forward = QVariantAnimation(self)
            forward.setStartValue(base_col)
            forward.setEndValue(light_col)
            forward.setDuration(3500)
            forward.setEasingCurve(QEasingCurve.InOutSine)

            # backward animation (light -> base)
            backward = QVariantAnimation(self)
            backward.setStartValue(light_col)
            backward.setEndValue(base_col)
            backward.setDuration(3500)
            backward.setEasingCurve(QEasingCurve.InOutSine)

            # sequential group to ping-pong smoothly
            from PyQt5.QtCore import QSequentialAnimationGroup
            group = QSequentialAnimationGroup(self)
            group.addAnimation(forward)
            group.addAnimation(backward)

            def _on_val(v):
                try:
                    brand_label.setStyleSheet(f"color: {v.name()}; background: transparent; font-weight: 700; font-size: 14pt; padding-right:12px;")
                except Exception:
                    pass

            forward.valueChanged.connect(_on_val)
            backward.valueChanged.connect(_on_val)

            group.setLoopCount(-1)
            # keep reference alive on self
            self._brand_anim = group
            group.start()
        except Exception:
            pass
    except Exception:
        pass


def show_tab_context_menu(self, global_pos: QPoint, index: int):
    """Show a custom popup menu with staggered fade-in animations for each menu item."""
    # build menu items (label, callback)
    # helper actions
    def _open_file_action():
        try:
            from PyQt5.QtWidgets import QFileDialog
            path, _ = QFileDialog.getOpenFileName(self, "Open SNIL File", "", "SNIL Files (*.snil);;All Files (*)")
            if path:
                # use existing loader
                try:
                    self.load_file(path)
                except Exception:
                    pass
        except Exception:
            pass

    items = [
        ("Close Tab", lambda: close_tab_with_animation(self, index)),
        ("Close Other Tabs", lambda: close_other_tabs(self, index)),
        ("Close Tabs With Deleted Files", lambda: close_deleted_tabs(self)),
    ]

    # parent the popup to main window so stacking is correct
    menu = QFrame(self, Qt.Popup | Qt.FramelessWindowHint)
    menu.setObjectName('TabContextMenu')
    # Use a solid background via stylesheet (avoids platform translucent issues)
    menu.setStyleSheet("QFrame#TabContextMenu { background: %s; border-radius:6px; padding:6px; } QPushButton { background: transparent; border: none; color: %s; padding:6px 12px; text-align: left; } QPushButton:hover { background: rgba(255,255,255,0.03); }" % (self.STYLES['DarkTheme'].get('SecondaryBackground', '#2A2A2A'), self.STYLES['DarkTheme'].get('Foreground', '#E8E8E8')))
    layout = QVBoxLayout(menu)
    layout.setContentsMargins(6, 6, 6, 6)
    layout.setSpacing(2)

    animations = []
    delay_step = 60
    fg = self.STYLES['DarkTheme'].get('Foreground', '#E8E8E8')
    font_family = self.STYLES['DarkTheme'].get('EditorFontName', None)
    for idx, (label_text, callback) in enumerate(items):
        btn = QPushButton(label_text)
        btn.setCursor(Qt.PointingHandCursor)
        # hook up callback
        def _make_cb(cb):
            return lambda checked=False: (menu.close(), cb())
        btn.clicked.connect(_make_cb(callback))

        # style explicitly so text is visible
        btn.setFlat(True)
        btn.setMinimumWidth(160)
        btn.setMinimumHeight(28)
        btn.setStyleSheet(f"color: {fg}; background: transparent; border: none; padding:6px 12px; text-align: left; font-size:12px;")
        if font_family:
            try:
                from PyQt5.QtGui import QFont
                btn.setFont(QFont(font_family, 11))
            except Exception:
                pass
        layout.addWidget(btn)

        # opacity effect and animation
        effect = QGraphicsOpacityEffect(btn)
        btn.setGraphicsEffect(effect)
        effect.setOpacity(0.0)
        anim = QPropertyAnimation(effect, b"opacity")
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setDuration(220)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        animations.append((anim, idx * delay_step))

    # size menu to contents before showing
    menu.adjustSize()
    menu.move(global_pos + QPoint(6, 6))
    menu.show()
    menu.raise_()

    # keep animation references alive on the menu object
    menu._animations = animations

    # start animations staggered (bind anim to lambda to preserve reference)
    for anim, delay in animations:
        QTimer.singleShot(delay, (lambda a=anim: a.start()))


def close_other_tabs(self, keep_index: int):
    keep = None
    try:
        keep = self.open_tabs[keep_index]
    except Exception:
        return
    new_tabs = [keep]
    self.open_tabs = new_tabs
    self.current_tab_index = 0
    self.current_tab = keep
    self.draw_tabs_placeholder()
    self.draw_file_tree()


def close_deleted_tabs(self):
    # remove tabs whose files no longer exist
    self.open_tabs = [t for t in self.open_tabs if os.path.exists(t.file_path)]
    self.current_tab_index = min(self.current_tab_index, len(self.open_tabs) - 1) if self.open_tabs else -1
    if self.current_tab_index >= 0:
        self.current_tab = self.open_tabs[self.current_tab_index]
    else:
        self.current_tab = None
    self.draw_tabs_placeholder()
    self.draw_file_tree()
    self.update_status_bar()


def close_tab_with_animation(self, index: int):
    """Animate tab widget (fade + shrink) then close the tab model entry."""
    if not (0 <= index < len(self.open_tabs)):
        return

    tab_to_close = self.open_tabs[index]

    # confirm unsaved changes similarly to try_close_tab
    if tab_to_close.is_dirty:
        try:
            from PyQt5.QtWidgets import QMessageBox
            reply = question_message_box(self, 'Save Changes',
                                          f"File '{os.path.basename(tab_to_close.file_path)}' has unsaved changes. Do you want to save?",
                                          QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel, QMessageBox.Cancel)
            if reply == QMessageBox.Cancel:
                return
            if reply == QMessageBox.Save:
                self.save_file_action(tab_to_close)
                if tab_to_close.is_dirty:
                    return
        except Exception:
            # if message box fails, abort close
            return

    file_path = tab_to_close.file_path

    # locate the widget that was created for this tab by stored property
    widget_to_animate = None
    try:
        for w in self.tab_placeholder.findChildren(QWidget):
            try:
                if w.property('file_path') == file_path:
                    widget_to_animate = w
                    break
            except Exception:
                continue
    except Exception:
        widget_to_animate = None

    # fallback: if we cannot find the widget, close immediately
    if widget_to_animate is None:
        self.try_close_tab(index)
        return

    # prepare animations: opacity + shrink height
    try:
        effect = QGraphicsOpacityEffect(widget_to_animate)
        widget_to_animate.setGraphicsEffect(effect)
        anim_op = QPropertyAnimation(effect, b"opacity")
        anim_op.setStartValue(1.0)
        anim_op.setEndValue(0.0)
        anim_op.setDuration(260)

        anim_h = QPropertyAnimation(widget_to_animate, b"maximumHeight")
        start_h = widget_to_animate.sizeHint().height() or widget_to_animate.height() or 28
        anim_h.setStartValue(start_h)
        anim_h.setEndValue(0)
        anim_h.setDuration(260)
        anim_h.setEasingCurve(QEasingCurve.InCubic)

        # keep references so GC doesn't stop animations
        widget_to_animate._close_anim_refs = (effect, anim_op, anim_h)

        def _on_finished():
            # find current index again (tabs might have changed)
            idx = next((i for i, t in enumerate(self.open_tabs) if t.file_path == file_path), None)
            if idx is None:
                return
            # call existing close logic which handles stacks and UI
            self.try_close_tab(idx)

        anim_h.finished.connect(_on_finished)

        anim_op.start()
        anim_h.start()
    except Exception:
        # fallback to immediate close
        self.try_close_tab(index)


def switch_tab_action(self, index):
    """Switch to a different tab, ensuring the text edit component updates properly."""
    if not (0 <= index < len(self.open_tabs)):
        return

    # Update current tab and index
    self.current_tab_index = index
    self.current_tab = self.open_tabs[index]

    # Use helper function to update text edit content
    update_text_edit_content(self)

    # Update dialogue map after switching tabs
    if hasattr(self, 'dialogue_map_panel') and self.dialogue_map_panel:
        current_text = self.text_edit.toPlainText() if hasattr(self, 'text_edit') and self.text_edit else ""
        self.dialogue_map_panel.update_dialogue_map(current_text)

    # Update UI
    self.draw_tabs_placeholder()
    self.draw_file_tree()
    self.update_status_bar()
    self.update_undo_redo_ui()


def handle_text_change(self):
    if not self.current_tab:
        return

    new_text = self.text_edit.toPlainText()
    if self.current_tab.snil_text != new_text:
        if len(self.current_tab.undo_stack) > 0 and self.current_tab.undo_stack[-1] != self.current_tab.snil_text:
            self.current_tab.undo_stack.append(self.current_tab.snil_text)
        elif len(self.current_tab.undo_stack) == 0:
            self.current_tab.undo_stack.append(self.current_tab.snil_text)

        self.current_tab.redo_stack.clear()
        self.current_tab.snil_text = new_text
        self.current_tab.is_dirty = True

    self.draw_tabs_placeholder()
    self.draw_file_tree()
    self.update_status_bar()
    self.update_undo_redo_ui()


def try_close_tab(self, index: int):
    """Close a tab and update the editor to show the appropriate content."""
    if not (0 <= index < len(self.open_tabs)):
        return

    tab_to_close = self.open_tabs[index]
    if tab_to_close.is_dirty:
        reply = question_message_box(self, 'Save Changes',
                                     f"File '{os.path.basename(tab_to_close.file_path)}' has unsaved changes. Do you want to save?",
                                     QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel, QMessageBox.Cancel)
        if reply == QMessageBox.Cancel:
            return
        if reply == QMessageBox.Save:
            self.save_file_action(tab_to_close)
            if tab_to_close.is_dirty:
                return

    # Determine if the tab being closed is the currently active one
    was_current_tab = (index == self.current_tab_index)

    # Remove the tab from the list
    closed_tab = self.open_tabs.pop(index)

    # Update the current tab index if needed
    if self.open_tabs:
        # Adjust current tab index if the current tab was after the closed tab
        if self.current_tab_index > index:
            self.current_tab_index -= 1
            # Update current tab reference to the new position
            if 0 <= self.current_tab_index < len(self.open_tabs):
                self.current_tab = self.open_tabs[self.current_tab_index]

        # If the currently active tab was closed, we need to select a new tab
        if was_current_tab:
            # If we closed the last tab, select the new last tab
            if self.current_tab_index >= len(self.open_tabs):
                self.current_tab_index = max(0, len(self.open_tabs) - 1)

            # Update the current tab reference
            if 0 <= self.current_tab_index < len(self.open_tabs):
                self.current_tab = self.open_tabs[self.current_tab_index]
            else:
                self.current_tab = None
                self.current_tab_index = -1

        # Ensure we have a valid current tab reference
        if self.current_tab_index >= 0 and self.current_tab_index < len(self.open_tabs):
            self.current_tab = self.open_tabs[self.current_tab_index]

        # Use helper function to update text edit content
        update_text_edit_content(self)
    else:
        # No tabs left
        self.current_tab = None
        self.current_tab_index = -1
        # Use helper function to update text edit content
        update_text_edit_content(self)

    # Update UI
    self.draw_tabs_placeholder()
    self.draw_file_tree()
    self.update_status_bar()
    self.update_undo_redo_ui()


def update_undo_redo_ui(self):
    if not self.current_tab:
        try:
            self.undo_action.setEnabled(False)
            self.redo_action.setEnabled(False)
        except Exception:
            pass
        return

    self.undo_action.setEnabled(len(self.current_tab.undo_stack) > 0)
    self.redo_action.setEnabled(len(self.current_tab.redo_stack) > 0)


def update_text_edit_content(self):
    """Helper function to ensure text edit content is properly updated from the current tab."""
    if self.current_tab:
        # Update the text edit with the current tab's content
        if hasattr(self.text_edit, 'setPlainText'):
            self.text_edit.setPlainText(self.current_tab.snil_text)
        else:
            self.text_edit.setPlainText(self.current_tab.snil_text)

        # Clear undo/redo stacks to avoid confusion with new content
        if hasattr(self.text_edit, 'document') and hasattr(self.text_edit.document(), 'clearUndoRedoStacks'):
            self.text_edit.document().clearUndoRedoStacks()

        # Update syntax highlighter with current theme colors
        if hasattr(self, 'highlighter') and self.highlighter:
            highlighter_colors = {
                'directive_color': self.STYLES['DarkTheme'].get('SyntaxKeyColor', '#E06C75'),
                'dialogue_color': self.STYLES['DarkTheme'].get('SyntaxStringColor', '#ABB2BF'),
                'comment_color': self.STYLES['DarkTheme'].get('SyntaxCommentColor', '#608B4E'),
                'keyword_color': self.STYLES['DarkTheme'].get('SyntaxKeywordColor', '#AF55C4'),
                'function_color': self.STYLES['DarkTheme'].get('SyntaxFunctionColor', '#56B6C2'),
                'default_color': self.STYLES['DarkTheme'].get('SyntaxDefaultColor', '#CCCCCC')
            }
            self.highlighter.update_colors(highlighter_colors)

            # Force re-highlighting to apply the new colors
            doc = self.text_edit.document()
            self.highlighter.setDocument(None)
            self.highlighter.setDocument(doc)
    else:
        if hasattr(self.text_edit, 'setPlainText'):
            self.text_edit.setPlainText("")
        else:
            self.text_edit.setPlainText("")

        if hasattr(self.text_edit, 'document') and hasattr(self.text_edit.document(), 'clearUndoRedoStacks'):
            self.text_edit.document().clearUndoRedoStacks()

    # Update dialogue map after updating text content
    if hasattr(self, 'dialogue_map_panel') and self.dialogue_map_panel:
        current_text = self.text_edit.toPlainText() if hasattr(self, 'text_edit') and self.text_edit else ""
        self.dialogue_map_panel.update_dialogue_map(current_text)

    # Update script graph window if it's open
    if hasattr(self, 'script_graph_window') and self.script_graph_window:
        current_text = self.text_edit.toPlainText() if hasattr(self, 'text_edit') and self.text_edit else ""
        self.script_graph_window.parse_script_content(current_text)


def question_message_box(parent, title, text, buttons, default_button):
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(text)
    msg_box.setStandardButtons(buttons)
    msg_box.setDefaultButton(default_button)

    # Apply custom styles
    palette = QPalette()
    background_color = parent.STYLES['DarkTheme']['SecondaryBackground']
    foreground_color = parent.STYLES['DarkTheme']['Foreground']
    border_color = parent.STYLES['DarkTheme']['BorderColor']

    palette.setColor(QPalette.Window, QColor(background_color))
    palette.setColor(QPalette.WindowText, QColor(foreground_color))
    msg_box.setPalette(palette)

    # Apply a stylesheet for more detailed control
    highlight_color = parent.STYLES['DarkTheme']['HighlightColor']
    msg_box.setStyleSheet(f"""
        QMessageBox {{
            background-color: {background_color};
            color: {foreground_color};
            border: 1px solid {border_color};
            font-size: 14px;
            padding: 15px;
            spacing: 10px; /* Increased spacing between buttons */
        }}
        QMessageBox QLabel {{
            background-color: transparent; /* Removed background from text */
            color: {foreground_color};
            padding: 10px 0;
        }}
        QMessageBox QPushButton {{
            background-color: {parent.STYLES['DarkTheme']['FilePanelBackground']};
            color: {foreground_color};
            border: 1px solid {highlight_color};
            padding: 8px 20px;
            min-width: 100px;
            border-radius: 4px;
            margin: 5px; /* Added margin for spacing */
        }}
        QMessageBox QPushButton:hover {{
            background-color: {parent.STYLES['DarkTheme']['FilePanelHover']};
        }}
        QMessageBox QPushButton:pressed {{
            background-color: {parent.STYLES['DarkTheme']['Background']};
        }}
    """)
    return msg_box.exec_()
