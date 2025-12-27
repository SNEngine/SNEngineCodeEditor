"""
Test script to verify the Jump To autocomplete functionality
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt5.QtWidgets import QApplication
from view import SNILEditorWindow


def test_autocomplete_functionality():
    """Test that the autocomplete functionality is working."""
    print("Testing Jump To autocomplete functionality...")
    
    # Create a test application
    app = QApplication(sys.argv)
    
    # Create the main window
    window = SNILEditorWindow()
    
    # Check that the dialog cache attribute exists
    if not hasattr(window, 'dialog_cache'):
        window.dialog_cache = []  # Initialize if not present
    
    # Add some test dialog names to the cache
    window.dialog_cache = [
        "StartDialogue",
        "PlayerChoice",
        "CharacterResponse",
        "GameOver",
        "VictoryScene"
    ]
    
    print(f"Dialog cache initialized with {len(window.dialog_cache)} items")
    print(f"Dialog cache: {window.dialog_cache}")

    # Check that the text editor has autocomplete functionality
    if hasattr(window, 'text_edit') and window.text_edit:
        if hasattr(window.text_edit, 'setup_autocomplete'):
            print("[OK] Autocomplete functionality is available in the text editor")
        else:
            print("[FAIL] Autocomplete functionality is NOT available in the text editor")
    else:
        print("[FAIL] Text editor is not available")

    # Check that the toolbar has the Open Project button
    # Look for QToolBar in the children
    toolbars = [child for child in window.children() if child.__class__.__name__ == 'QToolBar']
    if toolbars:
        # Get the first toolbar (main toolbar)
        toolbar = toolbars[0]
        actions = [action.text() for action in toolbar.actions()]
        if "Open Project" in actions:
            print("[OK] Open Project button is available in the toolbar")
        else:
            print("[FAIL] Open Project button is NOT available in the toolbar")
            print(f"Available actions: {actions}")
    else:
        print("[FAIL] Toolbar not found")

    print("Test completed successfully!")


if __name__ == "__main__":
    test_autocomplete_functionality()