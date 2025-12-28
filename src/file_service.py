import os
from typing import Dict, Any

class FileService:
    def normalize_path(self, path: str) -> str:
        if not path: return ""
        return os.path.normpath(path).lower()

    def add_folder_recursive(self, folder_path: str, structure: dict):
        normalized_path = self.normalize_path(folder_path)
        snil_files = []
        try:
            for file_name in os.listdir(folder_path):
                full_path = os.path.join(folder_path, file_name)
                # Only look for .snil files
                if os.path.isfile(full_path) and file_name.lower().endswith('.snil'):
                    snil_files.append(file_name)
        except OSError:
            pass

        structure[normalized_path] = sorted(snil_files)

        try:
            for item_name in os.listdir(folder_path):
                full_path = os.path.join(folder_path, item_name)
                if os.path.isdir(full_path):
                    self.add_folder_recursive(full_path, structure)
        except OSError:
            pass

    def get_file_structure_from_path(self, folder_path: str) -> dict:
        normalized_root = self.normalize_path(folder_path)
        structure = {}
        if os.path.isdir(folder_path):
            self.add_folder_recursive(folder_path, structure)
        return {'root_path': normalized_root, 'structure': structure}

    def has_snil_files_recursive(self, folder_path: str) -> bool:
        """Check if a folder or any of its subfolders contains .snil or .asset files (excluding .cs.snil files)."""
        try:
            # Limit the search depth to prevent long scans
            for root, dirs, files in os.walk(folder_path):
                # Limit depth to prevent long searches - only go 3 levels deep
                if root[len(folder_path):].count(os.sep) > 3:  # Limit to 3 levels deep
                    dirs[:] = []  # Don't recurse deeper
                    continue

                for file in files:
                    # Include .snil and .asset files, but exclude .cs.snil files
                    if file.lower().endswith(('.snil', '.asset')) and not file.lower().endswith('.cs.snil'):
                        return True
        except PermissionError:
            # Skip folders we don't have permission to access
            pass
        return False