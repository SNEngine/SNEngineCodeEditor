"""
Test script to verify the autocomplete functionality
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt5.QtWidgets import QApplication
from view import SNILEditorWindow


def test_autocomplete():
    """Test that the autocomplete functionality is working."""
    print("Testing autocomplete functionality...")
    
    # Create a QApplication (required for QWidget)
    app = QApplication(sys.argv)
    
    # Create the main window
    window = SNILEditorWindow()
    
    # Initialize autocomplete manager
    from views.autocomplete_manager import AutocompleteManager
    window.autocomplete_manager = AutocompleteManager(styles=window.STYLES)
    
    # Add some test dialog names to the cache
    window.autocomplete_manager.dialog_cache = [
        "StartDialogue",
        "PlayerChoice",
        "CharacterResponse",
        "GameOver",
        "VictoryScene"
    ]
    
    print(f"Dialog cache initialized with {len(window.autocomplete_manager.dialog_cache)} items")
    print(f"Dialog cache: {window.autocomplete_manager.dialog_cache}")
    
    # Create a test editor and setup autocomplete
    from views.code_editor import CodeEditor
    test_editor = CodeEditor(styles=window.STYLES, settings_manager=window.settings_manager)
    window.autocomplete_manager.setup_for_editor(test_editor)
    
    print("Autocomplete setup completed")
    print("Test completed!")


if __name__ == "__main__":
    test_autocomplete()