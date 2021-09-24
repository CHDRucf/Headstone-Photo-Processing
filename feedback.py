import tkinter as tk
import global_vars
import color_palette
import PIL
from PIL import Image, ImageTk
import numpy as np
import cv2
from headstone import Headstone
import pandas as pd
import labeling

color = color_palette.color_pallette
global_vars = global_vars.global_vars


class Pictures_Area(tk.Frame):
    def __init__(self, master, error_func):
        super().__init__(master, bg=color.bg)
        self.master = master
        self.pack(fill="both", side="left")

        self.images = Pictures_Subarea(self)
        
        
        self.error_button = tk.Button(self, text="Mark as Erroneous", command=error_func,
                                       highlightthickness=0, bg="#6D0000", fg="#E6B8DF", 
                                       activeforeground="#760000", activebackground="#E6B8DF")

        self.error_button.pack(fill="x", side="bottom")


    def update(self, headstone):
        self.images.update(headstone)


class Pictures_Subarea(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=color.bg)
        self.master = master
        self.pack(fill="both", expand=True)

        self.original = Single_Picture(self, "Original Image")
        self.processed = Single_Picture(self, "Processed Image")


    def update(self, headstone):
        self.original.update(headstone)
        self.processed.update(headstone)


class Single_Picture(tk.Frame):
    def __init__(self, master, text):
        super().__init__(master, bg=color.bg)
        self.master = master
        self.pack(fill="both", expand=True, side="left")

        self.is_original = text.split()[0].lower() == "original"

        self.label = tk.Label(self, text=text, bg=color.bg, fg=color.fg, padx=10)
        self.label.pack()

        self.im = None
        self.img = tk.Label(self)
        self.img.pack()
        

    def update(self, headstone):
        if self.is_original:
            image = headstone.original_image
        else:
            image = headstone.modified_image

        new_height = 400
        scale = new_height/image.shape[0]
        new_width = int(image.shape[1] * scale)
        dim = (new_width, new_height)
        scaled_image = cv2.resize(image, dim, interpolation=cv2.INTER_AREA)
        
        self.im = ImageTk.PhotoImage(PIL.Image.fromarray(cv2.cvtColor(scaled_image, cv2.COLOR_BGR2RGB)))
        self.img.config(image=self.im)


class Matches_Area(tk.Frame):
    def __init__(self, master, functions):
        super().__init__(master, bg=color.bg)
        self.master = master
        self.pack(fill="both", expand=True, side="left")

        self.label = tk.Label(self, text="Possible Matches", bg=color.bg, fg=color.fg, padx=10)
        self.label.pack()

        self.buttons = Match_Buttons_Subarea(self, functions[2])
        self.control = Control_Buttons(self, functions[0:2])

    def update(self, search_df):
        self.buttons.update(search_df)



class Match_Buttons_Subarea(tk.Frame):
    def __init__(self, master, label_function):
        super().__init__(master, bg=color.bg)
        self.master = master
        self.label_function = label_function
        self.pack(fill="both", expand=True)
        self.buttons = list()
    
    def update(self, search_df):
        for button in self.buttons:
            button.destroy()

        if search_df is not None:

            dicts_df = search_df.to_dict(orient="records")
            for entry in dicts_df:
                self.buttons.append(Match_Button(self, entry, self.label_function))
        

class Match_Button(tk.Button):
    def __init__(self, master, entry, label_function):
        self.entry = entry
        self.label_function = label_function
        super().__init__(master, text=self.format_entry(entry), command=self.select, height=3,
                         highlightthickness=0, bg="#00660C", fg="#7EE3C8", 
                         activeforeground="#05300A", activebackground="#7EE3C8")

        self.master = master
        self.pack(fill="x")

    def select(self):
        self.label_function(self.entry)

    def format_entry(self, entry):
        fields = list(Headstone.text_field_keys)
        fields.extend(["Section", "Row", "Site"])

        for i, field in enumerate(fields):
            if field not in entry.keys():
                fields[i] = ""

        fields_formatted = list()
        location_info_formatted = list()


        name = [entry.get("First Name", ""), entry.get("Middle Name", ""), entry.get("Surname", "")]
        name = [str(s) for s in name if s != ""]
        name = " ".join(name)
        if name != "":
            fields_formatted.append(name)

        if "State" in entry.keys() and entry["State"] != "":
            fields_formatted.append(str(entry["State"]))

        if "Conflict" in entry.keys() and entry["Conflict"] != "":
            fields_formatted.append(str(entry["Conflict"]))

        if "Birth Date" in entry.keys() and entry["Birth Date"] != "":
            fields_formatted.append("Born " + str(entry["Birth Date"]))

        if "Death Date" in entry.keys() and entry["Death Date"] != "":
            fields_formatted.append("Died " + str(entry["Death Date"]))

        for k in ["Section", "Row", "Site"]:
            if k in entry.keys() and entry[k] != "":
                location_info_formatted.append(k + " " + str(entry[k]))

        
        formatted_string = ", ".join(fields_formatted) + "\n" + ", ".join(location_info_formatted)  + "\n" + "Fuzzy Score: " + str(entry["Fuzziness"])

        
        return formatted_string


