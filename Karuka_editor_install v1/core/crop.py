from PIL import Image

def crop_image(input_path, output_path, left, top, right, bottom):
    img = Image.open(input_path)
    cropped = img.crop((left, top, right, bottom))
    cropped.save(output_path)
    return output_path
