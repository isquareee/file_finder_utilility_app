# file_logic.py

import os
import re
import shutil
import hashlib
from config import FILE_CATEGORIES, REGEX_RULES
from tkinter import messagebox
from typing import Dict, List, Tuple, Optional, Callable

# Stores (src, dst) for undo operations
# We now store (src, dst, success_flag)
undo_stack = []

def compute_file_hash(filepath: str, chunk_size: int = 8192) -> str:
    """Compute SHA-256 hash of a file in chunks to handle large files efficiently."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def find_duplicates(files: List[str]) -> Dict[str, List[str]]:
    """Find duplicate files by comparing their SHA-256 hashes.
    Returns a dict mapping hash -> list of file paths that share that hash."""
    hashes: Dict[str, List[str]] = {}
    
    for filepath in files:
        try:
            file_hash = compute_file_hash(filepath)
            if file_hash in hashes:
                hashes[file_hash].append(filepath)
            else:
                hashes[file_hash] = [filepath]
        except (PermissionError, FileNotFoundError) as e:
            messagebox.showwarning("Hash Error", 
                f"Could not check {os.path.basename(filepath)} for duplicates: {str(e)}")
    
    # Return only entries with duplicates (len > 1)
    return {h: paths for h, paths in hashes.items() if len(paths) > 1}

def categorize_file(filename):
    # First try extension-based categorization
    _, ext = os.path.splitext(filename.lower())
    for category, extensions in FILE_CATEGORIES.items():
        if ext in extensions:
            return category
    
    # Then try regex-based rules if no extension match
    name = os.path.basename(filename)
    for category, patterns in REGEX_RULES.items():
        for pattern in patterns:
            if re.search(pattern, name):
                return category
    
    return "Others"

def scan_directory(path: str) -> List[Tuple[str, str]]:
    """Scan directory for files to organize. Detects duplicates and warns the user.
    Returns list of (source_path, destination_path) tuples."""
    proposed_moves = []
    all_files = []  # Collect all files first for duplicate detection
    
    # os.walk can raise PermissionError, handle it gracefully
    try:
        for root, _, files in os.walk(path):
            for filename in files:
                old_path = os.path.join(root, filename)
                all_files.append(old_path)
        
        # Find duplicates before proposing moves
        duplicates = find_duplicates(all_files)
        if duplicates:
            # Format duplicate information for the message box
            msg = "Found duplicate files:\n\n"
            for hash_val, file_list in duplicates.items():
                msg += f"The following files are identical:\n"
                for f in file_list:
                    msg += f"  - {os.path.relpath(f, path)}\n"
                msg += "\n"
            messagebox.showwarning("Duplicates Found", msg)
        
        # Now propose moves for all files (including duplicates)
        for filepath in all_files:
            category = categorize_file(filepath)
            filename = os.path.basename(filepath)
            new_path = os.path.join(path, category, filename)
            
            if filepath != new_path:
                proposed_moves.append((filepath, new_path))
        
        return proposed_moves
        
    except PermissionError:
        messagebox.showerror("Error", f"Permission denied to scan: {path}. Please check your access rights.")
        return []
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred during scanning: {e}")
        return []


def move_files(moves, progress_callback=None, dry_run=False):
    total_moves = len(moves)
    successful_moves = 0
    
    for i, (old, new) in enumerate(moves):
        # 1. Error Handling for Move Operation
        try:
            if not dry_run:
                os.makedirs(os.path.dirname(new), exist_ok=True)
                shutil.move(old, new)
                undo_stack.append((new, old, True))
                successful_moves += 1
            else:
                # In dry-run mode, just verify we could do the operation
                if not os.access(os.path.dirname(old), os.R_OK):
                    raise PermissionError(f"No read permission for {old}")
                if os.path.exists(new):
                    messagebox.showwarning("Dry Run", f"File would be overwritten: {new}")
                successful_moves += 1
        except PermissionError:
            # File or folder is locked or permission is denied
            messagebox.showwarning("Permission Error", f"Skipping file: Permission denied to move {os.path.basename(old)}")
            undo_stack.append((new, old, False)) # Mark as failed/skipped
        except FileNotFoundError:
            # Source file was deleted between scan and move
            messagebox.showwarning("File Not Found", f"Skipping file: Source not found for {os.path.basename(old)}")
            undo_stack.append((new, old, False))
        except Exception as e:
            messagebox.showerror("Move Error", f"Failed to move {os.path.basename(old)}: {e}")
            undo_stack.append((new, old, False))
        
        # 2. Progress Bar Update
        if progress_callback:
            progress_callback(i + 1, total_moves)
            
    return successful_moves

def undo_last_operation():
    if not undo_stack:
        messagebox.showinfo("Undo", "No actions to undo")
        return

    # Only pop and reverse the successful moves from the last batch
    moves_to_undo = []
    # Identify the last *batch* of successful moves
    temp_stack = []
    while undo_stack:
        src, dst, success = undo_stack.pop()
        temp_stack.append((src, dst, success))
        if success:
            moves_to_undo.append((src, dst))
    
    # Push back any moves that were not part of the current undo batch (i.e., failed moves)
    # The undo stack will be reset in this simpler implementation, as we assume all moves
    # executed together form one single operation.
    
    if not moves_to_undo:
        messagebox.showinfo("Undo", "The last batch of operations had no successful moves to undo.")
        return

    # Execute the undo moves
    failed_undone_moves = 0
    for src, dst in reversed(moves_to_undo): # Undo in reverse order of operation
        # 3. Error Handling for Undo Operation
        try:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(src, dst)
        except PermissionError:
            messagebox.showwarning("Permission Error", f"Failed to undo: Permission denied to move {os.path.basename(src)} back.")
            failed_undone_moves += 1
        except FileNotFoundError:
            messagebox.showwarning("File Not Found", f"Failed to undo: Source file {os.path.basename(src)} not found (may have been manually moved).")
            failed_undone_moves += 1
        except Exception as e:
            messagebox.showerror("Undo Error", f"Failed to undo {os.path.basename(src)}: {e}")
            failed_undone_moves += 1

    if failed_undone_moves == 0:
        messagebox.showinfo("Undo", "Last operation undone successfully!")
    else:
        messagebox.showwarning("Undo Complete", f"Last operation undone, but {failed_undone_moves} file(s) failed to move back.")