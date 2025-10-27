# gui.py

from tkinter import *
from tkinter import ttk, filedialog, messagebox
from file_logic import scan_directory, move_files, undo_last_operation
import os # Added for path basename/dirname

class FileOrganizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("File Organizer Utility")

        self.selected_dir = StringVar()
        self.proposed_moves = []
        self.checked_moves = {} # Stores Treeview Item ID -> (old_path, new_path) for checked items

        self.build_ui()

    def build_ui(self):
        # Directory Frame
        dir_frm = Frame(self.root)
        dir_frm.pack(pady=10)

        Entry(dir_frm, textvariable=self.selected_dir, width=60).pack(side=LEFT, padx=5)
        Button(dir_frm, text="Browse", command=self.choose_directory).pack(side=LEFT)

        # Treeview (Preview Table)
        self.tree = ttk.Treeview(self.root, columns=("Checked", "File", "To", "Category"), show="headings")
        self.tree.column("Checked", width=60, stretch=NO, anchor=CENTER)
        self.tree.column("File", width=250, stretch=YES)
        self.tree.column("To", width=300, stretch=YES)
        self.tree.column("Category", width=100, stretch=NO, anchor=CENTER)

        self.tree.heading("Checked", text="Move", command=self.toggle_all_checks)
        self.tree.heading("File", text="File Name")
        self.tree.heading("To", text="New Path")
        self.tree.heading("Category", text="Category")
        
        self.tree.bind("<Button-1>", self.on_tree_click) # Handle checkbox clicks
        
        self.tree.pack(fill=BOTH, expand=True, padx=10, pady=5)

        # Progress Bar
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=200, mode="determinate")
        self.progress.pack(fill=X, padx=10)
        self.progress_label = Label(self.root, text="")
        self.progress_label.pack(pady=(2, 10))

        # Button Frame
        btn_frame = Frame(self.root)
        btn_frame.pack(pady=10)

        Button(btn_frame, text="Scan Directory", command=self.preview_moves).pack(side=LEFT, padx=10)
        Button(btn_frame, text="Organize Checked Files", command=self.execute_moves).pack(side=LEFT, padx=10)
        Button(btn_frame, text="Undo Last Operation", command=undo_last_operation).pack(side=LEFT, padx=10)

    # --- UI Logic ---
    
    def on_tree_click(self, event):
        """Toggles the checkbox when the user clicks anywhere on a row."""
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return

        current_values = self.tree.item(item_id, 'values')
        if not current_values:
            return

        is_checked = current_values[0] == "✔"
        
        new_values = list(current_values)
        if is_checked:
            new_values[0] = "☐"
            if item_id in self.checked_moves:
                del self.checked_moves[item_id]
        else:
            new_values[0] = "✔"
            # The proposed_moves list is indexed by the Treeview item_id for convenience
            old_path = current_values[1] # Path is stored in the File column for retrieval
            new_path = current_values[2]
            self.checked_moves[item_id] = (os.path.join(self.selected_dir.get(), old_path), new_path)

        self.tree.item(item_id, values=new_values)

    def toggle_all_checks(self):
        """Toggles all checkboxes in the Treeview."""
        all_checked = all(self.tree.item(item, 'values')[0] == "✔" for item in self.tree.get_children())
        
        for item_id in self.tree.get_children():
            current_values = list(self.tree.item(item_id, 'values'))
            old_path, new_path = current_values[1], current_values[2] # Actual paths are needed for logic

            if all_checked:
                # Uncheck all
                current_values[0] = "☐"
                if item_id in self.checked_moves:
                    del self.checked_moves[item_id]
            else:
                # Check all
                current_values[0] = "✔"
                # Store the absolute paths
                full_old_path = os.path.join(os.path.dirname(new_path), old_path)
                self.checked_moves[item_id] = (full_old_path, new_path)
            
            self.tree.item(item_id, values=current_values)

    # --- File Logic Integration ---
    
    def choose_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.selected_dir.set(directory)
            self.tree.delete(*self.tree.get_children())
            self.checked_moves.clear()

    def preview_moves(self):
        directory = self.selected_dir.get()
        if not directory:
            messagebox.showerror("Error", "Choose a folder first!")
            return

        self.tree.delete(*self.tree.get_children())
        self.checked_moves.clear()
        
        # Reset progress bar/label
        self.progress['value'] = 0
        self.progress_label.config(text="Scanning...")

        self.proposed_moves = scan_directory(directory)
        
        if not self.proposed_moves:
            self.progress_label.config(text="Scan complete. No files need organizing.")
            return

        for old, new in self.proposed_moves:
            filename = os.path.basename(old)
            category = os.path.basename(os.path.dirname(new))
            
            # The tree will display: (Checked, File Name, New Path, Category)
            # Checkbox starts checked by default
            item_id = self.tree.insert("", END, values=("✔", filename, new, category))
            
            # Store the full move tuple for checked items
            self.checked_moves[item_id] = (old, new)

        self.progress_label.config(text=f"Scan complete. Found {len(self.proposed_moves)} files to organize.")


    def update_progress(self, current, total):
        """Callback function to update the progress bar."""
        percent = (current / total) * 100
        self.progress['value'] = percent
        self.progress_label.config(text=f"Organizing file {current} of {total} ({percent:.0f}%)")
        self.root.update_idletasks() # Force UI refresh

    def execute_moves(self):
        moves_to_execute = list(self.checked_moves.values())
        
        if not moves_to_execute:
            messagebox.showerror("Error", "No files selected to organize!")
            return

        # Disable buttons during operation
        for child in self.root.winfo_children():
            if isinstance(child, Frame):
                for btn in child.winfo_children():
                    if isinstance(btn, Button):
                        btn.config(state=DISABLED)

        self.progress_label.config(text=f"Starting organization of {len(moves_to_execute)} files...")
        self.progress['maximum'] = len(moves_to_execute)
        
        successful_count = move_files(moves_to_execute, self.update_progress)
        
        # Re-enable buttons
        for child in self.root.winfo_children():
            if isinstance(child, Frame):
                for btn in child.winfo_children():
                    if isinstance(btn, Button):
                        btn.config(state=NORMAL)
        
        self.progress['value'] = 100
        
        if successful_count == len(moves_to_execute):
            messagebox.showinfo("Success", "All selected files organized successfully!")
        else:
            messagebox.showwarning("Partial Success", f"Organized {successful_count} out of {len(moves_to_execute)} selected files. Check console for errors (e.g., permission issues).")

        # Clear preview and checked items
        self.tree.delete(*self.tree.get_children())
        self.checked_moves.clear()
        self.progress_label.config(text="Organization complete.")