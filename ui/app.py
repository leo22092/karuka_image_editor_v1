import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
from core.crop import crop_image
from core.resize import resize_with_constraints
from core.convert import convert_image
from core.bgremove import remove_bg_ai,remove_white_background
from core.rotate import rotate_image
class ImageEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Karuka Image Editor Basic")

        self.image_path = None

        # UI Elements
        tk.Button(root, text="Select Image", command=self.load_image).pack(pady=5)

        self.width_entry = self.create_labeled_input("Width")
        self.height_entry = self.create_labeled_input("Height")
        self.size_entry = self.create_labeled_input("Target KB")

        self.exact_var = tk.IntVar()
        tk.Checkbutton(root, text="Exact Size (Crop)", variable=self.exact_var).pack()

        tk.Button(root, text="Resize", command=self.resize_image).pack(pady=10)
        tk.Button(root, text="Convert to PNG", command=self.convert_png).pack(pady=5)
        tk.Button(root, text="Remove Background", command=self.remove_bg).pack(pady=5)
        
       # tk.Button(root, text="AI Remove Background", command=self.remove_bg_ai).pack(pady=5)
        tk.Button(root, text="Crop", command=self.crop_selected).pack(pady=5)
        tk.Button(root, text="Rotate Left", command=self.rotate_left).pack(pady=5)
        tk.Button(root, text="Rotate Right", command=self.rotate_right).pack(pady=5)
        self.canvas = tk.Canvas(root, width=500, height=400, bg="gray")
        self.canvas.pack()
        #crop
        self.start_x = None
        self.start_y = None
        self.rect = None
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        
        
        
        
        
    def load_image(self):
        path = filedialog.askopenfilename()
        if not path:
            return

        self.image_path = path
        self.load_image_from_path(path)
    
    
    
    
    def load_image_from_path(self, path):
        from PIL import Image, ImageTk

        self.img = Image.open(path)

        # Resize for display (not modifying original)
        display_img = self.img.resize((500, 400))

        self.tk_img = ImageTk.PhotoImage(display_img)

        self.canvas.delete("all")  # clear old image
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)

        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)
        
        #ROTATAE
    def rotate_left(self):
        if not self.image_path:
            return

        output = "rotated.jpg"
        rotate_image(self.image_path, output, 90)

        self.image_path = output
        self.load_image_from_path(output)


    def rotate_right(self):
        if not self.image_path:
            return

        output = "rotated.jpg"
        rotate_image(self.image_path, output, -90)

        self.image_path = output
        self.load_image_from_path(output)
        
        
        
        
        
        
        
        
    def create_labeled_input(self, label):
        frame = tk.Frame(self.root)
        frame.pack()

        tk.Label(frame, text=label).pack(side="left")
        entry = tk.Entry(frame)
        entry.pack(side="right")

        return entry

#    def load_image(self):
#        self.image_path = filedialog.askopenfilename()
    def on_mouse_down(self, event):
        self.start_x = event.x
        self.start_y = event.y

        if self.rect:
            self.canvas.delete(self.rect)

        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="red"
        )


    def on_mouse_drag(self, event):
        cur_x, cur_y = event.x, event.y

        self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)


    def on_mouse_up(self, event):
        self.end_x = event.x
        self.end_y = event.y
        
    def resize_image(self):
        if not self.image_path:
            return

        w = int(self.width_entry.get())
        h = int(self.height_entry.get())
        size = int(self.size_entry.get())
        exact = bool(self.exact_var.get())

        resize_with_constraints(
            self.image_path,
            "resized.jpg",
            w, h, size, exact
        )
        self.load_image_from_path("resized.jpg")
        print("Saved as output.jpg")
        
    def crop_selected(self):
        if not self.image_path:
            return

    # Convert canvas coords → real image coords
        img_w, img_h = self.img.size

        canvas_w = 500
        canvas_h = 400

        scale_x = img_w / canvas_w
        scale_y = img_h / canvas_h

        left = int(min(self.start_x, self.end_x) * scale_x)
        top = int(min(self.start_y, self.end_y) * scale_y)
        right = int(max(self.start_x, self.end_x) * scale_x)
        bottom = int(max(self.start_y, self.end_y) * scale_y)

        crop_image(self.image_path, "cropped.jpg", left, top, right, bottom)
        
        
        self.load_image_from_path("cropped.jpg")
        print("Cropped saved as cropped.jpg")        
    def convert_png(self):
        if not self.image_path:
            return

        convert_image(self.image_path, "output.png", "PNG")
        print("Converted to PNG")


    def remove_bg(self):
        if not self.image_path:
            return

      #  remove_white_background(self.image_path, "output.png")
        remove_bg_ai(self.image_path, "bgremoved.png")
        self.load_image_from_path("bgremoved.png")
        print("Background removed (PNG)")
        
        
        
