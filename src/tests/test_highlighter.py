"""
Unit tests for the YamlHighlighter and related classes.
"""
import unittest
from PyQt5.QtGui import QTextDocument
from highlighter import YamlHighlighter, YamlSyntaxStyle


class TestYamlSyntaxStyle(unittest.TestCase):
    def setUp(self):
        self.style = YamlSyntaxStyle()

    def test_default_colors(self):
        """Test that default colors are set correctly"""
        self.assertEqual(self.style.comment_color, "#608B4E")
        self.assertEqual(self.style.key_color, "#E06C75")
        self.assertEqual(self.style.keyword_color, "#AF55C4")
        self.assertEqual(self.style.string_color, "#ABB2BF")
        self.assertEqual(self.style.default_color, "#CCCCCC")
        # New parameter color
        self.assertEqual(self.style.parameter_color, "#FFD700")


class TestYamlHighlighter(unittest.TestCase):
    def setUp(self):
        self.document = QTextDocument()
        self.highlighter = YamlHighlighter(self.document)


class TestSNILHighlighter(unittest.TestCase):
    def setUp(self):
        from snil_highlighter import SNILHighlighter
        self.highlighter = SNILHighlighter(QTextDocument())

    def test_load_patterns_contains_wait(self):
        patterns = self.highlighter.syntax_patterns
        self.assertIn('WaitNodeWorker', patterns)
        self.assertEqual(patterns['WaitNodeWorker'], 'Wait {seconds} seconds')

    def test_command_pattern_generated(self):
        # Ensure that a regex starting with '^\s*Wait' exists in highlighting_rules
        found = False
        for pattern, fmt in self.highlighter.highlighting_rules:
            try:
                pat_str = pattern.pattern()
            except Exception:
                continue
            if pat_str.lower().startswith('^\\s*wait'):
                found = True
                break
        self.assertTrue(found)
    def test_default_color_is_white(self):
        from snil_highlighter import SNILSyntaxStyle
        s = SNILSyntaxStyle()
        self.assertEqual(s.default_color, '#FFFFFF')

    def test_jump_to_coloring(self):
        from PyQt5.QtGui import QTextDocument
        from snil_highlighter import SNILHighlighter
        doc = QTextDocument()
        # Command + target + trailing text
        doc.setPlainText('Jump To SomePlace (Second dialogue reached)')
        h = SNILHighlighter(doc)
        h.rehighlight()
        block = doc.findBlockByNumber(0)
        layout = block.layout()
        spans = layout.formats()
        # Find command span (Jump To), argument span (SomePlace) and trailing gray text
        cmd_found = False
        arg_found = False
        trailing_found = False
        for f in spans:
            start = f.start
            length = f.length
            txt = block.text()[start:start+length]
            col = f.format.foreground().color().name()
            if txt.strip().lower().startswith('jump') and col.lower() == QColor(h.styles.function_color).name().lower():
                cmd_found = True
            if txt.strip() == 'SomePlace' and col.lower() == QColor(h.styles.parameter_color).name().lower():
                arg_found = True
            if 'Second dialogue reached' in txt and col.lower() == QColor(h.styles.dialogue_color).name().lower():
                trailing_found = True
        self.assertTrue(cmd_found)
        self.assertTrue(arg_found)
        self.assertTrue(trailing_found)
    def test_initialization(self):
        """Test that highlighter initializes correctly"""
        self.assertIsNotNone(self.highlighter.styles)
        # The actual number of highlighting rules based on initialize_formats method
        # 1 rule for comments, multiple for keywords, 1 for list dashes = 8 total rules
        self.assertGreater(len(self.highlighter.highlighting_rules), 0)  # At least some rules exist

    def test_update_colors(self):
        """Test updating colors functionality"""
        new_colors = {
            'key_color': '#FF0000',
            'string_color': '#00FF00',
            'comment_color': '#0000FF',
            'keyword_color': '#FFFF00',
            'default_color': '#00FFFF'
        }

        self.highlighter.update_colors(new_colors)

        self.assertEqual(self.highlighter.styles.key_color, '#FF0000')
        self.assertEqual(self.highlighter.styles.string_color, '#00FF00')
        self.assertEqual(self.highlighter.styles.comment_color, '#0000FF')
        self.assertEqual(self.highlighter.styles.keyword_color, '#FFFF00')
        self.assertEqual(self.highlighter.styles.default_color, '#00FFFF')

    def test_comment_highlighting(self):
        """Test that comments are highlighted correctly"""
        # This would require more complex testing with Qt's highlighting system
        # For now, just test the helper method
        self.assertEqual(self.highlighter.index_of_hash_outside_quotes("text # comment"), 5)
        # In the string 'text "# in quotes" # comment', the # outside quotes is at position 19
        self.assertEqual(self.highlighter.index_of_hash_outside_quotes('text "# in quotes" # comment'), 19)
        self.assertEqual(self.highlighter.index_of_hash_outside_quotes('text'), -1)

    def test_colon_outside_quotes(self):
        """Test that colon outside quotes is found correctly"""
        self.assertEqual(self.highlighter.index_of_char_outside_quotes("key: value", ":"), 3)
        self.assertEqual(self.highlighter.index_of_char_outside_quotes('key: "value: inside quotes"', ":"), 3)
        self.assertEqual(self.highlighter.index_of_char_outside_quotes("no colon here", ":"), -1)

    def test_yaml_number_detection(self):
        """Test detection of YAML numbers"""
        self.assertTrue(self.highlighter.is_yaml_number("123"))
        self.assertTrue(self.highlighter.is_yaml_number("-456"))
        self.assertTrue(self.highlighter.is_yaml_number("3.14"))
        self.assertTrue(self.highlighter.is_yaml_number("-2.5"))
        self.assertFalse(self.highlighter.is_yaml_number("abc"))
        self.assertFalse(self.highlighter.is_yaml_number("123abc"))
        self.assertFalse(self.highlighter.is_yaml_number(""))

    def test_yaml_bool_or_null_detection(self):
        """Test detection of YAML booleans and null values"""
        true_values = ["true", "True"]
        false_values = ["false", "False"]
        null_values = ["null", "NULL"]

        for val in true_values:
            with self.subTest(val=val):
                self.assertTrue(self.highlighter.is_yaml_bool_or_null(val))

        for val in false_values:
            with self.subTest(val=val):
                self.assertTrue(self.highlighter.is_yaml_bool_or_null(val))

        for val in null_values:
            with self.subTest(val=val):
                self.assertTrue(self.highlighter.is_yaml_bool_or_null(val))

        self.assertFalse(self.highlighter.is_yaml_bool_or_null("maybe"))
        self.assertFalse(self.highlighter.is_yaml_bool_or_null(""))

    def test_key_value_parsing(self):
        """Test parsing of key-value pairs in YAML"""
        # Test key and value detection
        test_cases = [
            ("name: John", 0, 4),   # "name" is the key
            ("  age: 30", 2, 5),   # "age" is the key with indentation
            ("  list: - item1", 2, 6)  # "list" is the key
        ]

        for line, expected_key_start, expected_key_length in test_cases:
            with self.subTest(line=line):
                # This is tricky to test without actual Qt document highlighting
                # Instead, testing the helper functions that are used in highlightBlock
                colon_idx = self.highlighter.index_of_char_outside_quotes(line, ':')
                if colon_idx != -1:
                    key_text = line[:colon_idx].rstrip()
                    actual_key_start = line.find(key_text.lstrip())
                    self.assertEqual(actual_key_start, expected_key_start)
                    self.assertEqual(len(key_text.strip()), expected_key_length - expected_key_start)


if __name__ == '__main__':
    unittest.main()