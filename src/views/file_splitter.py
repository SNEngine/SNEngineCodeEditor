"""
File splitting functionality for SNIL Editor
Splits a comprehensive SNIL file into separate files based on '---' separators
"""
import os
import re
from typing import List, Tuple
from PyQt5.QtWidgets import QMessageBox, QFileDialog


def split_snil_file(file_path: str, output_directory: str = None) -> bool:
    """
    Split a comprehensive SNIL file into separate files based on '---' separators.
    
    Args:
        file_path: Path to the input SNIL file to split
        output_directory: Directory where split files will be saved (defaults to input file directory)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Read the input file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split the content based on '---' separators
        sections = content.split('\n---\n')
        
        if output_directory is None:
            output_directory = os.path.dirname(file_path)
        
        # Extract dialogue names and create separate files
        for i, section in enumerate(sections):
            section = section.strip()
            if not section:
                continue
            
            # Extract the dialogue name from the section
            name_match = re.search(r'^name:\s*(.+)', section, re.MULTILINE | re.IGNORECASE)
            if name_match:
                dialogue_name = name_match.group(1).strip()
                # Sanitize the name for use as a filename
                safe_name = "".join(c for c in dialogue_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                if not safe_name:
                    safe_name = f"dialogue_{i+1}"
                
                # Create the output file path
                output_file_path = os.path.join(output_directory, f"{safe_name}.snil")
                
                # Write the section to the output file
                with open(output_file_path, 'w', encoding='utf-8') as output_file:
                    output_file.write(section.strip())
            else:
                # If no name: directive found, use a generic name
                safe_name = f"dialogue_{i+1}"
                output_file_path = os.path.join(output_directory, f"{safe_name}.snil")
                
                with open(output_file_path, 'w', encoding='utf-8') as output_file:
                    output_file.write(section.strip())
        
        return True
        
    except Exception as e:
        print(f"Error splitting SNIL file: {e}")
        return False


def split_current_file_with_dialog(main_window) -> bool:
    """
    Split the currently open file in the editor with a confirmation dialog.
    
    Args:
        main_window: Reference to the main window to access current file and editor content
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Check if there's a current file open
    if not main_window.current_tab or not main_window.current_tab.file_path:
        QMessageBox.warning(main_window, "No File Open", "Please open a SNIL file to split first.")
        return False
    
    # Confirm with the user
    reply = QMessageBox.question(
        main_window,
        "Split File Confirmation",
        f"Are you sure you want to split the current file?\n\nThis will create separate files in the same directory as:\n{os.path.basename(main_window.current_tab.file_path)}",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No
    )
    
    if reply != QMessageBox.Yes:
        return False
    
    # Ask user for output directory (default to current file's directory)
    current_dir = os.path.dirname(main_window.current_tab.file_path)
    output_dir = QFileDialog.getExistingDirectory(
        main_window,
        "Select Output Directory",
        current_dir,
        QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
    )
    
    if not output_dir:
        return False  # User cancelled
    
    # Perform the split
    success = split_snil_file(main_window.current_tab.file_path, output_dir)
    
    if success:
        QMessageBox.information(
            main_window,
            "Split Successful",
            f"File has been successfully split into separate dialogue files in:\n{output_dir}"
        )

        # Reload the file structure to show new files
        main_window.reload_structure(output_dir)
    else:
        QMessageBox.critical(
            main_window,
            "Split Failed",
            "An error occurred while splitting the file. Please check the file format and try again."
        )

    return success