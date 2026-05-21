from io import BytesIO
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

try:
    from pillow_heif import register_heif_opener
except ImportError:
    HEIC_AVAILABLE = False
else:
    register_heif_opener()
    HEIC_AVAILABLE = True

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp", ".bmp", ".gif", ".tif", ".tiff"}
FILE_TYPES = [
    ("Image files", "*.jpg *.jpeg *.png *.heic *.heif *.webp *.bmp *.gif *.tif *.tiff"),
    ("All files", "*.*"),
]
OUTPUT_FORMATS = ("JPEG", "JPG", "PNG", "HEIC")


class ImageEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Karuka Image Editor")
        self.root.minsize(1000, 700)
        self.maximize_window()

        self.image_path = None
        self.current_folder = Path.cwd()
        self.downloads_folder = self.get_downloads_folder()
        self.img = None
        self.original_name = None
        self.output_format = "PNG"
        self.target_kb = None
        self.has_unsaved_changes = False
        self.tk_img = None
        self.display_bounds = (0, 0, 1, 1)
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        self.rect = None

        self._configure_style()
        self._build_ui()
        self.refresh_file_list()

    def maximize_window(self):
        try:
            self.root.state("zoomed")
        except tk.TclError:
            width = self.root.winfo_screenwidth()
            height = self.root.winfo_screenheight()
            self.root.geometry(f"{width}x{height}+0+0")

    def _configure_style(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(".", font=("Segoe UI", 10), background="#f4f1ec", foreground="#222222")
        style.configure("App.TFrame", background="#f4f1ec")
        style.configure("Panel.TFrame", background="#ffffff", relief="flat")
        style.configure("Header.TLabel", background="#ffffff", foreground="#111111", font=("Segoe UI", 16, "bold"))
        style.configure("Subtle.TLabel", background="#ffffff", foreground="#6d6a65")
        style.configure("Canvas.TFrame", background="#1f2227")
        style.configure("TButton", padding=(12, 7), background="#ebe5dc", foreground="#1f1f1f")
        style.map("TButton", background=[("active", "#ded6ca")])
        style.configure("Accent.TButton", background="#1f6f68", foreground="#ffffff")
        style.map("Accent.TButton", background=[("active", "#195d57")], foreground=[("active", "#ffffff")])
        style.configure("Danger.TButton", background="#8f3c35", foreground="#ffffff")
        style.map("Danger.TButton", background=[("active", "#77312c")], foreground=[("active", "#ffffff")])
        style.configure("TEntry", padding=6)
        style.configure("TCheckbutton", background="#ffffff", foreground="#222222")

    def _build_ui(self):
        self.root.configure(bg="#f4f1ec")

        main = ttk.Frame(self.root, style="App.TFrame", padding=16)
        main.pack(fill="both", expand=True)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=1)

        browser = ttk.Frame(main, style="Panel.TFrame", padding=16)
        browser.grid(row=0, column=0, sticky="ns", padx=(0, 14))
        browser.rowconfigure(4, weight=1)

        ttk.Label(browser, text="Library", style="Header.TLabel").grid(row=0, column=0, columnspan=2, sticky="w")
        self.folder_label = ttk.Label(browser, text="", style="Subtle.TLabel", width=28)
        self.folder_label.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4, 12))

        ttk.Button(browser, text="Open Image", style="Accent.TButton", command=self.load_image).grid(
            row=2, column=0, sticky="ew", pady=(0, 8)
        )
        ttk.Button(browser, text="Choose Folder", command=self.choose_folder).grid(
            row=2, column=1, sticky="ew", padx=(8, 0), pady=(0, 8)
        )

        search_frame = ttk.Frame(browser, style="Panel.TFrame")
        search_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        search_frame.columnconfigure(0, weight=1)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh_file_list())
        ttk.Entry(search_frame, textvariable=self.search_var).grid(row=0, column=0, sticky="ew")

        list_frame = ttk.Frame(browser, style="Panel.TFrame")
        list_frame.grid(row=4, column=0, columnspan=2, sticky="nsew")
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
        self.file_list = tk.Listbox(
            list_frame,
            activestyle="none",
            bd=0,
            highlightthickness=1,
            highlightbackground="#ded8cf",
            selectbackground="#1f6f68",
            selectforeground="#ffffff",
            font=("Segoe UI", 10),
        )
        self.file_list.grid(row=0, column=0, sticky="nsew")
        self.file_list.bind("<<ListboxSelect>>", self.on_file_selected)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.file_list.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.file_list.configure(yscrollcommand=scrollbar.set)

        self.file_count_label = ttk.Label(browser, text="", style="Subtle.TLabel")
        self.file_count_label.grid(row=5, column=0, columnspan=2, sticky="w", pady=(10, 0))

        workspace = ttk.Frame(main, style="App.TFrame")
        workspace.grid(row=0, column=1, sticky="nsew")
        workspace.columnconfigure(0, weight=1)
        workspace.rowconfigure(1, weight=1)

        topbar = ttk.Frame(workspace, style="Panel.TFrame", padding=(16, 12))
        topbar.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        topbar.columnconfigure(0, weight=1)
        ttk.Label(topbar, text="Karuka Image Editor", style="Header.TLabel").grid(row=0, column=0, sticky="w")
        self.title_label = ttk.Label(topbar, text="No image selected", style="Subtle.TLabel")
        self.title_label.grid(row=1, column=0, sticky="w", pady=(4, 0))
        self.meta_label = ttk.Label(topbar, text="Choose an image to begin.", style="Subtle.TLabel")
        self.meta_label.grid(row=2, column=0, sticky="w", pady=(3, 0))

        content = ttk.Frame(workspace, style="App.TFrame")
        content.grid(row=1, column=0, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.rowconfigure(0, weight=1)

        preview_frame = ttk.Frame(content, style="Canvas.TFrame", padding=12)
        preview_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        self.canvas = tk.Canvas(preview_frame, bg="#262a31", bd=0, highlightthickness=0, cursor="crosshair")
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.bind("<Configure>", lambda _event: self.render_image())
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.preview_details_var = tk.StringVar(value="No image loaded")
        ttk.Label(preview_frame, textvariable=self.preview_details_var, style="Subtle.TLabel").grid(
            row=1, column=0, sticky="ew", pady=(10, 0)
        )

        controls = ttk.Frame(content, style="Panel.TFrame", padding=16)
        controls.grid(row=0, column=1, sticky="ns")
        controls.columnconfigure(1, weight=1)

        ttk.Label(controls, text="Edit", style="Header.TLabel").grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(controls, text="Edits stay in preview until you save.", style="Subtle.TLabel", wraplength=220).grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(6, 12)
        )
        ttk.Button(controls, text="Save to Downloads", style="Accent.TButton", command=self.save_image).grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=(0, 16)
        )
        ttk.Label(controls, text=f"Destination: {self.downloads_folder}", style="Subtle.TLabel", wraplength=220).grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(0, 12)
        )
        ttk.Label(controls, text="Resize", style="Subtle.TLabel").grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(6, 6)
        )
        self.width_entry = self.create_labeled_input(controls, "Width", 5)
        self.height_entry = self.create_labeled_input(controls, "Height", 6)
        self.size_entry = self.create_labeled_input(controls, "Save target KB", 7)
        self.size_entry.insert(0, "500")

        self.exact_var = tk.IntVar()
        ttk.Checkbutton(controls, text="Exact size crop", variable=self.exact_var).grid(
            row=8, column=0, columnspan=2, sticky="w", pady=(8, 12)
        )
        ttk.Button(controls, text="Resize", style="Accent.TButton", command=self.resize_image).grid(
            row=9, column=0, columnspan=2, sticky="ew"
        )

        ttk.Separator(controls).grid(row=10, column=0, columnspan=2, sticky="ew", pady=18)
        ttk.Button(controls, text="Crop Selection", command=self.crop_selected).grid(
            row=11, column=0, columnspan=2, sticky="ew", pady=(0, 8)
        )
        ttk.Button(controls, text="Rotate Left", command=self.rotate_left).grid(row=12, column=0, sticky="ew")
        ttk.Button(controls, text="Rotate Right", command=self.rotate_right).grid(
            row=12, column=1, sticky="ew", padx=(8, 0)
        )

        ttk.Separator(controls).grid(row=13, column=0, columnspan=2, sticky="ew", pady=18)
        ttk.Label(controls, text="Format", style="Subtle.TLabel").grid(row=14, column=0, sticky="w", pady=(0, 8))
        self.convert_format_var = tk.StringVar(value="PNG")
        ttk.Combobox(
            controls,
            textvariable=self.convert_format_var,
            values=OUTPUT_FORMATS,
            state="readonly",
            width=10,
        ).grid(row=14, column=1, sticky="ew", padx=(8, 0), pady=(0, 8))
        ttk.Button(controls, text="Convert Format", command=self.convert_selected_format).grid(
            row=15, column=0, columnspan=2, sticky="ew", pady=(0, 8)
        )
        ttk.Button(controls, text="Batch Resize / Convert", style="Accent.TButton", command=self.open_batch_dialog).grid(
            row=16, column=0, columnspan=2, sticky="ew"
        )
        ttk.Button(controls, text="Remove Background", style="Danger.TButton", command=self.remove_bg).grid(
            row=17, column=0, columnspan=2, sticky="ew", pady=(8, 0)
        )

        self.status_var = tk.StringVar(value="Ready.")
        status = ttk.Label(workspace, textvariable=self.status_var, style="Subtle.TLabel")
        status.grid(row=2, column=0, sticky="ew", pady=(10, 0))

    def create_labeled_input(self, parent, label, row):
        ttk.Label(parent, text=label, style="Subtle.TLabel").grid(row=row, column=0, sticky="w", pady=4)
        entry = ttk.Entry(parent, width=12)
        entry.grid(row=row, column=1, sticky="ew", pady=4, padx=(8, 0))
        return entry

    def load_image(self):
        path = filedialog.askopenfilename(
            title="Select an image",
            initialdir=self.current_folder,
            filetypes=FILE_TYPES,
        )
        if path:
            self.open_image(Path(path))

    def choose_folder(self):
        folder = filedialog.askdirectory(title="Choose image folder", initialdir=self.current_folder)
        if folder:
            self.current_folder = Path(folder)
            self.refresh_file_list()

    def refresh_file_list(self):
        query = self.search_var.get().lower().strip() if hasattr(self, "search_var") else ""
        self.file_list.delete(0, tk.END)
        self.folder_label.configure(text=str(self.current_folder))

        try:
            files = sorted(
                p for p in self.current_folder.iterdir()
                if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
            )
        except OSError as exc:
            self.status_var.set(f"Could not read folder: {exc}")
            files = []

        if query:
            files = [p for p in files if query in p.name.lower()]

        self.visible_files = files
        for path in files:
            self.file_list.insert(tk.END, path.name)

        self.file_count_label.configure(text=f"{len(files)} image{'s' if len(files) != 1 else ''}")

    def on_file_selected(self, _event):
        selection = self.file_list.curselection()
        if selection:
            self.open_image(self.visible_files[selection[0]])

    def open_image(self, path):
        try:
            loaded = Image.open(path)
            loaded.load()
        except Exception as exc:
            messagebox.showerror("Open image", f"Could not open this image:\n{exc}")
            return

        self.img = loaded.copy()
        self.image_path = str(path)
        self.original_name = path.stem
        self.output_format = self.normalize_format(loaded.format, path.suffix)
        self.target_kb = None
        self.has_unsaved_changes = False
        self.current_folder = path.parent
        self.refresh_file_list()
        self._select_current_in_list(path)
        self.clear_crop()
        self.render_image()
        self.update_metadata(path.name)
        self.status_var.set(f"Opened {path.name}")

    def _select_current_in_list(self, path):
        for index, item in enumerate(self.visible_files):
            if item == path:
                self.file_list.selection_clear(0, tk.END)
                self.file_list.selection_set(index)
                self.file_list.see(index)
                break

    def update_metadata(self, display_name=None):
        if not self.img:
            return
        width, height = self.img.size
        size_kb = self.estimate_current_size_kb()
        name = display_name or self.current_output_name()
        unsaved = "Unsaved preview" if self.has_unsaved_changes else "Original"
        self.title_label.configure(text=name)
        self.meta_label.configure(text=f"{unsaved}  |  {self.output_format}")
        self.preview_details_var.set(f"{width} x {height}px  |  approx {size_kb:.1f} KB  |  {self.output_format}")
        self.width_entry.delete(0, tk.END)
        self.height_entry.delete(0, tk.END)
        self.width_entry.insert(0, str(width))
        self.height_entry.insert(0, str(height))

    def render_image(self):
        if not self.img:
            self.canvas.delete("all")
            self.canvas.create_text(
                max(self.canvas.winfo_width() // 2, 120),
                max(self.canvas.winfo_height() // 2, 120),
                text="Open an image",
                fill="#d6d1c8",
                font=("Segoe UI", 18, "bold"),
            )
            return

        canvas_w = max(self.canvas.winfo_width(), 1)
        canvas_h = max(self.canvas.winfo_height(), 1)
        img_w, img_h = self.img.size
        scale = min(canvas_w / img_w, canvas_h / img_h)
        display_w = max(int(img_w * scale), 1)
        display_h = max(int(img_h * scale), 1)
        offset_x = (canvas_w - display_w) // 2
        offset_y = (canvas_h - display_h) // 2

        display_img = self.img.resize((display_w, display_h), Image.LANCZOS)
        self.tk_img = ImageTk.PhotoImage(display_img)
        self.display_bounds = (offset_x, offset_y, display_w, display_h)

        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 0, canvas_w, canvas_h, fill="#262a31", outline="")
        self.canvas.create_image(offset_x, offset_y, anchor="nw", image=self.tk_img)
        if self.start_x is not None and self.end_x is not None:
            self.rect = self.canvas.create_rectangle(
                self.start_x,
                self.start_y,
                self.end_x,
                self.end_y,
                outline="#f6d365",
                width=2,
            )

    def clear_crop(self):
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        self.rect = None

    def require_image(self):
        if not self.image_path:
            self.status_var.set("Open an image first.")
            return False
        return True

    def get_downloads_folder(self):
        downloads = Path.home() / "Downloads"
        downloads.mkdir(exist_ok=True)
        return downloads

    def normalize_format(self, image_format, suffix):
        if image_format:
            return "JPEG" if image_format.upper() == "JPG" else image_format.upper()
        ext = suffix.lower().lstrip(".")
        if ext in ["jpg", "jpeg"]:
            return "JPEG"
        if ext:
            return ext.upper()
        return "PNG"

    def output_extension(self):
        if self.output_format == "JPEG":
            return ".jpg"
        if self.output_format in ["HEIC", "HEIF"]:
            return ".heic"
        return f".{self.output_format.lower()}"

    def current_output_name(self):
        stem = self.original_name or "edited_image"
        return f"{stem}_edited{self.output_extension()}"

    def output_path(self):
        return self.downloads_folder / self.current_output_name()

    def success_message(self, action, path):
        message = f"✓ {action} saved to Downloads:\n{path.name}"
        self.status_var.set(message.replace("\n", " "))
        messagebox.showinfo("Saved", message)

    def estimate_current_size_kb(self):
        if not self.img:
            return 0
        buffer = BytesIO()
        save_img = self.image_for_save()
        save_kwargs = {}
        if self.output_format == "JPEG":
            save_kwargs = {"quality": self.jpeg_quality(), "optimize": True}
        try:
            save_img.save(buffer, format=self.output_format, **save_kwargs)
            return len(buffer.getvalue()) / 1024
        except Exception:
            width, height = self.img.size
            return width * height * len(self.img.getbands()) / 1024

    def image_for_save(self):
        if self.output_format in ["JPEG", "JPG"] and self.img.mode != "RGB":
            return self.img.convert("RGB")
        return self.img

    def jpeg_quality(self):
        return 85 if self.target_kb else 90

    def apply_preview_change(self, image, action):
        self.img = image.copy()
        self.has_unsaved_changes = True
        self.clear_crop()
        self.render_image()
        self.update_metadata()
        self.status_var.set(f"{action} applied to preview. Click Save to write the file.")

    def rotate_left(self):
        if not self.require_image():
            return
        self.apply_preview_change(self.img.rotate(90, expand=True), "Rotate left")

    def rotate_right(self):
        if not self.require_image():
            return
        self.apply_preview_change(self.img.rotate(-90, expand=True), "Rotate right")

    def on_mouse_down(self, event):
        if not self.img:
            return
        self.start_x, self.start_y = self._clamp_to_image(event.x, event.y)
        self.end_x, self.end_y = self.start_x, self.start_y
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(
            self.start_x,
            self.start_y,
            self.end_x,
            self.end_y,
            outline="#f6d365",
            width=2,
        )

    def on_mouse_drag(self, event):
        if not self.img or self.start_x is None:
            return
        self.end_x, self.end_y = self._clamp_to_image(event.x, event.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, self.end_x, self.end_y)

    def on_mouse_up(self, event):
        if not self.img or self.start_x is None:
            return
        self.end_x, self.end_y = self._clamp_to_image(event.x, event.y)

    def _clamp_to_image(self, x, y):
        offset_x, offset_y, display_w, display_h = self.display_bounds
        return (
            min(max(x, offset_x), offset_x + display_w),
            min(max(y, offset_y), offset_y + display_h),
        )

    def _canvas_to_image_coords(self, x, y):
        offset_x, offset_y, display_w, display_h = self.display_bounds
        img_w, img_h = self.img.size
        return (
            int((x - offset_x) * img_w / display_w),
            int((y - offset_y) * img_h / display_h),
        )

    def resize_image(self):
        if not self.require_image():
            return
        try:
            width = int(self.width_entry.get())
            height = int(self.height_entry.get())
            size = int(self.size_entry.get())
            if width <= 0 or height <= 0 or size <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Resize", "Width, height, and target KB must be positive numbers.")
            return

        if bool(self.exact_var.get()):
            resized = self.resize_exact_preview(self.img, width, height)
        else:
            resized = self.img.copy()
            resized.thumbnail((width, height), Image.LANCZOS)
        self.target_kb = size if self.output_format == "JPEG" else None
        self.apply_preview_change(resized, "Resize")

    def crop_selected(self):
        if not self.require_image():
            return
        if self.start_x is None or self.end_x is None:
            self.status_var.set("Drag on the image to choose a crop area.")
            return

        left, top = self._canvas_to_image_coords(min(self.start_x, self.end_x), min(self.start_y, self.end_y))
        right, bottom = self._canvas_to_image_coords(max(self.start_x, self.end_x), max(self.start_y, self.end_y))

        if right - left < 2 or bottom - top < 2:
            self.status_var.set("Crop area is too small.")
            return

        self.apply_preview_change(self.img.crop((left, top, right, bottom)), "Crop")

    def convert_selected_format(self):
        if not self.require_image():
            return
        selected_format = self.convert_format_var.get()
        if selected_format == "HEIC" and not HEIC_AVAILABLE:
            messagebox.showwarning(
                "Convert format",
                "HEIC output requires the optional HEIC dependency. Install with: python -m pip install \".[heic]\"",
            )
            return

        self.output_format = "JPEG" if selected_format == "JPG" else selected_format
        self.target_kb = None
        if self.output_format == "PNG" and self.img.mode not in ["RGBA", "LA"]:
            self.img = self.img.convert("RGBA")
        elif self.output_format == "JPEG" and self.img.mode != "RGB":
            self.img = self.img.convert("RGB")
        self.has_unsaved_changes = True
        self.render_image()
        self.update_metadata()
        self.status_var.set(f"{selected_format} selected for preview. Click Save to write the file.")

    def convert_png(self):
        if hasattr(self, "convert_format_var"):
            self.convert_format_var.set("PNG")
        self.convert_selected_format()

    def open_batch_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Batch Resize / Convert")
        dialog.transient(self.root)
        dialog.resizable(False, False)
        dialog.configure(bg="#f4f1ec")

        frame = ttk.Frame(dialog, style="Panel.TFrame", padding=16)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(1, weight=1)

        input_var = tk.StringVar(value=str(self.current_folder))
        output_var = tk.StringVar(value=str(self.downloads_folder / "karuka_batch_output"))
        width_var = tk.StringVar(value=self.width_entry.get() or "1024")
        height_var = tk.StringVar(value=self.height_entry.get() or "1024")
        format_var = tk.StringVar(value="JPEG")
        exact_var = tk.IntVar(value=0)

        def choose_input():
            folder = filedialog.askdirectory(title="Choose source folder", initialdir=input_var.get())
            if folder:
                input_var.set(folder)

        def choose_output():
            folder = filedialog.askdirectory(title="Choose output folder", initialdir=output_var.get())
            if folder:
                output_var.set(folder)

        ttk.Label(frame, text="Batch Resize / Convert", style="Header.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 12)
        )
        ttk.Label(frame, text="Source folder", style="Subtle.TLabel").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=input_var, width=46).grid(row=1, column=1, sticky="ew", padx=(8, 8), pady=4)
        ttk.Button(frame, text="Browse", command=choose_input).grid(row=1, column=2, sticky="ew", pady=4)

        ttk.Label(frame, text="Output folder", style="Subtle.TLabel").grid(row=2, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=output_var, width=46).grid(row=2, column=1, sticky="ew", padx=(8, 8), pady=4)
        ttk.Button(frame, text="Browse", command=choose_output).grid(row=2, column=2, sticky="ew", pady=4)

        ttk.Label(frame, text="Width", style="Subtle.TLabel").grid(row=3, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=width_var, width=12).grid(row=3, column=1, sticky="w", padx=(8, 0), pady=4)
        ttk.Label(frame, text="Height", style="Subtle.TLabel").grid(row=4, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=height_var, width=12).grid(row=4, column=1, sticky="w", padx=(8, 0), pady=4)

        ttk.Label(frame, text="Output format", style="Subtle.TLabel").grid(row=5, column=0, sticky="w", pady=4)
        ttk.Combobox(frame, textvariable=format_var, values=OUTPUT_FORMATS, state="readonly", width=10).grid(
            row=5, column=1, sticky="w", padx=(8, 0), pady=4
        )
        ttk.Checkbutton(frame, text="Exact size crop", variable=exact_var).grid(
            row=6, column=1, sticky="w", padx=(8, 0), pady=(6, 12)
        )

        ttk.Button(
            frame,
            text="Start Batch",
            style="Accent.TButton",
            command=lambda: self.run_batch_from_dialog(
                dialog,
                input_var.get(),
                output_var.get(),
                width_var.get(),
                height_var.get(),
                format_var.get(),
                bool(exact_var.get()),
            ),
        ).grid(row=7, column=0, columnspan=3, sticky="ew")

    def run_batch_from_dialog(self, dialog, input_folder, output_folder, width, height, output_format, exact):
        try:
            width = int(width)
            height = int(height)
            if width <= 0 or height <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Batch resize", "Width and height must be positive numbers.", parent=dialog)
            return

        source = Path(input_folder).expanduser()
        destination = Path(output_folder).expanduser()
        if not source.is_dir():
            messagebox.showwarning("Batch resize", "Choose a valid source folder.", parent=dialog)
            return
        if source.resolve() == destination.resolve():
            messagebox.showwarning("Batch resize", "Choose a different output folder.", parent=dialog)
            return
        if output_format == "HEIC" and not HEIC_AVAILABLE:
            messagebox.showwarning(
                "Batch resize",
                "HEIC output requires the optional HEIC dependency. Install with: python -m pip install \".[heic]\"",
                parent=dialog,
            )
            return

        try:
            processed, failed = self.batch_resize_convert(source, destination, width, height, output_format, exact)
        except Exception as exc:
            messagebox.showerror("Batch resize", f"Batch resize failed:\n{exc}", parent=dialog)
            self.status_var.set("Batch resize failed.")
            return

        dialog.destroy()
        self.status_var.set(f"Batch complete. {processed} saved to {destination}. {failed} failed.")
        messagebox.showinfo(
            "Batch complete",
            f"Saved {processed} image{'s' if processed != 1 else ''} to:\n{destination}\n\nFailed: {failed}",
        )

    def batch_resize_convert(self, source, destination, width, height, output_format, exact):
        destination.mkdir(parents=True, exist_ok=True)
        image_paths = sorted(p for p in source.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS)
        processed = 0
        failed = 0

        for path in image_paths:
            try:
                with Image.open(path) as img:
                    img.load()
                    edited = self.resize_exact_preview(img, width, height) if exact else img.copy()
                    if not exact:
                        edited.thumbnail((width, height), Image.LANCZOS)
                    output_path = destination / f"{path.stem}{self.extension_for_format(output_format)}"
                    self.save_converted_image(edited, output_path, output_format)
                    processed += 1
            except Exception:
                failed += 1

        return processed, failed

    def extension_for_format(self, output_format):
        if output_format in ["JPEG", "JPG"]:
            return ".jpg" if output_format == "JPG" else ".jpeg"
        if output_format == "HEIC":
            return ".heic"
        return ".png"

    def save_converted_image(self, image, path, output_format):
        if output_format in ["JPEG", "JPG"]:
            if image.mode != "RGB":
                image = image.convert("RGB")
            image.save(path, format="JPEG", quality=90, optimize=True)
            return
        if output_format == "HEIC":
            image.save(path, format="HEIF", quality=90)
            return
        image.save(path, format="PNG", optimize=True)

    def remove_bg(self):
        if not self.require_image():
            return
        self.status_var.set("Removing background...")
        self.root.update_idletasks()
        try:
            from rembg import remove

            buffer = BytesIO()
            self.img.convert("RGBA").save(buffer, format="PNG")
            output_data = remove(buffer.getvalue())
            removed = Image.open(BytesIO(output_data))
            removed.load()
        except Exception as exc:
            messagebox.showerror("Remove background", f"Background removal failed:\n{exc}")
            self.status_var.set("Background removal failed.")
            return
        self.output_format = "PNG"
        self.target_kb = None
        self.apply_preview_change(removed.convert("RGBA"), "Background removal")

    def resize_exact_preview(self, img, target_w, target_h):
        original_w, original_h = img.size
        scale = max(target_w / original_w, target_h / original_h)
        new_w = int(original_w * scale)
        new_h = int(original_h * scale)
        resized = img.resize((new_w, new_h), Image.LANCZOS)
        left = (new_w - target_w) // 2
        top = (new_h - target_h) // 2
        return resized.crop((left, top, left + target_w, top + target_h))

    def save_image(self):
        if not self.require_image():
            return
        path = self.output_path()
        try:
            save_img = self.image_for_save()
            if self.output_format == "JPEG":
                self.save_jpeg(path, save_img)
            elif self.output_format == "HEIC":
                self.save_converted_image(save_img, path, "HEIC")
            else:
                save_img.save(path, format=self.output_format)
        except Exception as exc:
            messagebox.showerror("Save image", f"Could not save the image:\n{exc}")
            self.status_var.set("Save failed.")
            return
        self.has_unsaved_changes = False
        self.image_path = str(path)
        self.current_folder = path.parent
        self.refresh_file_list()
        self._select_current_in_list(path)
        self.update_metadata(path.name)
        self.success_message("Image", path)

    def save_jpeg(self, path, image):
        if not self.target_kb:
            image.save(path, format="JPEG", quality=90, optimize=True)
            return

        low, high = 10, 95
        best_data = None
        best_diff = float("inf")
        for _ in range(8):
            quality = (low + high) // 2
            buffer = BytesIO()
            image.save(buffer, format="JPEG", quality=quality, optimize=True)
            data = buffer.getvalue()
            size_kb = len(data) / 1024
            diff = abs(size_kb - self.target_kb)
            if diff < best_diff:
                best_diff = diff
                best_data = data
            if size_kb > self.target_kb:
                high = quality - 1
            else:
                low = quality + 1

        path.write_bytes(best_data)
