from PIL import Image

def rotate_image(input_path, output_path, angle):
    img = Image.open(input_path)
    rotated = img.rotate(angle, expand=True)
    rotated.save(output_path)
    return output_path
