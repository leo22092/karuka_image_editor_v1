from PIL import Image
import os

from PIL import Image
import os

from PIL import Image
import os
def resize_exact(img, target_w, target_h):
    original_w, original_h = img.size

    scale = max(target_w / original_w, target_h / original_h)
    new_w = int(original_w * scale)
    new_h = int(original_h * scale)

    img = img.resize((new_w, new_h), Image.LANCZOS)

    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    right = left + target_w
    bottom = top + target_h

    return img.crop((left, top, right, bottom))
def resize_with_constraints(input_path, output_path, max_width, max_height, target_kb, exact):
    img = Image.open(input_path)

    # 👇 Choose mode
    if exact:
        img = resize_exact(img, max_width, max_height)
    else:
        img.thumbnail((max_width, max_height), Image.LANCZOS)

    low, high = 10, 95
    best_quality = low
    best_diff = float("inf")

    while low <= high:
        mid = (low + high) // 2
        img.save(output_path, quality=mid, optimize=True)

        size_kb = os.path.getsize(output_path) / 1024
        diff = abs(size_kb - target_kb)

        if diff < best_diff:
            best_diff = diff
            best_quality = mid

        if size_kb > target_kb:
            high = mid - 1
        else:
            low = mid + 1

    img.save(output_path, quality=best_quality, optimize=True)

    final_size = os.path.getsize(output_path) / 1024
    print(f"Done → {final_size:.2f} KB | Q={best_quality} | Size={img.size}")

def crop_image(input_path, output_path, left, top, right, bottom):
    img = Image.open(input_path)
    cropped = img.crop((left, top, right, bottom))
    cropped.save(output_path)
    print("Cropped image saved")


def rotate_image(input_path, output_path, angle):
    img = Image.open(input_path)
    rotated = img.rotate(angle, expand=True)
    rotated.save(output_path)
    print("Rotated image saved")


if __name__ == "__main__":
    print("Basic Image Editor")

    choice = input("1.Resize 2.Crop 3.Rotate: ")
    if choice == "1":
    	path = input("Image path: ")

    	max_w = int(input("Max width: "))
    	max_h = int(input("Max height: "))
    	target = int(input("Target size (KB): "))

    	exact_choice = input("Exact size? (y/n): ")

    	exact = True if exact_choice.lower() == 'y' else False

    	resize_with_constraints(path, "output.jpg", max_w, max_h, target, exact)
    elif choice == "2":
        path = input("Image path: ")
        l = int(input("Left: "))
        t = int(input("Top: "))
        r = int(input("Right: "))
        b = int(input("Bottom: "))
        crop_image(path, "output.jpg", l, t, r, b)

    elif choice == "3":
        path = input("Image path: ")
        angle = int(input("Angle (90/180/270): "))
        rotate_image(path, "output.jpg", angle)
