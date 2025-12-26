# src/models.py
import os
import collections
from typing import Any, Dict # <-- FIXED: Import necessary types!

# -------------------------------------------------------------------
# 1. SNILTab (Tab Model)
# -------------------------------------------------------------------

class SNILTab:
    """
    Model for an editor tab.
    Corresponds to the SNILTab class from C# (using Python lists as stacks).
    """
    def __init__(self, file_path: str, snil_text: str):
        self.file_path = file_path
        self._snil_text = snil_text
        self.is_dirty = False
        # Use a list as a stack. Unlike C# Stack<T>,
        # here we store the initial text in the stack
        self.undo_stack = [snil_text]
        self.redo_stack = []

    @property
    def snil_text(self):
        return self._snil_text

    @snil_text.setter
    def snil_text(self, new_text):
        """Simple logic for marking 'dirty'."""
        if self._snil_text != new_text:
            self.is_dirty = True
        self._snil_text = new_text


