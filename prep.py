import os
from PIL import Image

files = os.listdir("./inputs/")
for f in files:
  fpath = "./inputs/" + f
  im = Image.open(fpath)
  width, height = im.size
  newsize = (int(width/2), int(height/2))
  im = im.resize(newsize)
  im.save(fpath)