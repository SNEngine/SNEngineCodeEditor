"""File operations: load, save, switch, reload."""
import os
from PyQt5.QtGui import QColor


def load_file(self, file_path: str):
    """Load a file into a new or existing tab."""
    if not file_path:
        return

    normalized_path = self.file_service.normalize_path(file_path)
    existing_tab = next((t for t in self.open_tabs if self.file_service.normalize_path(t.file_path) == normalized_path), None)

    if existing_tab:
        self.switch_tab_action(self.open_tabs.index(existing_tab))
        return

    file_content = ""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
        else:
            color = QColor(self.STYLES['DarkTheme']['NotificationWarning'])
            self.show_notification(f"File not found: {os.path.basename(file_path)}", color)
            return
    except Exception as e:
        color = QColor(self.STYLES['DarkTheme']['NotificationError'])
        self.show_notification(f"Error reading file: {os.path.basename(file_path)}", color)
        print(f"File read error: {e}")
        return

    from models import SNILTab
    new_tab = SNILTab(file_path, file_content) # Keep original file_path for tab management
    self.open_tabs.append(new_tab)
    self.current_tab_index = len(self.open_tabs) - 1
    self.current_tab = new_tab

    # Use the helper function to ensure consistent text edit updates
    if hasattr(self, 'update_text_edit_content'):
        self.update_text_edit_content()
    else:
        # Fallback if helper function is not available
        if hasattr(self.text_edit, 'setPlainText'):
            self.text_edit.setPlainText(self.current_tab.snil_text)
        else:
            self.text_edit.setPlainText(self.current_tab.snil_text)

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

    # Update dialogue map after loading content
    if hasattr(self, 'dialogue_map_panel') and self.dialogue_map_panel:
        current_text = self.text_edit.toPlainText() if hasattr(self, 'text_edit') and self.text_edit else ""
        self.dialogue_map_panel.update_dialogue_map(current_text)

    # Update script graph window if it's open
    if hasattr(self, 'script_graph_window') and self.script_graph_window:
        current_text = self.text_edit.toPlainText() if hasattr(self, 'text_edit') and self.text_edit else ""
        self.script_graph_window.parse_script_content(current_text)

    self.draw_tabs_placeholder()
    self.draw_file_tree()
    self.update_status_bar()
    self.update_undo_redo_ui()


def try_switch_file_action(self, new_file_path: str):
    """Switch to another file, checking for unsaved changes."""
    from PyQt5.QtWidgets import QMessageBox

    file_name = os.path.basename(new_file_path).lower()
    # Only allow .snil files
    if not file_name.endswith('.snil'):
        color = QColor(self.STYLES['DarkTheme']['NotificationWarning'])
        self.show_notification(f"Cannot open {file_name}. Only .snil files are supported.", color)
        return

    current_tab = self.current_tab
    new_path_normalized = self.file_service.normalize_path(new_file_path)

    if current_tab and self.file_service.normalize_path(current_tab.file_path) == new_path_normalized:
        return

    if current_tab is None or not current_tab.is_dirty:
        self.load_file(new_file_path)
        return

    current_file_name = os.path.basename(current_tab.file_path)

    reply = QMessageBox.question(self, 'Unsaved Changes',
        f"Do you want to save changes to file '{current_file_name}' before switching to '{os.path.basename(new_file_path)}'?",
        QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel, QMessageBox.Cancel)

    if reply == QMessageBox.Save:
        self.save_file_action(current_tab)
        if not current_tab.is_dirty:
            self.load_file(new_file_path)
    elif reply == QMessageBox.Discard:
        current_tab.is_dirty = False
        self.load_file(new_file_path)

    self.draw_tabs_placeholder()
    self.draw_file_tree()
    self.update_status_bar()


def save_file_action(self, tab_to_save):
    """Save a tab's content to disk."""
    if not tab_to_save or not tab_to_save.is_dirty or not tab_to_save.file_path:
        color = QColor(self.STYLES['DarkTheme']['NotificationWarning'])
        self.show_notification("Nothing to save.", color)
        return

    try:
        with open(tab_to_save.file_path, 'w', encoding='utf-8') as f:
            f.write(tab_to_save.snil_text)

        tab_to_save.is_dirty = False

        self.draw_tabs_placeholder()
        self.draw_file_tree()
        self.update_status_bar()
        color = QColor(self.STYLES['DarkTheme']['NotificationSuccess'])
        self.show_notification(f"File saved successfully: {os.path.basename(tab_to_save.file_path)}", color)

    except Exception as ex:
        color = QColor(self.STYLES['DarkTheme']['NotificationError'])
        self.show_notification(f"Failed to save: {os.path.basename(tab_to_save.file_path)}", color)
        print(f"File save error: {ex}")


def reload_file_action(self):
    """Reload current file from disk."""
    if self.current_tab:
        self.load_file(self.current_tab.file_path)
        color = QColor(self.STYLES['DarkTheme']['NotificationWarning'])
        self.show_notification(f"File reloaded: {os.path.basename(self.current_tab.file_path)}", color)
    else:
        color = QColor(self.STYLES['DarkTheme']['NotificationWarning'])
        self.show_notification("No file open to reload.", color)
