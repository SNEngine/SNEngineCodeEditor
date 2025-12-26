# src/session_manager.py
import os
import json
import sys  
from typing import Dict, Any, List, TYPE_CHECKING
from PyQt5.QtGui import QColor 
from PyQt5.QtGui import QIcon, QPixmap

from models import SNILTab 

# For static type checking without circular import at runtime
if TYPE_CHECKING:
    from view import SNILEditorWindow
    from PyQt5.QtWidgets import QTextEdit 

class SessionManager:
    """
    Manages saving and loading the editor's session state.
    Includes saving the last open path for QFileDialog.
    """
    
    SESSION_FILENAME = "session.json"

    def __init__(self, parent_window: 'YAMLEditorWindow'):
        self.parent_window = parent_window
        
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            try:
                base_path = os.path.dirname(os.path.abspath(__file__))
            except NameError:
                 base_path = os.getcwd()
            
        self.session_file_path = os.path.join(base_path, self.SESSION_FILENAME)
        

    def save_session(self):
        """
        Saves the current application state to session.json.
        """
        current_tab_index = -1
        if self.parent_window.current_tab:
            try:
                current_tab_index = self.parent_window.open_tabs.index(self.parent_window.current_tab)
            except ValueError:
                current_tab_index = -1

        session_data = {
            'root_path': self.parent_window.root_path,
            'current_tab_index': current_tab_index,
            'open_tabs': [], # Always initialize as empty list
            'foldouts': self.parent_window._foldouts,
            'last_open_dir': self.parent_window._last_open_dir,
            'font_size': self.parent_window._current_font_size
        }

        # If there's no root_path, we still want to save last_open_dir
        if not self.parent_window.root_path:
            if self.parent_window._last_open_dir:
                session_data['last_open_dir'] = self.parent_window._last_open_dir
            # If no root_path and no last_open_dir, then nothing significant to save
            elif not self.parent_window.open_tabs: # Only return if no tabs are open either
                if os.path.exists(self.session_file_path):
                    try:
                        os.remove(self.session_file_path)
                    except Exception as e:
                        print(f"Warning: Could not clear session file: {e}")
                return

        # Always iterate and save open tabs
        for tab in self.parent_window.open_tabs:
            tab_data = {
                'file_path': tab.file_path,
                'is_dirty': tab.is_dirty,
                'dirty_content': tab.snil_text if tab.is_dirty else None
            }
            session_data['open_tabs'].append(tab_data)

        try:
            with open(self.session_file_path, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=4)
            print("Session saved successfully.")
        except Exception as e:
            print(f"Error saving session: {e}")

    def load_session(self) -> Dict[str, Any] | None:
        """Loads session data from session.json."""
        if not os.path.exists(self.session_file_path):
            return None

        try:
            with open(self.session_file_path, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            if 'root_path' in session_data or 'last_open_dir' in session_data:
                return session_data
            else:
                print("Session file is corrupt or incomplete.")
                return None

        except Exception as e:
            print(f"Error loading session: {e}")
            return None
            
    def restore_session(self):
        """Restores the saved application state on startup."""
        session_data = self.load_session()
        if not session_data:
            return

        root_path = session_data.get('root_path')
        # These variables are no longer used in SNIL editor
        root_localization_path = None
        active_language = None
        open_tabs_data = session_data.get('open_tabs', [])
        current_tab_index = session_data.get('current_tab_index', -1)
        foldouts = session_data.get('foldouts', {})
        last_open_dir = session_data.get('last_open_dir')
        saved_font_size = session_data.get('font_size', 14) # Default to 14 if not saved

        # 1. Restore last path for QFileDialog
        if last_open_dir and os.path.isdir(last_open_dir):
            self.parent_window._last_open_dir = last_open_dir
        
        # 2. If no project is open, stop
        if not root_path or not os.path.isdir(root_path):
            return
            
        # Restore root_path
        if root_path and os.path.isdir(root_path):
            self.parent_window.root_path = root_path

        # 3. Restore folder foldout states
        self.parent_window._foldouts = foldouts

        # 4. Load folder structure 
        error_color = QColor(self.parent_window.STYLES['DarkTheme']['NotificationError'])
        success_color = QColor(self.parent_window.STYLES['DarkTheme']['NotificationSuccess'])
        
        # Load the file structure
        new_structure = self.parent_window.file_service.get_file_structure_from_path(root_path)

        if not self.parent_window.validator.validate_structure(new_structure):
            self.parent_window.show_notification(
                f"Session folder validation failed: {self.parent_window.validator.get_last_error()}", 
                error_color, 
                duration_ms=5000
            )
            return
            
        self.parent_window.temp_structure = new_structure
        self.parent_window.root_path = self.parent_window.temp_structure.get('root_path')

        folder_name = os.path.basename(root_path)
        # self.parent_window.language_label.setText(f"Language: {folder_name}") # Removed
        self.parent_window.show_notification(
            f"Structure loaded from previous session: {folder_name}", 
            success_color
        )

        # 5. Restore open tabs
        for tab_data in open_tabs_data:
            file_path = tab_data.get('file_path')
            is_dirty = tab_data.get('is_dirty', False)
            dirty_content = tab_data.get('dirty_content')
            
            # Normalize the file_path from session_data for consistent comparison
            normalized_tab_file_path = self.parent_window.file_service.normalize_path(file_path)

            if not os.path.exists(file_path): continue
            
            file_content = ""
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
            except Exception as e:
                print(f"Error reading file {os.path.basename(file_path)} during restore: {e}")
                continue

            # Check if the file is part of the project structure or if it's a standalone file that exists
            is_valid_file = False
            if self.parent_window.temp_structure and 'structure' in self.parent_window.temp_structure:
                for normalized_folder, files in self.parent_window.temp_structure['structure'].items():
                    file_name = os.path.basename(file_path)
                    # Use the normalized_tab_file_path for comparison
                    if file_name in files and normalized_tab_file_path.startswith(normalized_folder):
                         is_valid_file = True
                         break

            # If the file exists on disk, allow it to be opened even if it's not in the project structure
            # This handles files opened via "Open File" that are outside the project folder
            if os.path.exists(file_path):
                content_to_use = dirty_content if is_dirty and dirty_content is not None else file_content

                new_tab = SNILTab(file_path, content_to_use)
                new_tab.is_dirty = is_dirty
                self.parent_window.open_tabs.append(new_tab)

        # 6. Set active tab
        if self.parent_window.open_tabs:
            target_index = min(current_tab_index, len(self.parent_window.open_tabs) - 1)

            if target_index < 0:
                 target_index = 0

            self.parent_window.current_tab_index = target_index
            self.parent_window.current_tab = self.parent_window.open_tabs[target_index]

            # Use helper function to ensure consistent text edit updates
            if hasattr(self.parent_window, 'update_text_edit_content'):
                self.parent_window.update_text_edit_content()
            else:
                # Fallback if helper function is not available
                self.parent_window.text_edit.setPlainText(self.parent_window.current_tab.snil_text)
                self.parent_window.text_edit.document().clearUndoRedoStacks()
                # Update syntax highlighter with current theme colors
                if hasattr(self.parent_window, 'highlighter') and self.parent_window.highlighter:
                    highlighter_colors = {
                        'directive_color': self.parent_window.STYLES['DarkTheme'].get('SyntaxKeyColor', '#E06C75'),
                        'dialogue_color': self.parent_window.STYLES['DarkTheme'].get('SyntaxStringColor', '#ABB2BF'),
                        'comment_color': self.parent_window.STYLES['DarkTheme'].get('SyntaxCommentColor', '#608B4E'),
                        'keyword_color': self.parent_window.STYLES['DarkTheme'].get('SyntaxKeywordColor', '#AF55C4'),
                        'function_color': self.parent_window.STYLES['DarkTheme'].get('SyntaxFunctionColor', '#56B6C2'),
                        'parameter_color': self.parent_window.STYLES['DarkTheme'].get('SyntaxParameterColor', '#FFD700'),
                        'default_color': self.parent_window.STYLES['DarkTheme'].get('SyntaxDefaultColor', '#CCCCCC')
                    }
                    self.parent_window.highlighter.update_colors(highlighter_colors)

                    # Force re-highlighting to apply the new colors
                    doc = self.parent_window.text_edit.document()
                    self.parent_window.highlighter.setDocument(None)
                    self.parent_window.highlighter.setDocument(doc)
        else:
            self.parent_window.current_tab_index = -1
            self.parent_window.current_tab = None
            # Use helper function to ensure consistent text edit updates
            if hasattr(self.parent_window, 'update_text_edit_content'):
                self.parent_window.update_text_edit_content()
            else:
                # Fallback if helper function is not available
                if hasattr(self.parent_window.text_edit, 'setPlainText'):
                    self.parent_window.text_edit.setPlainText("")
                else:
                    self.parent_window.text_edit.setPlainText("")

                # RESTORED: Use clearUndoRedoStacks()
                if hasattr(self.parent_window.text_edit, 'document') and hasattr(self.parent_window.text_edit.document(), 'clearUndoRedoStacks'):
                    self.parent_window.text_edit.document().clearUndoRedoStacks()

        # 7. Update UI
        self.parent_window.draw_file_tree()
        self.parent_window.draw_tabs_placeholder()
        self.parent_window.update_status_bar()
        self.parent_window.update_undo_redo_ui()

        # 8. Restore font size
        # Use settings manager value if available, otherwise use session value
        if hasattr(self.parent_window, 'settings_manager') and self.parent_window.settings_manager:
            # Settings manager has the current user preference
            restored_font_size = self.parent_window.settings_manager.font_size
        else:
            # Fallback to session value if settings manager not available at this point
            restored_font_size = saved_font_size

        self.parent_window._current_font_size = restored_font_size
        if hasattr(self.parent_window, 'text_edit'):
            # Update font size in text editor
            font = self.parent_window.text_edit.font()
            font.setPointSize(restored_font_size)
            self.parent_window.text_edit.setFont(font)

            # Update font size label in status bar if it exists
            if hasattr(self.parent_window, 'font_size_label'):
                self.parent_window.font_size_label.setText(f"Font Size: {restored_font_size} (Ctrl+↑/↓)")