from tkinter import Tk
from gui import FileOrganizerGUI
  # Works if main.py and gui.py are in same folder

if __name__ == "__main__":
    root = Tk()
    app = FileOrganizerGUI(root)
    root.geometry("800x500")
    root.mainloop()
