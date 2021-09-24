import cv2
import pytesseract
import os
from PIL import Image
import numpy as np
import os.path
from os import path
import matplotlib.pyplot as plt
from skimage import feature

#Takes each text segment and runs Tesseract character extraction
def Rec():

    #Set the tesseract_cmd, errors without
    pytesseract.pytesseract.tesseract_cmd = "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

    #Get the image text segments directory
    path ="output/image_crops"

    num = 0
    output = []

    #Grab each image in text segment directory
    for imageName in os.listdir(path):
        
        inputPath = os.path.join(path, imageName)
        img = Image.open(inputPath)
        img = np.asarray(img)

        #Change dpi, change to grayscale to improve accuracies
        img = cv2.resize(img, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
        gry = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        #Image post processing
        kernel = np.ones((1, 1), np.uint8)
        gry = cv2.dilate(gry, kernel, iterations=1)
        gry = cv2.erode(gry, kernel, iterations=1)

        #Image post processing
        thr = cv2.threshold(cv2.medianBlur(gry, 5), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

        #Tesseract Image to string
        text = pytesseract.image_to_string(thr, lang='eng', config='--psm 13 --oem 3 -c tessedit_char_whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -."')

        text = text.split('\n', 1)[0]
        output += [text]
        
        num = num + 1

    return output
        
        

