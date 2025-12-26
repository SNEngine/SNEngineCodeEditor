import unittest
import sys
import os
from PyQt5.QtWidgets import QApplication

# Add src to path to import CodeEditor
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from views.code_editor import CodeEditor

class TestFolding(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    def test_name_block_and_if_show_variant_folding(self):
        editor = CodeEditor(styles={'DarkTheme': {}}, settings_manager=None)
        sample = """name: TestIfShowVariant
Start
If Show Variant
Variants:
Option A
Option B
True:
Jump To SecondDialogue
Nagatoro s
False:
End
endif


---

# Another dialogue target used by Jump To
name: SecondDialogue
Start
Nagatoro says (Second dialogue reached)
End
"""
        editor.setPlainText(sample)
        # Force recompute
        editor.compute_fold_ranges()

        # Find line numbers
        lines = sample.splitlines()
        name1_index = next(i for i, l in enumerate(lines) if l.strip().lower().startswith('name: testifshowvariant'))
        name2_index = next(i for i, l in enumerate(lines) if l.strip().lower().startswith('name: seconddialogue'))
        if_index = next(i for i, l in enumerate(lines) if l.strip().lower().startswith('if show variant'))
        endif_index = next(i for i, l in enumerate(lines) if l.strip().lower().startswith('endif'))

        # The name1 fold range should exist and include the 'endif' line
        self.assertIn(name1_index, editor._fold_ranges)
        self.assertGreaterEqual(editor._fold_ranges[name1_index], endif_index)

        # The If Show Variant fold range should exist from if_index to endif_index
        self.assertIn(if_index, editor._fold_ranges)
        self.assertEqual(editor._fold_ranges[if_index], endif_index)

        # The second name should also have a fold range (it contains Start..End)
        self.assertIn(name2_index, editor._fold_ranges)
        # Its end should be after its start
        self.assertGreater(editor._fold_ranges[name2_index], name2_index)

if __name__ == '__main__':
    unittest.main()
