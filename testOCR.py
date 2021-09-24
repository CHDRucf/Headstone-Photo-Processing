import cv2
import pytesseract
import os
from PIL import Image
import numpy as np


pytesseract.pytesseract.tesseract_cmd = "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

# Load the image manually for testing
img = cv2.imread("output/image_crops/crop_0.png")

# Image resize/grayscale
img = cv2.resize(img, None, fx=1.7, fy=1.7, interpolation=cv2.INTER_CUBIC)
gry = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Post processing
thr = cv2.threshold(gry, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

#Tesseract OCR
config = ("-l eng --oem 1 --psm 7")
text = pytesseract.image_to_string(thr, config=config)
#text = pytesseract.image_to_string(gry, config=config)


print(text)

#Show results
img1 = cv2.resize(thr, (0, 0), fx=0.4, fy=0.4)
cv2.imshow('Result',img1)
cv2.waitKey(0)

