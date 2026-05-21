from rembg import remove

with open("./a.jpg", "rb") as i:
    data = i.read()

out = remove(data)

with open("output.png", "wb") as o:
    o.write(out)
