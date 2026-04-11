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

    if exact:
        img = resize_exact(img, max_width, max_height)
    else:
        img.thumbnail((max_width, max_height), Image.LANCZOS)

    low, high = 10, 95
    best_quality = low
    best_diff = float("inf")

    for _ in range(8):  # limit iterations (stable + fast)
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

    return output_path
