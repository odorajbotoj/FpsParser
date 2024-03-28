from bs4 import BeautifulSoup as BS
import base64

class ImgPacker(object):
    def __init__(self, html: bytes) -> None:
        self.bs = BS(str(html), "html.parser")

    def pack(self) -> None:
        img_all = self.bs.find_all("img")
        for img in img_all:
            img_url = str(img.attrs["src"])
            img_type = img_url.split(".")[-1]
            new_url = "data:image/"
            if img_type == "apng":
                new_url += "apng"
            elif img_type == "avif":
                new_url += "avif"
            elif img_type == "gif":
                new_url += "gif"
            elif img_type in ["jpg", "jpeg", "jfif", "pjpeg", "pjp"]:
                new_url += "jpeg"
            elif img_type == "png":
                new_url += "png"
            elif img_type == "svg":
                new_url += "svg+xml"
            elif img_type == "webp":
                new_url += "webp"
            elif img_type == "bmp":
                new_url += "bmp"
            elif img_type in ["ico", "cur"]:
                new_url += "x-icon"
            elif img_type in ["tif", "tiff"]:
                new_url += "tiff"
            else:
                raise TypeError("Invalid img file type")
            new_url += ";base64,"
            if img_url.startswith("/"):
                img_url = img_url[1:]
            f = open(img_url, "rb")
            new_url += base64.b64encode(f.read()).decode("utf-8")
            f.close()
            img.attrs["src"] = new_url

    def get(self) -> bytes:
        return self.bs.prettify()

if __name__ == "__main__":
    import os
    for file in os.listdir("."):
        if file.split(".")[-1] in ["htm", "html"]:
            try:
                try:
                    os.makedirs("output")
                except FileExistsError:
                    pass
                f = open(file, "r", encoding="utf-8")
                packer = ImgPacker(f.read())
                f.close()
                packer.pack()
                f = open("output/packed-"+file, "w", encoding="utf-8")
                f.write(packer.get())
                f.close()
            except Exception as e:
                print("err: "+file)
                print(e)
                #raise e