import sys
import textDetect
import os
import shutil
import textRec
import textRecCloud
import cv2
from PIL import Image

def OCR(image, isOnline):

    OCR_output = []

    #Run both the text detection and text recognition
    num = textDetect.OCR(image)
    if isOnline is True:
        OCR_output = textRecCloud.Rec()
    else:
        OCR_output = textRec.Rec()

    shutil.rmtree('output')

    #return string of text segments
    return OCR_output