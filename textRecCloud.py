import os, io
import cv2
from google.cloud import vision
import pandas as pd
from PIL import Image
import numpy as np
import os.path
from os import path
import matplotlib.pyplot as plt

def Rec():
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'visionApi.json'

    client = vision.ImageAnnotatorClient()

    path ="output/image_crops"

    num = 0
    output = []

    for imageName in os.listdir(path):
        
        inputPath = os.path.join(path, imageName)
        img = Image.open(inputPath)
        img = np.asarray(img)
        img = cv2.resize(img, None, fx=1.3, fy=1.3, interpolation=cv2.INTER_CUBIC)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        content = cv2.imencode('.jpg', img)[1].tobytes()

        image = vision.Image(content = content)

        response = client.text_detection(
        image=image,
        image_context={"language_hints": ["en"]},
        
        )
        texts = response.text_annotations
        df = pd.DataFrame(columns=['description'])
        for text in texts:
            df = df.append(dict(description=text.description), ignore_index=True)
        
        df = df.dropna()
        if not df.empty:
            text = texts[0].description
        else:
            text = ""
        output += [text]
        
        num = num + 1

        if response.error.message:
            raise Exception(
                '{}\nFor more info on error messages, check: '
                'https://cloud.google.com/apis/design/errors'.format(
                    response.error.message))
    total = []

    for x in output:
        total.append(x.replace("\n", ""))

    return total