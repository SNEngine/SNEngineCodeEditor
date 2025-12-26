"""
Unit tests for the YAMLEditorWindow class and related functions in view.py.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QColor

# Add the src directory to the sys.path to allow importing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from view import YAMLEditorWindow


class TestYAMLEditorWindow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create a QApplication instance for testing (required for Qt widgets)
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        self.window = YAMLEditorWindow()

    def tearDown(self):
        # Clean up the window after each test
        self.window.close()
        del self.window

    def test_initialization(self):
        """Test that YAMLEditorWindow initializes correctly"""
        self.assertIsNotNone(self.window.STYLES)
        self.assertIsNotNone(self.window.CSS_STYLES)
        self.assertIsNotNone(self.window.validator)
        self.assertIsNotNone(self.window.file_service)
        self.assertIsNotNone(self.window.session_manager)
        self.assertEqual(len(self.window.open_tabs), 0)
        self.assertEqual(self.window.current_tab_index, -1)
        self.assertIsNone(self.window.current_tab)

    def test_load_styles(self):
        """Test that styles are loaded correctly"""
        styles = self.window._load_styles()
        self.assertIn('DarkTheme', styles)
        theme = styles['DarkTheme']
        self.assertIn('Background', theme)
        self.assertIn('Foreground', theme)
        self.assertIn('SecondaryBackground', theme)

    def test_generate_css(self):
        """Test that CSS is generated correctly from styles"""
        styles = self.window._load_styles()
        css = self.window._generate_css(styles)
        self.assertIsInstance(css, str)
        self.assertIn('background-color', css)
        self.assertIn('color', css)

    def test_get_resource_path(self):
        """Test the resource path functionality"""
        # Test with a relative path
        path = self.window._get_resource_path('styles.yaml')
        self.assertIsInstance(path, str)
        self.assertTrue(isinstance(path, str))

    def test_icon_creation_functions(self):
        """Test SVG icon creation functions"""
        # Test basic SVG content
        svg_content = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"><path fill="#E06C75" d="M14 6H8.5L7 4.5H2a1 1 0 0 0-1 1V11a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V7a1 1 0 0 0-1-1zM2 5h4.5l1 1h6.5v4H2V5z"/></svg>'
        
        # Test icon creation from SVG content
        icon = self.window._create_icon_from_svg_content(svg_content)
        self.assertIsNotNone(icon)
        
        # Test folder icon loading
        folder_svg = self.window._load_folder_icon()
        self.assertIsInstance(folder_svg, str)
        self.assertIn('svg', folder_svg)
        
        # Test YAML file icon loading
        yaml_svg = self.window._load_yaml_file_icon()
        self.assertIsInstance(yaml_svg, str)
        self.assertIn('svg', yaml_svg)

    def test_update_svg_colors(self):
        """Test SVG color updating functionality"""
        # Test with folder SVG content (contains folder-specific path data)
        folder_svg = '<svg><path fill="white" d="M2 4.5A1.5 1.5 0 0 1 3.5 3h3.086a1.5 1.5 0 0 1 1.06.44L8.56 4.354A1.5 1.5 0 0 0 9.62 4.8H12.5A1.5 1.5 0 0 1 14 6.3v5.2A1.5 1.5 0 0 1 12.5 13h-9A1.5 1.5 0 0 1 2 11.5v-7z"/></svg>'

        # Update with folder color
        updated_folder_svg = self.window._update_svg_colors(folder_svg, folder_color='#FF0000')
        self.assertIn('#FF0000', updated_folder_svg)

        # Test with YAML file SVG content (contains document-specific path)
        yaml_svg = '<svg><path fill="white" d="M4 2h5.5L13 5.5V13a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V3a1 1 0 0 1 1-1z"/></svg>'

        # Update with YAML color
        updated_yaml_svg = self.window._update_svg_colors(yaml_svg, yaml_color='#00FF00')
        self.assertIn('#00FF00', updated_yaml_svg)

    def test_notification_functions(self):
        """Test notification functionality"""
        # This tests the notification system without actually showing UI
        # We'll just make sure the methods exist and can be called without error
        
        # Mock the notification label if it doesn't exist
        if self.window._notification_label is None:
            from PyQt5.QtWidgets import QLabel
            self.window._notification_label = QLabel()
        
        color = QColor(255, 0, 0)  # Red color
        self.window.show_notification("Test message", color, 1000)  # 1 second duration
        
        # The notification should be set without errors
        self.assertIsNotNone(self.window._notification_label)

    def test_status_bar_functions(self):
        """Test status bar functionality"""
        initial_status = self.window.status_label.text()
        self.window.update_status_bar()
        
        # Status should be updated without errors
        current_status = self.window.status_label.text()
        self.assertIsInstance(current_status, str)

    @patch('view.QFileDialog.getExistingDirectory')
    def test_open_folder_dialog(self, mock_get_directory):
        """Test the open folder dialog functionality"""
        # Mock the dialog to return a test path
        test_path = "/test/path"
        mock_get_directory.return_value = test_path
        
        # Since the actual dialog behavior relies on Qt UI components,
        # we're testing that the function can be called without errors
        # The actual behavior would be tested in integration tests
        self.window.open_folder_dialog()
        
        # Verify that the dialog was called
        mock_get_directory.assert_called_once()

    def test_change_font_size(self):
        """Test font size change functionality"""
        initial_size = self.window._current_font_size
        
        # Test increasing font size
        self.window.change_font_size(1)
        self.assertEqual(self.window._current_font_size, initial_size + 1)
        
        # Test decreasing font size
        self.window.change_font_size(-1)
        self.assertEqual(self.window._current_font_size, initial_size)

    def test_update_highlighter_colors(self):
        """Test updating highlighter colors"""
        # Mock the text_edit and highlighter attributes
        self.window.text_edit = Mock()
        self.window.highlighter = Mock()
        
        # Create a mock styles dict
        test_styles = {
            'SyntaxKeyColor': '#FF0000',
            'SyntaxStringColor': '#00FF00',
            'SyntaxCommentColor': '#0000FF',
            'SyntaxKeywordColor': '#FFFF00',
            'SyntaxDefaultColor': '#FFFFFF'
        }
        
        # This should not raise an exception
        self.window.update_highlighter_colors(test_styles)

    def test_apply_style_update_merges(self):
        """Test that applying a partial style update merges with existing theme instead of replacing it"""
        # Set initial full theme
        initial = {
            'Background': '#111111',
            'Foreground': '#222222',
            'SyntaxStringColor': '#123456'
        }
        self.window.STYLES = {'DarkTheme': initial.copy()}

        # Apply partial update
        partial = {'SyntaxDefaultColor': '#FFFFFF'}
        self.window._apply_style_update(partial)

        # Ensure previous keys remain
        self.assertEqual(self.window.STYLES['DarkTheme']['SyntaxStringColor'], '#123456')
        # Ensure new key applied
        self.assertEqual(self.window.STYLES['DarkTheme']['SyntaxDefaultColor'], '#FFFFFF')

    def test_styles_editor_writes_file_on_apply_and_save(self):
        """Test that StylesEditor writes to the styles file on Apply and Save"""
        import tempfile
        import shutil
        tmpdir = tempfile.mkdtemp()
        try:
            styles_path = os.path.join(tmpdir, 'styles.yaml')
            # Create a minimal styles file
            with open(styles_path, 'w', encoding='utf-8') as f:
                f.write('DarkTheme:\n  Background: "#000000"\n')

            from views.styles_editor import StylesEditorDialog
            dialog = StylesEditorDialog(parent=self.window, styles_file_path=styles_path)

            # Change a color in the dialog inputs
            # Find a color input key and set new color
            some_key = None
            for k in dialog.color_inputs.keys():
                some_key = k
                break
            if some_key is None:
                self.skipTest('No color inputs available')

            dialog.color_inputs[some_key]['input'].setText('#ABCDEF')
            # Apply (should write file)
            dialog.apply_styles()

            # Verify file contains the new color
            with open(styles_path, 'r', encoding='utf-8') as f:
                text = f.read()
            self.assertIn('#ABCDEF', text)

            # Now Save (should also write and close dialog)
            dialog.color_inputs[some_key]['input'].setText('#123456')
            dialog.save_styles()
            with open(styles_path, 'r', encoding='utf-8') as f:
                text2 = f.read()
            self.assertIn('#123456', text2)
        finally:
            shutil.rmtree(tmpdir)


if __name__ == '__main__':
    unittest.main()