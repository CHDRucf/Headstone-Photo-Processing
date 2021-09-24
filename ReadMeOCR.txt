Install these python libraries:

torch
torchvision
opencv-python
scikit-image
scipy
matplotlib

Also install CRAFT and PyTesseract

pip install craft-text-detector
pip install pytesseract

In run:

run with command python mainOCR.py [image_file]

Add folder directly in the Hpps folder and add files to it, for example if the name of the folder was 'data':

python mainOCR.py data/Image.jpg

if the image was labeled Image.jpg

Also, to see heatmaps, boxes, and cropped text segments, include details as a parameter

To run with details, run:


python mainOCR.py data/Image.jpg details

