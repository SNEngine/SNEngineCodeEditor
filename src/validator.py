# src/validator.py
import os
from typing import Dict, Any, List

class StructureValidator:
    """
    Class for validating the minimum required structure of a SNIL folder.
    """

    def validate_structure(self, snil_structure: Dict[str, Any]) -> bool:
        """
        Checks if the SNIL structure is valid.

        Args:
            snil_structure: Dictionary obtained from FileService,
                            containing 'root_path' and 'structure'.

        Returns:
            True if the structure is valid, False otherwise.
        """
        root_path_normalized = snil_structure.get('root_path')
        structure_map = snil_structure.get('structure', {})

        if not root_path_normalized:
            return False

        # The structure is valid if there's at least a root path and some structure
        # SNIL doesn't require specific files, so just check if structure exists
        if not structure_map:
            self.last_error = "No files found in the selected directory"
            return False

        self.last_error = ""
        return True

    def get_last_error(self) -> str:
        """Returns the last validation error message."""
        return getattr(self, 'last_error', "")