from PIL import Image

def convert_image(input_path, output_path, format):
    img = Image.open(input_path)

    # Handle JPG (no transparency)
    if format.lower() in ["jpg", "jpeg"]:
        img = img.convert("RGB")

    img.save(output_path, format=format.upper())

    return output_path
