import pickle
import cv2
import os
import subprocess
from global_vars import global_vars, slash
import threading

#global_vars = global_vars.global_vars

# Class to organize all the relevant information for a particular headstone image
# Image metadata is saved by serializing this object
class Headstone():
    text_field_keys = ("First Name", "Middle Name", "Surname", "State", "Conflict", "Birth Date", "Death Date")
    log_lock = threading.Lock()

    def __init__(self, path):
        self.original_filename = self.extract_filename(path)[1:]
        self.original_path = path
        self.original_image = cv2.imread(path)
        self.modified_path = None
        self.modified_image = None
        self.error = None
        self.ocr_text = None
        self.text_fields = {k:'' for k in Headstone.text_field_keys}
        self.label = None
        self.fuzziness_score = None
        self.as_string = None
        self.log = '\n\nLog:'


    # Save metadata in same location as images (original and modified)
    def save(self):
        # Replace the numpy representations of image with None so that
        # they aren't saved in the save file, which would take unnecesary space
        original_backup = self.original_image
        self.original_image = None

        modified_backup = self.modified_image
        self.modified_image = None

        self.as_string = '\n\n' + str(self) + '\n\n'

        for path in (self.original_path, self.modified_path):
            if path is None:
                continue

            save_file = path.replace(".JPG", ".pickle")

            try:
                if os.path.isfile(save_file):
                    os.remove(save_file)
                with open(save_file, 'wb') as f:
                    pickle.dump(self, f, pickle.HIGHEST_PROTOCOL)
            except:
                pass

            self.hide_file(save_file)

        # Restore backups
        self.original_image = original_backup
        self.modified_image = modified_backup


    # Save the modified as an image on disk
    def write_modified(self, dest_folder, apply_label=False):
        if self.modified_image is None:
            raise Exception("image not modified")

        filename = self.extract_filename(self.original_path)
        if apply_label:
            filename = slash + self.label

        new_path = global_vars.parameters.get(dest_folder) + filename
        new_path = self.overwrite_protection(new_path)

        # PIL.Image.fromarray(self.modified_image).save(new_path)
        cv2.imwrite(new_path, self.modified_image)

        self.modified_path = new_path

        self.log_event("Modified image written to " + dest_folder)


    # Move either the original image or the modified image to a new folder
    # Target must be "ORIGINAL" or "MODIFIED"
    def move(self, dest_folder, target="ORIGINAL", apply_label=False):
        if dest_folder not in global_vars.parameters.keys():
            raise Exception("invalid dest_folder")

        path = ""

        # Determine which version of the image we are moving
        if target == "ORIGINAL":
            path = self.original_path
        elif target == "MODIFIED":
            if self.modified_path is None:
                raise Exception("modified image does not exist")
            path = self.modified_path
        else:
            raise Exception("invalid target, must be 'ORIGINAL' or 'MODIFIED'")

        # Move the image
        filename = self.extract_filename(path)
        if apply_label:
            filename = slash + self.label

        new_path = global_vars.parameters.get(dest_folder) + filename
        new_path = self.overwrite_protection(new_path)
        os.replace(path, new_path)

        # Move the corresponding save data if it exists
        save_file = self.get_save_path(path)
        if os.path.isfile(save_file):
            new_save = self.get_save_path(new_path)
            os.replace(save_file, new_save)

        # Update path
        if target == "ORIGINAL":
            self.original_path = new_path
        elif target == "MODIFIED":
            self.modified_path = new_path

        self.log_event(target.title() + " image moved to " + dest_folder)

    # Maintain a log of events that happen to this headstone while processing
    def log_event(self, event):
        self.log += '\t' + event + '\n'

        Headstone.log_lock.acquire()
        if global_vars.prev_log != self.original_filename:
            if global_vars.prev_log != '':
                global_vars.log += '\n' 
            global_vars.prev_log = self.original_filename
        
        global_vars.log += self.original_filename + '\t' + event + '\n'
        Headstone.log_lock.release()


    # Load class from pickle file
    @staticmethod
    def load(path):
        save_file = path.replace(".JPG", ".pickle")

        if os.name == 'posix':
            directory, filename = save_file.rsplit('/', 1)
            save_file = directory + '/.' + filename 

        with open(save_file, 'rb') as f:
            loaded = pickle.load(f)

        loaded.original_image = cv2.imread(loaded.original_path)
        if loaded.modified_path is not None:
            loaded.modified_image = cv2.imread(loaded.modified_path)

        return loaded


    # Split a path along the right-most '/', return whatever right of the split
    # Typically, this will return just the filename without the directory it's in
    @staticmethod
    def extract_filename(path):
        slash_index = path.rfind(slash)
        filename = path[slash_index:]
        return filename


    # Set the label, making sure that the filename still ends in ".JPG"
    def set_label(self, label):
        self.label = label + ".JPG"

    # Marks the file located at "path" to be hidden
    # Works on both Windows and Linux
    @staticmethod
    def hide_file(path):
        # Windows
        if os.name == 'nt':
            subprocess.check_call(["attrib","+H", path])

        # Linux
        else:
            # Separate path into directory and filename
            directory, filename = path.rsplit('/', 1)
            new_path = directory + '/.' + filename 
            os.replace(path, new_path)

    # path: path to a .JPG file
    # output: path to the corresponding .pickle file
    @staticmethod
    def get_save_path(path):
        path = path.replace(".JPG", ".pickle")

        # Windows
        if os.name == 'nt':
            return path

        # Linux
        else:
            # Separate path into directory and filename
            directory, filename = path.rsplit('/', 1)
            new_path = directory + '/.' + filename 
            return new_path

    # Check if a file already exists at path
    # If it does, append a (1) to the path and return it
    # Otherwise return path unchanged
    @staticmethod
    def overwrite_protection(path):
        if os.path.isfile(path):
            i = 1
            no_extension = path.replace('.JPG', '')
            while os.path.isfile(no_extension + f" ({i}).JPG"):
                i += 1
            path = no_extension + f" ({i}).JPG"

        return path


    def __str__(self):
        info = '\n'.join(['\t{}:\t{}'.format(k,v) for k, v in self.text_fields.items()])

        strings = [
            "Original Path: {}".format(self.original_path),
            "Modified Path: {}".format(self.modified_path),
            "Error: {}".format(self.error),
            "OCR Text: {}".format(self.ocr_text),
            "Info: {}".format(info),
            "Label: {}".format(self.label),
            "Fuzziness Score: {}".format(self.fuzziness_score)
        ]

        return '\n'.join(strings)
