# Headstone Photograph Processing System
# Global Variables for System Operation
# Provides a mechanism to store all of the parameters and options that govern the program's execution
# 
# Parameters
#   > Image Folder: The folder contain the images to be processed
#   > Data File: The comma-separated-values (csv) file containing gravesite information
#   > Destination Folder: The folder to contain the processed images once completed
#   > Error Folder: The folder to contain all images that encountered an error while processing
# 
# Options
#   > User Feedback (None, Partial, or Full): The amount of assistance the program will request from the user
#   > Fuzzy Matches (Reject, Request Confirmation, or Accept): How the program should handle imperfect near-matches for the labeling system
#   > Fuzziness Threshold: An integer from 0 to 100 controlling how close a fuzzy match must be to be considered
#   > Error Processing (True or False): Identifies if the images to be processed have already been partially-processed

import collections
import os
from typing import OrderedDict

if os.name == 'nt':
    slash = '\\'
elif os.name == 'posix':
    slash = '/'

settings_file = 'initialization_settings.txt'
default_settings = {
    "Working Folder":"", 
    "Image Folder": "images",
    "Data File": "data.csv",
    "Destination Folder": "complete",
    "Error Folder": "errors",
    "Feedback Folder": "feedback",
    "Processed Originals Folder": "processed_originals",
    "Log File": "log.txt",
    "User Feedback": "Full",
    "Fuzzy Matches": "Request Confirmation",
    "Fuzziness Threshold": 50,
    "Confirmation Tolerance": 5,
    "Cropping Buffer": 0,
    "OCR Technique": "Tesseract",
    "Label Format": "{Section}-{Site}",
    "Macro Rotate": True,
    "Micro Rotate": True,
    "Crop": True,
    "OCR": True,
    "Label": True,
}

class Global_Vars:
    def __init__(self):
        if os.path.isfile(settings_file):
            self.file_init()
        else:
            self.default_init()

        self.feedback_queue = list()
        self.initialized = False
        self.log = ""
        self.prev_log = ""

    def default_init(self):
        # Default values for the parameters
        self.parameters = collections.OrderedDict()
        self.parameters["Working Folder"] =     ""
        self.parameters["Image Folder"] =       "{}{}images".format("{}", slash)
        self.parameters["Data File"] =          "{}{}data.csv".format("{}", slash)
        self.parameters["Destination Folder"] = "{}{}complete".format("{}", slash)
        self.parameters["Error Folder"] =       "{}{}errors".format("{}", slash)
        self.parameters["Feedback Folder"] =    "{}{}feedback".format("{}", slash)
        self.parameters["Processed Originals Folder"] = "{}{}processed_originals".format("{}", slash)
        self.parameters["Log File"] =                "{}{}log.txt".format("{}", slash)

        # Default values for the runtime options
        self.options = collections.OrderedDict()
        self.options["User Feedback"] =     "Full"
        self.options["Fuzzy Matches"] =     "Request Confirmation"
        self.options["Fuzziness Threshold"]= 50
        self.options["Confirmation Tolerance"]= 5
        self.options["Cropping Buffer"] =    0
        self.options["OCR Technique"] =     "Tesseract"
        self.options["Label Format"] =       "{Section}-{Site}"

        self.toggles = collections.OrderedDict()
        self.toggles["Macro Rotate"] = True
        self.toggles["Micro Rotate"] = True
        self.toggles["Crop"] = True
        self.toggles["OCR"] = True
        self.toggles["Label"] = True


    def file_init(self):
        with open(settings_file) as f:
            settings = f.read()
        settings = settings.split('\n')
        settings = {k:v.strip() for (k,v) in [line.split(':', 1) for line in settings]}

        self.parameters = collections.OrderedDict()
        self.parameters["Working Folder"] = settings.get("Working Folder", "")
        for parameter in ("Image Folder", "Data File", "Destination Folder",
                          "Error Folder", "Feedback Folder", "Processed Originals Folder", "Log File"):
            self.parameters[parameter] = "{}{}{}".format("{}", slash, settings.get(parameter, default_settings[parameter]))


        self.options = collections.OrderedDict()

        try:
            assert settings["User Feedback"] in ("None", "Partial", "Full")
            self.options["User Feedback"] = settings["User Feedback"]
        except Exception as e:
            self.options["User Feedback"] = default_settings["User Feedback"]
        
        try:
            assert settings["Fuzzy Matches"] in ("Reject", "Request Confirmation", "Accept")
            self.options["Fuzzy Matches"] = settings["Fuzzy Matches"]
        except Exception as e:
            self.options["Fuzzy Matches"] = default_settings["Fuzzy Matches"]
        
        try:
            self.options["Fuzziness Threshold"] = int(settings["Fuzziness Threshold"])
        except Exception as e:
            self.options["Fuzziness Threshold"] = default_settings["Fuzziness Threshold"]
        
        try:
            self.options["Confirmation Tolerance"] = int(settings["Confirmation Tolerance"])
        except Exception as e:
            self.options["Confirmation Tolerance"] = default_settings["Confirmation Tolerance"]

        try:
            self.options["Cropping Buffer"] = int(settings["Cropping Buffer"])
        except Exception as e:
            self.options["Cropping Buffer"] = default_settings["Cropping Buffer"]
        
        try:
            assert settings["OCR Technique"] in ("Tesseract", "Google Cloud Vision")
            self.options["OCR Technique"] = settings["OCR Technique"]
        except Exception as e:
            self.options["OCR Technique"] = default_settings["OCR Technique"]
        
        try:
            self.options["Label Format"] = settings["Label Format"]
        except Exception as e:
            self.options["Label Format"] = default_settings["Label Format"]

        
        self.toggles = collections.OrderedDict()
        for toggle in ("Macro Rotate", "Micro Rotate", "Crop", "OCR", "Label"):
            self.toggles[toggle] = True
            try:
                if settings[toggle].lower() == "false":
                    self.toggles[toggle] = False
            except Exception as e:
                self.toggles[toggle] = True


    # Return a string detailing all of the parameters and options neatly
    def __str__(self):
        output = ""
        for d in [self.parameters, self.options]:
            for k, v in d.items():
                output += f'{k}:'.ljust(30) +  f'{v}\n'
        return output
    
    # Format all the parameters to prepend the working folder, and create any folders that don't exist
    def init_working_folder(self):
        for k, v in self.parameters.items():
            if k == "Working Folder":
                continue
            
            v = v.format(self.parameters["Working Folder"])
            self.parameters[k] = v

            if k in ("Data File", "Log File"):
                continue

            if not os.path.isdir(v):
                os.mkdir(v)


global_vars = Global_Vars()