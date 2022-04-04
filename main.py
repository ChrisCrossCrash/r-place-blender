from PIL import Image

if __name__ == "__main__":
    img = Image.open("StarWarsPlace.jpg")
    print(img.format, img.size, img.mode)
    img.show()
