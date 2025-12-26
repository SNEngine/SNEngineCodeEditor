# src/snil_highlighter.py
from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PyQt5.QtCore import Qt, QRegularExpression
import re
from typing import Dict, Any

import json
import os

# --- Style Constants for SNIL ---
class SNILSyntaxStyle:
    def __init__(self):
        # Colors in HEX format, used in Rich Text and adapted for Qt
        self.comment_color = "#608B4E"      # Bright green
        self.directive_color = "#61AFEF"    # Blue for directives like Start/End (changed by request)
        self.keyword_color = "#FFB86C"      # Warm orange for keywords (replacing purple)
        self.dialogue_color = "#ABB2BF"     # Light gray (for dialogue text)
        self.function_color = "#56B6C2"     # Cyan (for function-related keywords)
        self.parameter_color = "#FFD700"    # Gold (for template parameters in {})
        self.default_color = "#FFFFFF"      # White for plain text (user requested)


class SNILHighlighter(QSyntaxHighlighter):
    def __init__(self, document, custom_colors=None):
        super().__init__(document)
        self.styles = SNILSyntaxStyle()

        # Load syntax patterns from JSON file
        self.syntax_patterns = self.load_syntax_patterns()

        self.highlighting_rules = []
        self.command_keywords = set()  # collected command keywords for argument coloring

        # Если переданы пользовательские цвета, обновляем стили
        if custom_colors:
            self.update_colors(custom_colors)
        else:
            self.initialize_formats()

    def update_colors(self, colors):
        """Обновление цветов подсветки"""
        if 'directive_color' in colors:
            self.styles.directive_color = colors['directive_color']
        if 'dialogue_color' in colors:
            self.styles.dialogue_color = colors['dialogue_color']
        if 'comment_color' in colors:
            self.styles.comment_color = colors['comment_color']
        if 'keyword_color' in colors:
            self.styles.keyword_color = colors['keyword_color']
        if 'function_color' in colors:
            self.styles.function_color = colors['function_color']
        if 'parameter_color' in colors:
            self.styles.parameter_color = colors['parameter_color']
        if 'default_color' in colors:
            self.styles.default_color = colors['default_color']

        # Обновляем форматы с новыми цветами
        self.initialize_formats()

    def load_syntax_patterns(self):
        """Load syntax patterns from snil_syntax.json file."""
        try:
            # Get the directory of the current file to build the path to the JSON file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            json_path = os.path.join(current_dir, 'snil_syntax.json')

            with open(json_path, 'r', encoding='utf-8') as f:
                patterns = json.load(f)
            return patterns
        except FileNotFoundError:
            # If the file is not found, return default patterns
            print(f"Warning: snil_syntax.json not found at {json_path}")
            return {
                "ClearBackgroundNodeWorker": "Clear Background",
                "CompareIntegersNodeWorker": "Compare {a} {type} {b}",
                "DebugNodeWorker": "Print {message}",
                "DialogNodeWorker": "{_character} says {_text}",
                "DialogOnScreenNodeWorker": "Dialog On Screen {_text}",
                "ExitNodeWorker": "End",
                "GroupCallsNodeWorker": "function {_name}",
                "HideCharacterNodeWorker": "Hide {_character}",
                "IfNodeWorker": "IF {condition}",
                "JumpToDialogueNodeWorker": "Jump To {_dialogue}",
                "PlaySoundNodeWorker": "Play Sound {_sound}",
                "SetBackgroundNodeWorker": "Show Background {_sprite}",
                "ShowCharacterNodeWorker": "Show {_character} with emotion {_emotion}",
                "ShowVariantsNodeWorker": "Show Variants {_variants}",
                "StartNodeWorker": "Start",
                "WaitNodeWorker": "Wait {seconds} seconds"
            }
        except Exception as e:
            print(f"Error loading syntax patterns: {e}")
            return {}

    def initialize_formats(self):
        # Clear the rules list to avoid duplicates when updating colors
        self.highlighting_rules.clear()

        # 1. Format for comments (# or //)
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(self.styles.comment_color))
        # Regular expression for comment: starts with # or // and goes to the end of the line
        self.highlighting_rules.append((QRegularExpression(r"(#|//).*"), comment_format))

        # 2. Format for directives (name:, Start, End) - these should remain unchanged
        directive_format = QTextCharFormat()
        directive_format.setForeground(QColor(self.styles.directive_color))
        directive_format.setFontWeight(QFont.Bold)
        directives = [r"name:\s*.+", r"^\s*Start\s*$", r"^\s*End\s*$"]
        for directive_pattern in directives:
            pattern = QRegularExpression(directive_pattern, QRegularExpression.CaseInsensitiveOption)
            self.highlighting_rules.append((pattern, directive_format))

        # 3. Format for function keywords (function, call, end)
        function_format = QTextCharFormat()
        function_format.setForeground(QColor(self.styles.function_color))
        function_format.setFontWeight(QFont.Bold)
        function_keywords = [r"^\s*function\s+.+", r"^\s*call\s+.+", r"^\s*end\s*$"]
        for func_pattern in function_keywords:
            pattern = QRegularExpression(func_pattern, QRegularExpression.CaseInsensitiveOption)
            self.highlighting_rules.append((pattern, function_format))

        # 3.1. Command patterns derived from syntax file (e.g., "Wait {seconds} seconds")
        # Highlight the leading command (like 'Wait') using the function color so commands are visible.
        command_format = QTextCharFormat()
        command_format.setForeground(QColor(self.styles.function_color))
        command_format.setFontWeight(QFont.Bold)
        # Iterate unique syntax pattern values and create a simple regex that highlights the command keyword
        seen = set()
        for pattern_text in self.syntax_patterns.values():
            if not pattern_text or not isinstance(pattern_text, str):
                continue
            keyword = pattern_text.strip().split()[0]
            if not keyword:
                continue
            key_l = keyword.lower()
            if key_l in seen:
                continue
            seen.add(key_l)
            # Store keyword for later argument highlighting
            self.command_keywords.add(keyword)
            # Match lines starting with the command keyword (case-insensitive)
            cmd_pattern = QRegularExpression(r"^\s*" + re.escape(keyword) + r"\b.*$", QRegularExpression.CaseInsensitiveOption)
            self.highlighting_rules.append((cmd_pattern, command_format))

        # 4. Format for conditional keywords (If Show Variant, True:, False:, endif)
        conditional_format = QTextCharFormat()
        conditional_format.setForeground(QColor(self.styles.keyword_color))
        conditional_format.setFontWeight(QFont.Bold)
        conditional_keywords = [r"^\s*If\s+Show\s+Variant\s*$", r"^\s*Variants:\s*$", r"^\s*True:\s*$", r"^\s*False:\s*$", r"^\s*endif\s*$"]
        for cond_pattern in conditional_keywords:
            pattern = QRegularExpression(cond_pattern, QRegularExpression.CaseInsensitiveOption)
            self.highlighting_rules.append((pattern, conditional_format))

        # 5. Format for variable assignments (set [name] = [value])
        variable_format = QTextCharFormat()
        variable_format.setForeground(QColor(self.styles.keyword_color))
        variable_pattern = QRegularExpression(r"^\s*set\s+\w+\s*=.*$", QRegularExpression.CaseInsensitiveOption)
        self.highlighting_rules.append((variable_pattern, variable_format))

        # 6. Format for jump statements (Jump To [name]) - highlight the command like functions and argument separately
        jump_format = QTextCharFormat()
        jump_format.setForeground(QColor(self.styles.function_color))
        jump_format.setFontWeight(QFont.Bold)
        # Only highlight the 'Jump To' keyword part here; argument will be colored later
        jump_pattern = QRegularExpression(r"^\s*Jump\s+To\b", QRegularExpression.CaseInsensitiveOption)
        self.highlighting_rules.append((jump_pattern, jump_format))

        # 7. Format for dialogue lines (character says text) - using syntax patterns
        dialogue_format = QTextCharFormat()
        dialogue_format.setForeground(QColor(self.styles.dialogue_color))
        # Pattern to match character says dialogue format
        dialogue_pattern = QRegularExpression(r"^\s*[^:]+says\s+.+$", QRegularExpression.CaseInsensitiveOption)
        self.highlighting_rules.append((dialogue_pattern, dialogue_format))

    def highlightBlock(self, text: str):
        """
        The main method, overriding line highlighting.
        Apply syntax highlighting for SNIL specific patterns.
        """
        # Apply rules based on QRegularExpression first
        for pattern, format in self.highlighting_rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                match = it.next()
                # Apply format to the entire found part
                self.setFormat(match.capturedStart(), match.capturedLength(), format)

        # Special handling for multi-script separator (---)
        separator_format = QTextCharFormat()
        separator_format.setForeground(QColor(self.styles.keyword_color))
        separator_format.setFontWeight(QFont.Bold)
        separator_pattern = QRegularExpression(r"^\s*---\s*$")
        match = separator_pattern.match(text)
        if match.hasMatch():
            self.setFormat(match.capturedStart(), match.capturedLength(), separator_format)

        # --- Smart parameter highlighting based on syntax patterns from JSON
        # This will match actual usage against defined patterns and highlight corresponding arguments
        self.highlight_smart_parameters(text)

        # --- Special handling for dialogues: make the character name highlighted as a parameter and the rest as default/normal text
        # Example: "Nagatoro says You'll have to wait and see!" -> 'Nagatoro' gets parameter color
        dialogue_match = re.match(r"^\s*([^:]+?)\s+says\s+(.+)$", text, re.IGNORECASE)
        if dialogue_match:
            name_part = dialogue_match.group(1).strip()
            # Find name start index in original text
            name_index = text.find(dialogue_match.group(1))
            if name_index != -1 and name_part:
                param_format = QTextCharFormat()
                param_format.setForeground(QColor(self.styles.parameter_color))
                param_format.setFontWeight(QFont.Bold)

                default_format = QTextCharFormat()
                default_format.setForeground(QColor(self.styles.default_color))

                # Apply name format
                self.setFormat(name_index, len(name_part), param_format)

                # Apply default to the rest of the line (overwrites earlier dialogue coloring)
                rest_start = name_index + len(name_part)
                rest_len = len(text) - rest_start
                if rest_len > 0:
                    self.setFormat(rest_start, rest_len, default_format)

        # --- Special handling for numeric arguments in command lines (e.g., "Wait 2 seconds")
        # If line starts with a known command keyword, color numeric tokens as parameters
        if self.command_keywords:
            lower_text = text.lstrip().lower()
            for kw in self.command_keywords:
                if lower_text.startswith(kw.lower()):
                    param_format = QTextCharFormat()
                    param_format.setForeground(QColor(self.styles.parameter_color))
                    param_format.setFontWeight(QFont.Bold)
                    for m in re.finditer(r"\b\d+\b", text):
                        self.setFormat(m.start(), m.end() - m.start(), param_format)
                    break

        # --- Special handling for 'Jump To' argument coloring
        # Color the command itself like functions, color the first token argument as parameter (yellow), and the rest as dialogue/gray
        jump_match = re.match(r"^\s*(Jump\s+To)\s+(.+)$", text, re.IGNORECASE)
        if jump_match:
            cmd_text = jump_match.group(1)
            args_text = jump_match.group(2).strip()
            cmd_index = text.lower().find(cmd_text.lower())
            if cmd_index != -1:
                cmd_fmt = QTextCharFormat()
                cmd_fmt.setForeground(QColor(self.styles.function_color))
                cmd_fmt.setFontWeight(QFont.Bold)
                self.setFormat(cmd_index, len(cmd_text), cmd_fmt)
            if args_text:
                # Split args_text into first token (target) and the rest
                parts = args_text.split(None, 1)
                first = parts[0]
                rest = parts[1] if len(parts) > 1 else ''
                # Find first index of the first token in the text
                arg_index = text.lower().find(first.lower(), (cmd_index + len(cmd_text)) if cmd_index != -1 else 0)
                if arg_index != -1:
                    first_fmt = QTextCharFormat()
                    first_fmt.setForeground(QColor(self.styles.parameter_color))
                    first_fmt.setFontWeight(QFont.Bold)
                    self.setFormat(arg_index, len(first), first_fmt)
                    # If there's rest, color it with dialogue color (gray)
                    if rest:
                        rest_index = arg_index + len(first) + 1  # +1 for space
                        rest_fmt = QTextCharFormat()
                        rest_fmt.setForeground(QColor(self.styles.dialogue_color))
                        self.setFormat(rest_index, len(rest), rest_fmt)

        # Highlight template parameters (content within curly braces {}) - called last to ensure parameters are highlighted
        self.highlight_template_parameters(text)

    def highlight_smart_parameters(self, text: str):
        """
        Smart parameter highlighting that matches actual usage against defined patterns
        and highlights corresponding arguments based on the syntax patterns from JSON.
        """
        # For each defined syntax pattern, check if the current text matches
        for pattern_text in self.syntax_patterns.values():
            if not pattern_text or not isinstance(pattern_text, str):
                continue

            # Escape special regex characters in the pattern, but keep template parameter placeholders
            # Replace template parameters with regex groups that match any non-whitespace sequence
            escaped_pattern = re.escape(pattern_text)
            # Replace escaped template parameters like \{_character\} with regex patterns
            regex_pattern = re.sub(r'\\\{[^}]+\\\}', r'([^\\s]+)', escaped_pattern)

            # Create a regex that matches the command structure
            match = re.match(f'^\\s*{regex_pattern}\\s*$', text, re.IGNORECASE)
            if match:
                # Found a match, now extract the actual parameter values
                param_format = QTextCharFormat()
                param_format.setForeground(QColor(self.styles.parameter_color))
                param_format.setFontWeight(QFont.Bold)

                # Extract template parameter names to know positions
                template_params = re.findall(r'\{([^}]+)\}', pattern_text)

                # Now match the text against the pattern to extract actual values
                # Replace template parameters with capturing groups
                actual_regex = re.escape(pattern_text)
                for param in template_params:
                    actual_regex = actual_regex.replace(r'\{' + param + r'\}', r'([^"]+?)')

                actual_match = re.match(f'^\\s*{actual_regex}\\s*$', text, re.IGNORECASE)
                if actual_match and len(template_params) == len(actual_match.groups()):
                    # Find positions of actual values in the text
                    current_pos = 0
                    for i, actual_value in enumerate(actual_match.groups()):
                        # Find the actual value in the text starting from current_pos
                        value_pos = text.find(actual_value.strip(), current_pos)
                        if value_pos != -1:
                            self.setFormat(value_pos, len(actual_value.strip()), param_format)
                            # Move past this value for the next search
                            current_pos = value_pos + len(actual_value.strip())

    def highlight_template_parameters(self, text: str):
        """
        Highlight content within curly braces {} based on the syntax patterns from JSON.
        """
        # Find all template parameters in the format {param_name}
        param_pattern = re.compile(r'\{[^}]+\}')
        matches = param_pattern.finditer(text)

        param_format = QTextCharFormat()
        param_format.setForeground(QColor(self.styles.parameter_color))
        param_format.setFontWeight(QFont.Bold)

        for match in matches:
            start = match.start()
            end = match.end()
            self.setFormat(start, end - start, param_format)