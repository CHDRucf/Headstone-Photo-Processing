from initialization import Initialization_Screen
from processing import Processing_Screen
from headstone import Headstone
from categorize_ocr_output import categorize_ocr_output
import labeling
from global_vars import global_vars, slash
import exceptions
import threading
import time
import tkinter as tk
import glob
import numpy as np
from PIL import Image
import cv2
import traceback

data_loaded = False

debug = False
timing = False
timing_ouput_file = "runtime_output_file.txt"
profiling = False
profiling_output_file = "profiling_output_file.prof"

if global_vars.toggles["Macro Rotate"] or global_vars.toggles["Micro Rotate"]:
    from rotation import rotation_algorithm as rotate

if global_vars.toggles["Crop"]:
    from cropping import cropping_process as crop

if global_vars.toggles["OCR"]:
    from mainOCR import OCR

if profiling:
    import cProfile
    import pstats


def drive(main_window):
    initialize(main_window)
    if not global_vars.initialized:
        return

    image_paths = load_images()
    labeling.load_data()
    global data_loaded
    data_loaded = True
    
    if profiling:
        with cProfile.Profile() as pr:
            process_images(main_window, image_paths)
        
        stats = pstats.Stats(pr)
        stats.sort_stats(pstats.SortKey.TIME)
        stats.dump_stats(filename=profiling_output_file)
    else:
        process_images(main_window, image_paths)


def initialize(main_window):
    lock = threading.Lock()
    Initialization_Screen(main_window, lock)
    lock.acquire()


def load_images():
    image_paths = glob.glob(global_vars.parameters.get("Image Folder") + slash + "*.JPG")
    image_paths.sort()
    
    global_vars.num_images = len(image_paths)
    global_vars.current_image = 1

    return image_paths


def process_images(main_window, image_paths):
    screen = Processing_Screen(main_window)

    for i, path in enumerate(image_paths):
        global_vars.current_image = i + 1

        if screen.update():
            break

        if debug: 
            print("Processing Image {}: {}".format(i+1, Headstone.extract_filename(path)))
        
        if timing:
            start = time.perf_counter()

        process_image(path)

        if timing or debug:
            end = time.perf_counter()
            elapsed = end - start
        
        if debug:
            print(f"Image {i+1} processed in {elapsed:.02f} seconds")

        if timing:
            with open(timing_ouput_file, 'a') as f:
                f.write(f"{elapsed:.02f}\n")


    screen.done()


def process_image(path):
    headstone = Headstone(path)

    try:
        modify_image(headstone)
    except Exception:
        headstone.move("Error Folder")
        headstone.save()
        traceback.print_exc()
        return

    headstone.move("Processed Originals Folder")
    headstone.save()

    try:
        label_image(headstone)
    except exceptions.OCRError:
        pass
    except exceptions.LabelError as e:
        headstone.write_modified("Feedback Folder")
        headstone.save()
        if global_vars.options["User Feedback"] == "Full" or \
        e.situation in (exceptions.LabelError.Situations.Multiple_Perfect, exceptions.LabelError.Situations.Debugging) or \
        e.situation in (exceptions.LabelError.Situations.Fuzzy, exceptions.LabelError.Situations.Fuzzy_Tie, exceptions.LabelError.Situations.Too_Close_To_Call) and global_vars.options["User Feedback"] != "Reject":
            global_vars.feedback_queue.append(headstone.modified_path)
        return
    except Exception:
        headstone.move("Error Folder")
        headstone.save()
        return
    
    headstone.write_modified("Destination Folder", apply_label=True)
    headstone.save()


def modify_image(headstone): 
    if global_vars.toggles["Micro Rotate"] or global_vars.toggles["Macro Rotate"]:
        try:
            headstone.modified_image = rotate(headstone.original_image, global_vars.toggles["Macro Rotate"], global_vars.toggles["Micro Rotate"])
        except Exception as e:
            headstone.error = e
            headstone.log_event("Encountered exception '{}' during rotation".format(str(e)))
            traceback.print_exc()
            raise e
        else:
            headstone.log_event("Rotated successfully")

    if global_vars.toggles["Crop"]:
        try:
            if global_vars.toggles["Micro Rotate"] or global_vars.toggles["Macro Rotate"]:
                converted = Image.fromarray(cv2.cvtColor(headstone.modified_image, cv2.COLOR_BGR2RGB))
            else:
                converted = Image.fromarray(cv2.cvtColor(headstone.original_image, cv2.COLOR_BGR2RGB))
            cropped = crop(converted, global_vars.options["Cropping Buffer"])
            headstone.modified_image = cv2.cvtColor(np.array(cropped), cv2.COLOR_RGB2BGR)
        except Exception as e:
            headstone.error = e
            headstone.log_event("Encountered exception '{}' during cropping".format(str(e)))
            #traceback.print_exc()
            raise e
        else:
            headstone.log_event("Cropped successfully")

    if not (global_vars.toggles["Macro Rotate"] or global_vars.toggles["Micro Rotate"] or global_vars.toggles["Crop"]):
        headstone.modified_image = headstone.original_image
    


def label_image(headstone): 
    if global_vars.toggles["OCR"]:
        try:
            headstone.ocr_text = OCR(headstone.modified_image, global_vars.options["OCR Technique"] == "Google Cloud Vision")
        except Exception as e:
            headstone.error = e
            headstone.log_event("Encountered exception '{}' during OCR".format(str(e)))
            traceback.print_exc()
            raise e

        # Convert ocr_text into the headstone's text fields
        try:
            categorize_ocr_output(headstone)
        except Exception as e:
            traceback.print_exc()
        
        if global_vars.toggles["Label"]:
            try:
                labeling.driver_labeling(headstone)
            except exceptions.LabelError as e:
                if headstone.error is None:
                    headstone.error = e
                headstone.log_event("Encountered exception '{}' during driver labeling".format(str(e)))
                raise e
            else:
                headstone.log_event("Labeled successfully with label '{}'".format(headstone.label))
        else:
            e = exceptions.LabelError(situation=exceptions.LabelError.Situations.Manual)
            headstone.error = e
            raise e

    else:
        e = exceptions.LabelError(situation=exceptions.LabelError.Situations.Manual)
        headstone.error = e
        raise e


if __name__ == "__main__":
    main_window = tk.Tk()
    main_window.geometry("1500x500")
    main_window.title("Headstone Photograph Processing System")
    
    driver = threading.Thread(target=drive, args=(main_window,))
    driver.start()

    main_window.mainloop()

    if data_loaded:
        labeling.write_data()