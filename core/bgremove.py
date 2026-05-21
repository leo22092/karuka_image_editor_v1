from PIL import Image

def remove_bg_ai(input_path, output_path):
    from rembg import remove

    with open(input_path, 'rb') as i:
        input_data = i.read()

    output_data = remove(input_data)

    with open(output_path, 'wb') as o:
        o.write(output_data)

    print("AI background removed!")
    
def remove_white_background(input_path, output_path, threshold=240):
    img = Image.open(input_path).convert("RGBA")

    data = img.getdata()
    new_data = []

    for pixel in data:
        r, g, b, a = pixel

        # Detect near-white
        if r > threshold and g > threshold and b > threshold:
            new_data.append((255, 255, 255, 0))  # transparent
        else:
            new_data.append(pixel)

    img.putdata(new_data)
    img.save(output_path, "PNG")

    return output_path
