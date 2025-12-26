# src/highlighter.py
from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PyQt5.QtCore import Qt, QRegularExpression
import re
from typing import Dict, Any

# --- Style Constants (based on screenshot and dark theme) ---
# In a real project, this should be loaded from YamlSyntaxStyle
# Using dark colors, close to Unity Editor
class YamlSyntaxStyle:
    def __init__(self):
        # Colors in HEX format, used in Rich Text and adapted for Qt
        self.comment_color = "#608B4E"  # Bright green
        self.key_color = "#E06C75"      # Soft red (for keys)
        self.keyword_color = "#AF55C4"  # Purple (for boolean/null)
        self.string_color = "#ABB2BF"   # Light gray (for strings and list dashes, instead of blue)
        self.default_color = "#CCCCCC"  # Light gray (for plain text)
        self.parameter_color = "#FFD700"  # Gold for parameters inside braces {}


class YamlHighlighter(QSyntaxHighlighter):
    def __init__(self, document, custom_colors=None):
        super().__init__(document)
        self.styles = YamlSyntaxStyle()

        self.highlighting_rules = []

        # Если переданы пользовательские цвета, обновляем стили
        if custom_colors:
            self.update_colors(custom_colors)
        else:
            self.initialize_formats()

    def update_colors(self, colors):
        """Обновление цветов подсветки"""
        if 'key_color' in colors:
            self.styles.key_color = colors['key_color']
        if 'string_color' in colors:
            self.styles.string_color = colors['string_color']
        if 'comment_color' in colors:
            self.styles.comment_color = colors['comment_color']
        if 'keyword_color' in colors:
            self.styles.keyword_color = colors['keyword_color']
        if 'default_color' in colors:
            self.styles.default_color = colors['default_color']
        if 'parameter_color' in colors:
            self.styles.parameter_color = colors['parameter_color']

        # Обновляем форматы с новыми цветами
        self.initialize_formats()

    def initialize_formats(self):
        # 1. Format for comments (CommentColor)
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(self.styles.comment_color))
        # Regular expression for comment: starts with # and goes to the end of the line
        self.highlighting_rules.append((QRegularExpression("#.*"), comment_format))

        # 2. Format for keys (KeyColor) - Use it in the highlightBlock method

        # 3. Format for keywords (KeywordColor) - true, false, null, numbers
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor(self.styles.keyword_color))
        keywords = ["true", "false", "null", "True", "False", "NULL"]
        for word in keywords:
            # Word boundaries, so as not to highlight 'true' inside 'something-true'
            pattern = QRegularExpression(r'\b' + re.escape(word) + r'\b')
            self.highlighting_rules.append((pattern, keyword_format))

        # 4. Format for strings and list dashes (StringColor)
        string_format = QTextCharFormat()
        string_format.setForeground(QColor(self.styles.string_color))
        
        # Quoted strings (single or double)
        # This is complex, better handled in highlightBlock
        
        # List dash at the beginning of the line
        list_dash_format = QTextCharFormat()
        list_dash_format.setForeground(QColor(self.styles.string_color))
        # Pattern for list dash: ^(\s*)-(\s*)\S
        self.highlighting_rules.append((QRegularExpression(r"^\s*-\s*"), list_dash_format))


    def highlightBlock(self, text: str):
        """
        The main method, overriding line highlighting.
        Here, ApplyYamlHighlighting logic is implemented, but through QSyntaxHighlighter.
        """
        # Apply rules based on QRegularExpression
        for pattern, format in self.highlighting_rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                match = it.next()
                # Apply format to the entire found part
                self.setFormat(match.capturedStart(), match.capturedLength(), format)


        # --- Complex Logic: Keys and Values (Analogous to ApplyYamlHighlighting) ---

        default_format = QTextCharFormat()
        default_format.setForeground(QColor(self.styles.default_color))
        key_format = QTextCharFormat()
        key_format.setForeground(QColor(self.styles.key_color))
        string_format = QTextCharFormat()
        string_format.setForeground(QColor(self.styles.string_color))

        
        # 1. Find comment to avoid analyzing it
        # Use regex, mimicking IndexOfHashOutsideQuotes
        comment_match = re.search(r'#.*', text)
        content = text
        comment_start = -1
        if comment_match:
            # Find the hash index, ensure it's outside quotes
            try:
                comment_index = self.index_of_hash_outside_quotes(text)
                if comment_index >= 0:
                    comment_start = comment_index
                    content = text[:comment_index]
            except:
                # In case of error, leave the entire line to avoid breaking the application
                pass


        # 2. Find separator (:)
        colon_index = self.index_of_char_outside_quotes(content, ':')

        if colon_index >= 0:
            # We found a "key: value" pair
            key_text = content[:colon_index].strip()
            value_text = content[colon_index + 1:].lstrip()

            # --- Highlight Key (KeyColor) ---
            # Find the actual start of the key, skipping indents
            key_start_in_line = text.find(key_text.lstrip()) 
            
            if key_start_in_line != -1 and key_text.strip():
                # Key length
                key_end_in_line = key_start_in_line + len(key_text.strip())
                
                # Apply key format
                self.setFormat(key_start_in_line, len(key_text.strip()), key_format)

            # --- Highlight Value (StringColor/KeywordColor) ---
            value_start = text.find(value_text, colon_index + 1)
            
            if value_start != -1 and value_text:
                # If value is quoted (string)
                if value_text.startswith('"') and value_text.endswith('"') or \
                   value_text.startswith("'") and value_text.endswith("'"):
                    self.setFormat(value_start, len(value_text), string_format)
                
                # If it's numbers/booleans (need to use QRegularExpression for accuracy)
                elif self.is_yaml_bool_or_null(value_text) or self.is_yaml_number(value_text):
                    # Apply previously defined KeywordFormat
                    keyword_format = self.highlighting_rules[2][1] # Get format from rules
                    self.setFormat(value_start, len(value_text), keyword_format)
                
                # The rest - not quoted and not keywords/numbers (StringColor)
                else:
                    self.setFormat(value_start, len(value_text), string_format)

        
        # --- Highlight List Dash (Dash - already done in initialize_formats) ---
        # The `list_dash_format` rule already covers dashes at the beginning of the line.

        # --- Highlight template parameters inside values (apply after value highlighting so parameters override inner parts)
        self.highlight_template_parameters(text)


    def highlight_template_parameters(self, text: str):
        """
        Highlight content inside curly braces {} in YAML values.
        """
        param_pattern = re.compile(r'\{[^}]+\}')
        matches = param_pattern.finditer(text)

        param_format = QTextCharFormat()
        param_format.setForeground(QColor(self.styles.parameter_color))
        param_format.setFontWeight(QFont.Bold)

        for match in matches:
            start = match.start()
            end = match.end()
            self.setFormat(start, end - start, param_format)


    # --- Ported helper methods from C# ---

    def index_of_hash_outside_quotes(self, line: str) -> int:
        """Find # outside quotes (IndexOfHashOutsideQuotes)."""
        in_single = False
        in_double = False
        for i, c in enumerate(line):
            if c == '\'' and not in_double:
                in_single = not in_single
            elif c == '"' and not in_single:
                in_double = not in_double
            elif c == '#' and not in_single and not in_double:
                return i
        return -1

    def index_of_char_outside_quotes(self, line: str, target: str) -> int:
        """Find character outside quotes (IndexOfCharOutsideQuotes)."""
        in_single = False
        in_double = False
        for i, c in enumerate(line):
            if c == '\'' and not in_double:
                in_single = not in_single
            elif c == '"' and not in_single:
                in_double = not in_double
            elif c == target and not in_single and not in_double:
                return i
        return -1
    
    def is_yaml_number(self, s: str) -> bool:
        """Check for number (IsYamlNumber)."""
        return re.match(r"^[+-]?\d+(\.\d+)?$", s.strip()) is not None

    def is_yaml_bool_or_null(self, s: str) -> bool:
        """Check for boolean or null (IsYamlBoolOrNull)."""
        token = s.strip()
        return token in ["true", "false", "null", "True", "False", "NULL"]