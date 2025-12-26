from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QLabel, QCheckBox
from PyQt5.QtGui import QTextCharFormat, QColor
from PyQt5.QtCore import Qt, QRegularExpression


def create_search_widget(self):
    widget = QWidget()
    layout = QHBoxLayout(widget)
    layout.setContentsMargins(2, 2, 2, 2)

    self.editor_search_input = QLineEdit()
    self.editor_search_input.setPlaceholderText("Find (Ctrl+F)...")
    self.editor_search_input.returnPressed.connect(lambda: perform_search(self))
    self.editor_search_input.textChanged.connect(lambda _: perform_search(self))
    layout.addWidget(self.editor_search_input)

    self.search_prev_btn = QPushButton("◀")
    self.search_prev_btn.setFixedWidth(28)
    self.search_prev_btn.clicked.connect(lambda: navigate_search(self, -1))
    layout.addWidget(self.search_prev_btn)

    self.search_next_btn = QPushButton("▶")
    self.search_next_btn.setFixedWidth(28)
    self.search_next_btn.clicked.connect(lambda: navigate_search(self, 1))
    layout.addWidget(self.search_next_btn)

    self.search_count_label = QLabel("")
    layout.addWidget(self.search_count_label)

    # Case-sensitivity toggle
    self.search_case_checkbox = QCheckBox("Match case")
    self.search_case_checkbox.setChecked(False)
    self.search_case_checkbox.stateChanged.connect(lambda _: perform_search(self))
    layout.addWidget(self.search_case_checkbox)

    self.search_close_btn = QPushButton("×")
    self.search_close_btn.setFixedWidth(28)
    self.search_close_btn.clicked.connect(lambda: hide_search(self))
    layout.addWidget(self.search_close_btn)

    widget.setVisible(False)

    # storage for found positions
    self._search_matches = []
    self._search_current = -1
    # attach to self for easy access
    self.editor_search_widget = widget
    return widget


def perform_search(self):
    query = self.editor_search_input.text()
    doc = self.text_edit.document()
    cursor = self.text_edit.textCursor()

    # clear previous selections
    self._search_matches = []
    self._search_current = -1
    extra_selections = []

    if not query:
        self.text_edit.setExtraSelections([])
        self.search_count_label.setText("")
        return

    fmt = QTextCharFormat()
    try:
        hl_color = QColor(self.STYLES['DarkTheme']['HighlightColor'])
    except Exception:
        hl_color = QColor('#444444')
    fmt.setBackground(hl_color)
    fmt.setForeground(QColor(self.STYLES['DarkTheme']['Foreground']))

    # find all occurrences using QRegularExpression (case-insensitive)
    # prepare regex with optional case sensitivity
    try:
        regex = QRegularExpression(query)
        if not getattr(self, 'search_case_checkbox', None) or not self.search_case_checkbox.isChecked():
            regex.setPatternOptions(QRegularExpression.CaseInsensitiveOption)
    except Exception:
        regex = QRegularExpression(query)

    cur = doc.find(regex, 0)
    while not cur.isNull():
        start = cur.selectionStart()
        end = cur.selectionEnd()
        self._search_matches.append((start, end))
        cur = doc.find(regex, end)

    # build extra selections (normal + active)
    for i, (start, end) in enumerate(self._search_matches):
        extra = QTextEditExtraSelectionStub(start, end, fmt)
        extra_selections.append(extra.toExtraSelection(self.text_edit.document()))

    # if we have matches, mark the active match with a distinct color
    if self._search_matches:
        active_fmt = QTextCharFormat(fmt)
        try:
            active_color = QColor(self.STYLES['DarkTheme']['ActiveHighlightColor'])
        except Exception:
            active_color = QColor('#FFD27A')
        active_fmt.setBackground(active_color)

        # create active selection and append so it's drawn on top
        active_start, active_end = self._search_matches[self._search_current] if self._search_current >= 0 else self._search_matches[0]
        active_extra = QTextEditExtraSelectionStub(active_start, active_end, active_fmt)
        extra_selections.append(active_extra.toExtraSelection(self.text_edit.document()))

    self.text_edit.setExtraSelections(extra_selections)
    total = len(self._search_matches)
    if total > 0:
        self._search_current = 0
        _scroll_to_match(self, 0)
        self.search_count_label.setText(f"1/{total}")
    else:
        self.search_count_label.setText("0/0")


class QTextEditExtraSelectionStub:
    def __init__(self, start, end, fmt: QTextCharFormat):
        self.start = start
        self.end = end
        self.fmt = fmt

    def toExtraSelection(self, document):
        from PyQt5.QtGui import QTextCursor
        from PyQt5.QtWidgets import QTextEdit
        cursor = QTextCursor(document)
        cursor.setPosition(self.start)
        cursor.setPosition(self.end, QTextCursor.KeepAnchor)
        extra = QTextEdit.ExtraSelection()
        extra.cursor = cursor
        extra.format = self.fmt
        return extra


def navigate_search(self, direction: int):
    if not self._search_matches:
        return
    total = len(self._search_matches)
    self._search_current = (self._search_current + direction) % total
    idx = self._search_current
    _scroll_to_match(self, idx)
    self.search_count_label.setText(f"{idx+1}/{total}")
    # refresh highlights so active match color updates
    try:
        # rebuild extra selections quickly by reusing perform_search logic without resetting current
        fmt = QTextCharFormat()
        try:
            hl_color = QColor(self.STYLES['DarkTheme']['HighlightColor'])
        except Exception:
            hl_color = QColor('#444444')
        fmt.setBackground(hl_color)
        fmt.setForeground(QColor(self.STYLES['DarkTheme']['Foreground']))

        extra_selections = []
        for i, (start, end) in enumerate(self._search_matches):
            extra = QTextEditExtraSelectionStub(start, end, fmt)
            extra_selections.append(extra.toExtraSelection(self.text_edit.document()))

        active_fmt = QTextCharFormat(fmt)
        try:
            active_color = QColor(self.STYLES['DarkTheme']['ActiveHighlightColor'])
        except Exception:
            active_color = QColor('#FFD27A')
        active_fmt.setBackground(active_color)
        act_start, act_end = self._search_matches[self._search_current]
        active_extra = QTextEditExtraSelectionStub(act_start, act_end, active_fmt)
        extra_selections.append(active_extra.toExtraSelection(self.text_edit.document()))
        self.text_edit.setExtraSelections(extra_selections)
    except Exception:
        pass


def _scroll_to_match(self, idx: int):
    start, end = self._search_matches[idx]
    from PyQt5.QtGui import QTextCursor
    cursor = QTextCursor(self.text_edit.document())
    cursor.setPosition(start)
    cursor.setPosition(end, QTextCursor.KeepAnchor)
    self.text_edit.setTextCursor(cursor)
    # ensure visible (use ensureCursorVisible for broader compatibility)
    try:
        self.text_edit.ensureCursorVisible()
    except Exception:
        # fallback: attempt centerCursor if available
        try:
            self.text_edit.centerCursor()
        except Exception:
            pass


def show_search(self):
    if not hasattr(self, 'editor_search_widget'):
        return
    self.editor_search_widget.setVisible(True)
    self.editor_search_input.setFocus()
    self.editor_search_input.selectAll()


def hide_search(self):
    if not hasattr(self, 'editor_search_widget'):
        return
    self.editor_search_widget.setVisible(False)
    self._search_matches = []
    self._search_current = -1
    self.text_edit.setExtraSelections([])
