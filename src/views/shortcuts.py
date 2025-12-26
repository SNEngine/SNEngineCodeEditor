"""Keyboard shortcuts and input handling."""
from PyQt5.QtCore import Qt
from views.search import show_search, hide_search


def keyPressEvent(self, event):
    """Handle keyboard events: Ctrl+S, Ctrl+Z, Ctrl+Y, Ctrl+Up/Down."""
    if event.modifiers() == Qt.ControlModifier:
        if event.key() == Qt.Key_Up:
            self.change_font_size(1)
            event.accept()
            return
        if event.key() == Qt.Key_Down:
            self.change_font_size(-1)
            event.accept()
            return
        if event.key() == Qt.Key_O:
            # Open file dialog
            try:
                self.open_file_dialog()
            except AttributeError:
                # If open_file_dialog doesn't exist, fallback to open folder
                self.open_folder_dialog()
            event.accept()
            return
        if event.key() == Qt.Key_S and self.current_tab:
            self.save_file_action(self.current_tab)
            event.accept()
            return
        if event.key() == Qt.Key_F:
            # open in-file search
            try:
                show_search(self)
            except Exception:
                # fallback: show widget if present
                if hasattr(self, 'editor_search_widget'):
                    self.editor_search_widget.setVisible(True)
            event.accept()
            return

    # If Esc pressed and search visible, hide it
    if event.key() == Qt.Key_Escape:
        if hasattr(self, 'editor_search_widget') and self.editor_search_widget.isVisible():
            try:
                hide_search(self)
            except Exception:
                try:
                    self.editor_search_widget.setVisible(False)
                    self.text_edit.setExtraSelections([])
                except Exception:
                    pass
            event.accept()
            return

    if event.key() == Qt.Key_Z and event.modifiers() == Qt.ControlModifier and self.undo_action.isEnabled():
        self.handle_undo()
        event.accept()
        return
    if event.key() == Qt.Key_Y and event.modifiers() == Qt.ControlModifier and self.redo_action.isEnabled():
        self.handle_redo()
        event.accept()
        return

    super(self.__class__, self).keyPressEvent(event)


def change_font_size(self, change):
    """Change font size in editor (Ctrl+Up/Down)."""
    new_size = self._current_font_size + change

    if 10 <= new_size <= 24:
        self._current_font_size = new_size
        # Update font size in settings manager
        if hasattr(self, 'settings_manager') and self.settings_manager:
            self.settings_manager.font_size = new_size

        # Update the font from settings in the text editor to ensure proper layout updates
        if hasattr(self, 'text_edit') and self.text_edit and hasattr(self.text_edit, 'update_font_from_settings'):
            # Use the update_font_from_settings method which properly handles layout updates
            # Temporarily update the font family to use the same one currently in settings
            current_font_family = self.text_edit.font().family()
            if hasattr(self, 'settings_manager') and self.settings_manager:
                # Save current font family, update size via settings manager, then restore family
                self.settings_manager.font_family = current_font_family
                # Now update the editor font which will handle all layout updates properly
                self.text_edit.update_font_from_settings()
            else:
                # Fallback: directly update font if settings manager not available
                font = self.text_edit.font()
                font.setPointSize(new_size)
                self.text_edit.setFont(font)

                # Check if line numbers are enabled and update accordingly
                show_line_numbers = True
                if hasattr(self, 'settings_manager') and self.settings_manager:
                    show_line_numbers = self.settings_manager.show_line_numbers

                if show_line_numbers and hasattr(self.text_edit, 'line_numbers') and self.text_edit.line_numbers:
                    # Update line numbers font as well
                    line_numbers_font = self.text_edit.line_numbers.font()
                    line_numbers_font.setPointSize(new_size - 1)
                    self.text_edit.line_numbers.setFont(line_numbers_font)

                # Update viewport margins based on whether line numbers should be shown
                if hasattr(self.text_edit, 'update_line_number_area_width') and show_line_numbers:
                    self.text_edit.update_line_number_area_width(0)
                elif hasattr(self.text_edit, 'setViewportMargins') and not show_line_numbers:
                    # If line numbers are disabled, ensure no left margin is set
                    self.text_edit.setViewportMargins(0, 0, 0, 0)
        else:
            # Fallback to direct font update
            font = self.text_edit.font()
            font.setPointSize(new_size)
            self.text_edit.setFont(font)

            # Check if line numbers are enabled and update accordingly
            show_line_numbers = True
            if hasattr(self, 'settings_manager') and self.settings_manager:
                show_line_numbers = self.settings_manager.show_line_numbers

            # Update line numbers as well for consistency if they are enabled
            if show_line_numbers and hasattr(self.text_edit, 'line_numbers') and self.text_edit.line_numbers:
                line_numbers_font = self.text_edit.line_numbers.font()
                line_numbers_font.setPointSize(new_size - 1)
                self.text_edit.line_numbers.setFont(line_numbers_font)

            # Update viewport margins based on whether line numbers should be shown
            if hasattr(self.text_edit, 'update_line_number_area_width') and show_line_numbers:
                self.text_edit.update_line_number_area_width(0)
            elif hasattr(self.text_edit, 'setViewportMargins') and not show_line_numbers:
                # If line numbers are disabled, ensure no left margin is set
                self.text_edit.setViewportMargins(0, 0, 0, 0)

        # Update font size label in status bar
        if hasattr(self, 'font_size_label') and self.font_size_label:
            self.font_size_label.setText(f"Font Size: {new_size} (Ctrl+↑/↓)")


def handle_undo(self):
    """Undo last change."""
    if not self.current_tab:
        return

    if len(self.current_tab.undo_stack) > 0:
        self.current_tab.redo_stack.append(self.current_tab.snil_text)
        text_to_restore = self.current_tab.undo_stack.pop()

        self.current_tab._snil_text = text_to_restore
        self.current_tab.is_dirty = True

        # Use helper function to ensure consistent text edit updates
        if hasattr(self, 'update_text_edit_content'):
            # Temporarily update the current tab content to reflect the undo
            original_text = self.text_edit.toPlainText()
            self.text_edit.setPlainText(text_to_restore)
            # Since highlighter is already set up, we can just trigger re-highlighting if needed
            if hasattr(self, 'highlighter') and self.highlighter:
                self.highlighter.rehighlight()
        else:
            self.text_edit.setPlainText(text_to_restore)

        self.draw_tabs_placeholder()
        self.draw_file_tree()
        self.update_status_bar()
        self.update_undo_redo_ui()


def handle_redo(self):
    """Redo last undone change."""
    if not self.current_tab:
        return

    if len(self.current_tab.redo_stack) > 0:
        self.current_tab.undo_stack.append(self.current_tab.snil_text)
        text_to_restore = self.current_tab.redo_stack.pop()

        self.current_tab._snil_text = text_to_restore
        self.current_tab.is_dirty = True

        # Use helper function to ensure consistent text edit updates
        if hasattr(self, 'update_text_edit_content'):
            # Temporarily update the current tab content to reflect the redo
            original_text = self.text_edit.toPlainText()
            self.text_edit.setPlainText(text_to_restore)
            # Since highlighter is already set up, we can just trigger re-highlighting if needed
            if hasattr(self, 'highlighter') and self.highlighter:
                self.highlighter.rehighlight()
        else:
            self.text_edit.setPlainText(text_to_restore)

        self.draw_tabs_placeholder()
        self.draw_file_tree()
        self.update_status_bar()
        self.update_undo_redo_ui()
