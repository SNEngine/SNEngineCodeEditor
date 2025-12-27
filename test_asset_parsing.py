"""
Test script to verify the .asset file parsing functionality
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt5.QtWidgets import QApplication
from view import SNILEditorWindow


def test_asset_parsing():
    """Test that the .asset file parsing functionality is working."""
    print("Testing .asset file parsing functionality...")

    # Create a QApplication (required for QWidget)
    app = QApplication(sys.argv)

    # Create the main window
    window = SNILEditorWindow()

    # Test parsing a .asset file
    test_file_path = r"E:\repos\Nagatoro-Novel-Game\Assets\SNEngine\Source\SNEngine\Resources\Dialogues\_startDialogue.asset"

    if os.path.exists(test_file_path):
        dialog_names = window.extract_dialog_names_from_file(test_file_path)
        print(f"Parsed {test_file_path}")
        print(f"Found dialog names: {dialog_names}")

        # Expected to find "_startDialogue" in the file
        if dialog_names:
            print(f"[OK] Successfully extracted {len(dialog_names)} dialog name(s) from the .asset file")
            print(f"Dialog names found: {dialog_names}")
        else:
            print("[FAIL] No dialog names found in the .asset file")
    else:
        print(f"[FAIL] Test file does not exist: {test_file_path}")

    print("Test completed!")


if __name__ == "__main__":
    test_asset_parsing()