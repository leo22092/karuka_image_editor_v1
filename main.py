import tkinter as tk
from ui.app import ImageEditorApp

def main():
    root = tk.Tk()
    app = ImageEditorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
