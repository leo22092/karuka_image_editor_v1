
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import os

from core.crop import crop_image
from core.resize import resize_with_constraints
from core.convert import convert_image
from core.bgremove import remove_bg_ai, remove_white_background
from core.rotate import rotate_image


class ImageEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Karuka Image Editor Basic")

        self.image_path = None

        # UI
        tk.Button(root, text="Select Image", command=self.load_image).pack(pady=5)

        self.width_entry = self.create_labeled_input("Width")
        self.height_entry = self.create_labeled_input("Height")
        self.size_entry = self.create_labeled_input("Target KB")

        self.exact_var = tk.IntVar()
        tk.Checkbutton(root, text="Exact Size (Crop)", variable=self.exact_var).pack()

        tk.Button(root, text="Resize", command=self.resize_image).pack(pady=10)
        tk.Button(root, text="Convert to PNG", command=self.convert_png).pack(pady=5)
        tk.Button(root, text="Remove Background", command=self.remove_bg).pack(pady=5)
        tk.Button(root, text="Crop", command=self.crop_selected).pack(pady=5)
        tk.Button(root, text="Rotate Left", command=self.rotate_left).pack(pady=5)
        tk.Button(root, text="Rotate Right", command=self.rotate_right).pack(pady=5)

        self.canvas = tk.Canvas(root, width=500, height=400, bg="gray")
        self.canvas.pack()

        # Crop
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        self.rect = None

        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

    # ---------- Utility ----------

    def get_save_path(self, prefix="output"):
        ext = os.path.splitext(self.image_path)[1]

        path = filedialog.asksaveasfilename(
            defaultextension=ext,
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg"),
                ("PNG", "*.png"),
                ("JPEG", "*.jpg *.jpeg")
            ],
            initialfile=f"{prefix}{ext}"
        )
        return path

    # ---------- Load ----------

    def load_image(self):
        path = filedialog.askopenfilename()
        if not path:
            return

        self.image_path = path
        self.load_image_from_path(path)

    def load_image_from_path(self, path):
        self.img = Image.open(path)

        display_img = self.img.resize((500, 400))
        self.tk_img = ImageTk.PhotoImage(display_img)

        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)

    # ---------- Rotate ----------

    def rotate_left(self):
        if not self.image_path:
            return

        output = self.get_save_path("rotated")
        if not output:
            return

        rotate_image(self.image_path, output, 90)
        self.image_path = output
        self.load_image_from_path(output)

    def rotate_right(self):
        if not self.image_path:
            return

        output = self.get_save_path("rotated")
        if not output:
            return

        rotate_image(self.image_path, output, -90)
        self.image_path = output
        self.load_image_from_path(output)

    # ---------- Resize ----------

    def resize_image(self):
        if not self.image_path:
            return

        try:
            w = int(self.width_entry.get())
            h = int(self.height_entry.get())
            size = int(self.size_entry.get())
        except ValueError:
            print("Invalid input")
            return

        exact = bool(self.exact_var.get())

        output = self.get_save_path("resized")
        if not output:
            return

        resize_with_constraints(self.image_path, output, w, h, size, exact)
        self.load_image_from_path(output)
        print(f"Saved: {output}")

    # ---------- Crop ----------

    def crop_selected(self):
        if not self.image_path or self.start_x is None:
            return

        img_w, img_h = self.img.size
        canvas_w, canvas_h = 500, 400

        scale_x = img_w / canvas_w
        scale_y = img_h / canvas_h

        left = int(min(self.start_x, self.end_x) * scale_x)
        top = int(min(self.start_y, self.end_y) * scale_y)
        right = int(max(self.start_x, self.end_x) * scale_x)
        bottom = int(max(self.start_y, self.end_y) * scale_y)

        output = self.get_save_path("cropped")
        if not output:
            return

        crop_image(self.image_path, output, left, top, right, bottom)
        self.load_image_from_path(output)
        print(f"Cropped saved: {output}")

    # ---------- Convert ----------

    def convert_png(self):
        if not self.image_path:
            return

        output = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png")],
            initialfile="converted.png"
        )

        if not output:
            return

        convert_image(self.image_path, output, "PNG")
        self.load_image_from_path(output)
        print(f"Converted: {output}")

    # ---------- Background ----------

    def remove_bg(self):
        if not self.image_path:
            return

        output = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png")],
            initialfile="bg_removed.png"
        )

        if not output:
            return

        remove_bg_ai(self.image_path, output)
        self.load_image_from_path(output)
        print(f"Background removed: {output}")

    # ---------- Mouse (Crop UI) ----------

    def create_labeled_input(self, label):
        frame = tk.Frame(self.root)
        frame.pack()

        tk.Label(frame, text=label).pack(side="left")
        entry = tk.Entry(frame)
        entry.pack(side="right")

        return entry

    def on_mouse_down(self, event):
        self.start_x = event.x
        self.start_y = event.y

        if self.rect:
            self.canvas.delete(self.rect)

        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y,
            self.start_x, self.start_y,
            outline="red"
        )

    def on_mouse_drag(self, event):
        cur_x, cur_y = event.x, event.y
        self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_mouse_up(self, event):
        self.end_x = event.x
        self.end_y = event.y


