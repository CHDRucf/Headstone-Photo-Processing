# import craft functions
import os
from craft import CRAFT
from refinenet import RefineNet
import torch
import torch.nn as nn
from torch.autograd import Variable
import warnings

from craft_text_detector import (
    read_image,
    get_prediction,
    export_detected_regions,
    export_extra_results
)

# Model loading
craft_net = None
refine_net = None

#Recieves input image and determines bounding box positions for each text segment
def OCR(image):

    #Both of the directories for the cropped photos and the details
    output_dir = 'output/'
    details_dir = 'details/'

        # # load both models if needed
    global craft_net
    global refine_net

    if craft_net is None:
        craft_net = CRAFT()
        craft_net.load_state_dict(copyStateDict(torch.load('craft_mlt_25k.pth', map_location='cpu')))
        craft_net.eval()
    
    if refine_net is None:
        refine_net = RefineNet()
        refine_net.load_state_dict(copyStateDict(torch.load('craft_refiner_CTW1500.pth', map_location='cpu')))
        refine_net.eval()

    # read the image
    image = read_image(image)

    # perform the prediction
    prediction_result = get_prediction(
        image=image,
        craft_net=craft_net,
        refine_net=refine_net,
        text_threshold=0.4,
        link_threshold=0.2,
        low_text=0.2,
        poly=True,
        cuda=False,
        long_size= 1280
    )

    # export detected text regions to ouput
    exported_file_paths = export_detected_regions(
        image=image,
        regions=prediction_result["polys"],
        output_dir=output_dir,
        rectify=True
    )

from collections import OrderedDict
def copyStateDict(state_dict):
    if list(state_dict.keys())[0].startswith("module"):
        start_idx = 1
    else:
        start_idx = 0
    new_state_dict = OrderedDict()
    for k, v in state_dict.items():
        name = ".".join(k.split(".")[start_idx:])
        new_state_dict[name] = v
    return new_state_dict