class Control_Buttons(tk.Frame):
    def __init__(self, master, functions):
        super().__init__(master, bg=color.bg)
        self.master = master
        self.pack(fill="both", side="bottom")
        self.return_func, self.update = functions


        self.return_button = tk.Button(self, text="Return", command=self.return_func,
                                       highlightthickness=0, bg=color.accent, fg=color.fg, 
                                       activeforeground=color.bg, activebackground=color.fg)

        self.skip_button = tk.Button(self, text="Skip Image", command=self.skip,
                                     highlightthickness=0, bg=color.accent, fg=color.fg, 
                                     activeforeground=color.bg, activebackground=color.fg)

        self.return_button.pack(fill="x", expand=True, side="left")
        self.skip_button.pack(fill="x", expand=True, side="left")

    def skip(self):
        global_vars.feedback_queue.append(global_vars.feedback_queue.pop(0))
        self.update()


class Search_Area(tk.Frame):
    def __init__(self, master, parent_search):
        super().__init__(master, bg=color.bg)
        self.master = master
        self.parent_search = parent_search
        self.pack(fill="both", expand=True, side="left", pady=(25, 0))

        self.fields = dict()

        for k in Headstone.text_field_keys:
            self.fields[k] = Label_Entry_Pair(self, k)

        self.search_button = tk.Button(self, text="Search", command=self.search,
                                       highlightthickness=0, bg=color.accent, fg=color.fg, 
                                       activeforeground=color.bg, activebackground=color.fg)

        self.search_button.pack(fill="x", side="bottom")


    def search(self):
        data = {k: self.fields[k].entry.get() for k in self.fields.keys()}
        self.parent_search(data)

    def update(self, headstone):
        for k, v in self.fields.items():
            v.entry.delete(0, len(v.entry.get()))
            v.entry.insert(0, headstone.text_fields[k])


class Label_Entry_Pair(tk.Frame):
    def __init__(self, master, key):
        super().__init__(master, bg=color.bg)
        self.master = master
        self.pack(fill="x", padx=20, pady=(15, 0))

        self.label = tk.Label(self, text=key, bg=color.bg, fg=color.fg, padx=10, width=12, anchor="w")
        self.label.pack(side="left")

        self.entry = tk.Entry(self, width=20, bg=color.accent, fg=color.fg, highlightthickness=0, insertbackground=color.fg)
        self.entry.pack(fill="x", expand=True, side="left")



class Feedback_Screen(tk.Frame):
    def __init__(self, master, processing_screen):
        super().__init__(master, bg=color.bg)
        self.master = master
        self.processing_screen = processing_screen
        self.headstone = None

        self.pictures = Pictures_Area(self, self.error_headstone)
        self.matches = Matches_Area(self, (self.switch_to_processing_screen, self.update, self.label_headstone))
        self.search = Search_Area(self, self.update_buttons)


    def switch_to_processing_screen(self):
        self.pack_forget()
        self.processing_screen.pack(fill="both", expand=True)
        self.processing_screen.update()

    def update(self):
        if len(global_vars.feedback_queue) == 0:
            self.switch_to_processing_screen()
            return

        self.headstone = Headstone.load(global_vars.feedback_queue[0])
        self.pictures.update(self.headstone)
        self.matches.update(labeling.feedback_labeling(self.headstone))
        self.search.update(self.headstone)
        

    def update_buttons(self, data):
        if self.headstone is None:
            return

        for k, v in data.items():
            self.headstone.text_fields[k] = v

        search_df = labeling.feedback_labeling(self.headstone)

        self.matches.update(search_df)


    def label_headstone(self, entry):
        if self.headstone is None:
            return

        # Fuzziness score of 100 because we assume the user is correct
        self.headstone.fuzziness_score = 100 #entry["Fuzziness"]
        labeling.set_fuzziness(entry, 100)
        self.headstone.set_label(global_vars.options["Label Format"].format(entry))
        self.headstone.error = None
        self.headstone.log_event("Manually labeled with label '{}'".format(self.headstone.label))
        self.headstone.move("Destination Folder", target="MODIFIED", apply_label=True)
        self.headstone.save()
        #print(self.headstone)
        global_vars.feedback_queue.pop(0)
        self.update()

    
    def error_headstone(self):
        if self.headstone is None:
            return

        self.headstone.set_label(Headstone.extract_filename(self.headstone.original_path).replace(".JPG", "") + "_PROCESSED")
        self.headstone.move("Error Folder")
        self.headstone.move("Error Folder", target="MODIFIED", apply_label=True)
        self.headstone.save()
        global_vars.feedback_queue.pop(0)
        self.update()


        

        