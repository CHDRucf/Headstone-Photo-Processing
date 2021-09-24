import glob
import os
from pprint import pprint
import global_vars
from global_vars import slash
import traceback
import pandas as pd

def extract_filename(path):
    slash_index = path.rfind(slash)
    filename = path[slash_index:]
    return filename

if __name__ == "__main__":
    global_vars = global_vars.global_vars
    #global_vars.parameters["Working Folder"] = "C:\\Users\\mesaj\\Documents\\SD_working"
    global_vars.parameters["Working Folder"] = "C:\\Users\\mesaj\\Desktop\\Demo Fresh"
    #global_vars.parameters["Working Folder"] = "C:\\Users\\mesaj\\Desktop\\Full System Tests\\Greenwood Curved Cloud Vision Micro Only"
    global_vars.init_working_folder()
    rm_list = list()
    mv_list = list()

    for k, v in global_vars.parameters.items():
        v += slash
        if k in ("Destination Folder", "Feedback Folder"):
            rm_list.extend(glob.glob(v + "*"))
            rm_list.extend(glob.glob(v + ".*"))
        if k == "Error Folder":
            rm_list.extend(glob.glob(v+"*.pickle"))
            rm_list.extend(glob.glob(v+".*.pickle"))
            rm_list.extend(glob.glob(v+"*_PROCESSED.JPG"))
            mv_list.extend(glob.glob(v + "*.JPG"))
        if k == "Processed Originals Folder":
            rm_list.extend(glob.glob(v + "*.pickle"))
            rm_list.extend(glob.glob(v + ".*.pickle"))
            mv_list.extend(glob.glob(v + "*.JPG"))

    
    for path in rm_list:
        try:
            os.remove(path)
        except Exception as e:
            traceback.print_exc()

        if path in mv_list:
            mv_list.remove(path)

    for path in mv_list:
        try:
            new_path = global_vars.parameters.get("Image Folder") + extract_filename(path)
            os.replace(path, new_path)
        except Exception as e:
            traceback.print_exc()


    data_file = global_vars.parameters.get("Data File")
    if os.path.isfile(data_file):
        df = pd.read_csv(data_file)
        df = df.assign(Fuzziness = [0] * len(df))
        os.remove(data_file)
        df.to_csv(data_file, index=False)

    log_file = global_vars.parameters.get('Log File')
    if os.path.isfile(log_file):
        os.remove(log_file)
    