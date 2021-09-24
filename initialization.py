# Headstone Photograph Processing System
# Program Initialization User Interface
# 
# Provides an interface for the user to select parameters for the program's execution:
#   > Image Folder: The folder contain the images to be processed
#   > Data File: The comma-separated-values (csv) file containing gravesite information
#   > Destination Folder: The folder to contain the processed images once completed
#   > Error Folder: The folder to contain all images that encountered an error while processing
# 
# Also provides an interface for the user to select options that control the behavior of the program:
#   > User Feedback (None, Partial, or Full): The amount of assistance the program will request from the user
#   > Fuzzy Matches (Reject, Request Confirmation, or Accept): How the program should handle imperfect near-matches for the labeling system
#   > Fuzziness Threshold: An integer from 0 to 100 controlling how close a fuzzy match must be to be considered
#   > Error Processing (True or False): Identifies if the images to be processed have already been partially-processed
#
# Provides a single function (initialize()) which runs the interface and returns the parameters and options

import os
import glob
import re
import pandas as pd
import traceback

import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox

from global_vars import global_vars
from color_palette import color_pallette as color
from headstone import Headstone
import exceptions

#color = color_palette.color_pallette
#global_vars = global_vars.global_vars

# Displays a parameter's current value (if any)
# User may click on a button to set the parameter's value
class Parameter(tk.Frame):
    def __init__(self, master=None, name="Parameter"):
        super().__init__(master, bg=color.bg, bd=5)
        self.pack(fill="x", expand=True)
        
        self.name = name

        # Buttons are all the same size and left-justified
        self.btn = tk.Button(self, text=name, width=12, command=self.set_parameter, highlightthickness=0,
                            bg=color.accent, fg=color.fg, activebackground=color.fg, activeforeground=color.accent, highlightbackground=color.fg)
        self.btn.pack(side="left")

        # Display the current value of the cooresponding parameter, or "Unselected" if it is empty
        if global_vars.parameters[name] == "":
            label_string = "Unselected"
        else:
            label_string = "Current: " + global_vars.parameters[name]

        self.label = tk.Label(self, text=label_string, bg=color.bg, fg=color.fg, justify="left", padx=10, font="Helvetica 10 italic")
        self.label.pack(side="left")

    
    # When the button is clicked, open up the file manager to select the parameter
    # Select either a folder or file depending on the last word in the parameter name
    def set_parameter(self):
        parameter_value = ""
        # If the parameter is a folder, select a folder
        if self.name.split()[-1] == "Folder":
            parameter_value = filedialog.askdirectory(initialdir=os.getcwd(), title="Select Folder")

        # If the parameter is a file, select a file
        elif self.name.split()[-1] == "File":
            parameter_value = filedialog.askopenfilename(initialdir=os.getcwd(), title="Select File", filetypes=(("csv", "*.csv"), ("all files", "*.*")))

        # Error catching (should never get here)
        else:
            return

        # Make sure windows
        
        # Once selected, update the parameter and label accordingly
        # Must chech that parameter_value is a string because it could be NULL
        if isinstance(parameter_value, str):
            self.label.config(text="Current: " + parameter_value)
            global_vars.parameters[self.name] = parameter_value


# The section of the initialization screen that contains all the parameters
class Parameter_Section(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master, bg=color.bg)
        self.pack(padx=20, pady=(20, 0))
        Parameter(self, "Working Folder")
        #for parameter in global_vars.parameters.keys():
            #Parameter(self, parameter)


# Radio buttons for a particular option
# Contains a label to describe what the option is
# Includes a dummy frame just to visually indent the radio buttons
class Radio(tk.Frame):
    def __init__(self, master=None, name="Radio", variable=None, options=None):
        super().__init__(master, bg=color.bg, bd=5)
        self.pack(side="left", fill="y")

        # Display what the option is so the user knows what they're doing
        label = tk.Label(self, text=name, bg=color.bg, fg=color.fg, justify="left", anchor="w")
        label.pack(fill='x')

        # We need a container frame in order to make the indentation work
        lower_area = tk.Frame(self, bg=color.bg)
        lower_area.pack()
        
        # Dummy frame to indent the buttons
        indent = tk.Frame(lower_area, bg=color.bg, width=15)
        indent.pack(side="left")

        # Frame to contain the buttons
        button_area = tk.Frame(lower_area, bg=color.bg)
        button_area.pack(side="left")

        # The buttons need to all be the same width so that they line up correctly
        # Set the width to be the greatest width needed 
        width = max([len(option) for option in options])

        # Create a button for each of the radio options
        for option in options:
            button = tk.Radiobutton(button_area, text=option, variable=variable, value=option, justify="left",
                                    borderwidth=0, anchor='w', width=width, highlightthickness=0,
                                    bg=color.bg, fg=color.fg, activebackground=color.fg, activeforeground=color.bg, selectcolor=color.bg)
            button.pack()


# The section of the initialization screen that contains all the radio options
# Radio buttons in tkinter modify a tkinter StringVar object (or IntVar, BooleanVar, etc) 
# Those objects are kept here, and only propogate to global_vars when prompted by the start button
class Radio_Section(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master, bg=color.bg)
        self.pack(padx=20, pady=(15, 0))
        
        # All of the options for the three radios
        self.user_feedback_options = ["None", "Partial", "Full"]
        self.fuzzy_matches_options = ["Reject", "Request Confirmation", "Accept"]
        self.ocr_technique_options = ["Tesseract", "Google Cloud Vision"]
        
        # These will contain whatever the radio selection is until the user presses the start button
        self.user_feedback = tk.StringVar(value=global_vars.options["User Feedback"])
        self.fuzzy_matches = tk.StringVar(value=global_vars.options["Fuzzy Matches"])
        self.ocr_technique = tk.StringVar(value=global_vars.options["OCR Technique"])

        # Create the first radio
        Radio(self, "User Feedback", self.user_feedback, self.user_feedback_options)
        
        # Create a dummy frame to put a gap between the radios
        gap = tk.Frame(self, bg=color.bg, width=50)
        gap.pack(side="left")
        
        # Create the second radio
        Radio(self, "Fuzzy Matches", self.fuzzy_matches, self.fuzzy_matches_options)

        # Create a dummy frame to put a gap between the radios
        gap = tk.Frame(self, bg=color.bg, width=50)
        gap.pack(side="left")

        # Create the third radio
        Radio(self, "OCR Technique", self.ocr_technique, self.ocr_technique_options)


# Entry box for the user to enter their desired fuzziness threshold, or similar
# Contains some descriptive labels as well
class Entry_Box(tk.Frame):
    def __init__(self, master=None, text="Entry Box!"):
        super().__init__(master, bg=color.bg)
        self.pack(padx=20, pady=(15, 0))

        default_value = global_vars.options[text]

        # Label to identify what this box is for
        label = tk.Label(self, text=text, bg=color.bg, fg=color.fg, padx=10)
        label.pack(side="left")

        # The entry box to enter the desired value
        # The value can be retrieved with entry.get()
        # Value will wait here until retrieved by the start button
        self.entry = tk.Entry(self, width=10, bg=color.accent, fg=color.fg, highlightthickness=0, insertbackground=color.fg)
        self.entry.insert(0, str(default_value))
        self.entry.pack(side="left")

        # Label to identify what the default value is
        default = tk.Label(self, text=f"Default: {default_value}", bg=color.bg, fg=color.fg, padx=10, font="Helvetica 10 italic")
        default.pack(side="left")

# Holds all the toggle checkboxes
class Toggles_Area(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master, bg=color.bg)
        self.pack(padx=10, pady=(15,0))
        self.checkboxes = dict()
        for toggle, value in global_vars.toggles.items():
            self.checkboxes[toggle] = Checkbox(self, toggle, value)
    
    def apply_toggles(self):
        for toggle in global_vars.toggles.keys():
            global_vars.toggles[toggle] = self.checkboxes[toggle].value.get()

# Simple checkbox to set the section toggles
# Checkboxes in tkinter modify a tkinter BooleanVar object (or IntVar, StringVar, etc) 
# This object is kept here, and only propogates to global_vars when prompted by the start button
class Checkbox(tk.Frame):
    def __init__(self, master=None, text="Toggle Me!", default_value="True"):
        super().__init__(master, bg=color.bg)
        self.pack(padx=10, side="left")

        # Contains the checkbox value until the user preses the start button
        self.value = tk.BooleanVar(value=default_value)

        # The checkbox
        checkbox = tk.Checkbutton(self, text=text, highlightthickness=0,
                                    variable=self.value, onvalue=True, offvalue=False, 
                                    bg=color.bg, fg=color.fg, activeforeground=color.bg, activebackground=color.fg,
                                    selectcolor=color.accent)
        checkbox.pack()

# Entry box for the user to enter their desired format for the image labeling
# Contains some descriptive labels as well
class Label_Formatting(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master, bg=color.bg)
        self.pack(padx=20, pady=(15, 0))

        default = global_vars.options["Label Format"]

        # Label to identify that this is for the label formatting
        label = tk.Label(self, text="Label Format", bg=color.bg, fg=color.fg, padx=10)
        label.pack(side="left")

        # The entry box to enter the desired value
        # The value can be retrieved with entry.get()
        # Value will wait here until retrieved by the start button
        self.entry = tk.Entry(self, width=35, bg=color.accent, fg=color.fg, highlightthickness=0, font="Courier 10", insertbackground=color.fg)
        self.entry.insert(0, default)
        self.entry.pack(side="left")

        # Label to identify what the default value is
        default_lbl1 = tk.Label(self, text=f"Default: ", bg=color.bg, fg=color.fg, font="Helvetica 10 italic")
        default_lbl2 = tk.Label(self, text=default, bg=color.bg, fg=color.fg, font="Courier 10")
        default_lbl1.pack(side="left", padx=(10,0))
        default_lbl2.pack(side="left", padx=(0,10))

    # Verify that the contents of the entry box are valid
    # If yes, the entry and a list of its parsed elements
    # If not, return None
    def get(self):
        s = self.entry.get()

        num_open = len([c for c in s if c == '{'])
        num_close= len([c for c in s if c == '}'])
        if num_open != num_close:
            return None

        # Check for double-close without open or vice-versa
        check = re.compile("{[^}]*{|}[^{]*}")
        if check.search(s) is not None:
            return None

        # Check for close-without-open and open-without-close
        check = re.compile("^[^{]*}|{[^}]*$")
        if check.search(s) is not None:
            return None

        # Extract all the text bounded by {}
        reg = re.compile("{.*?}")
        matches = reg.findall(s)
        
        # Trim off the unneeded {}
        trimmer = re.compile("{|}")
        matches = [trimmer.sub("", match) for match in matches]

        return s, matches



# Frame to hold the start and abort buttons
class Control_Buttons(tk.Frame):
    def __init__(self, master, start_cmd, abort_cmd):
        super().__init__(master, bg=color.bg)
        self.pack(padx=20, pady=(15, 20))
        
        self.start = tk.Button(self, text="Process Images", command=start_cmd, highlightthicknes=0,
                               bg=color.accent, fg=color.fg, activeforeground=color.bg, activebackground=color.fg)

        self.abort = tk.Button(self, text="Close", command=abort_cmd,  highlightthickness=0, bg="#6D0000", fg="#E6B8DF", 
                                       activeforeground="#760000", activebackground="#E6B8DF")
        
        self.start.pack(side="left", padx=5)
        self.abort.pack(side="left", padx=5)


# The over-all frame for the initialization screen
# Packs in the contained sections from top down
# Button updates global_vars and closes the screen
class Initialization_Screen(tk.Frame):
    def __init__(self, master, lock):
        super().__init__(master, bg=color.bg)
        self.master = master
        self.pack(fill="both", expand=True)

        self.lock = lock
        self.lock.acquire()
        
        self.parameters = Parameter_Section(self)
        self.toggles = Toggles_Area(self)
        self.radio = Radio_Section(self)
        self.fuzziness_threshold = Entry_Box(self, "Fuzziness Threshold")
        self.confirmation_tolerance = Entry_Box(self, text="Confirmation Tolerance")
        self.cropping_buffer = Entry_Box(self, "Cropping Buffer")
        self.label_formatting = Label_Formatting(self)
        self.btns = Control_Buttons(self, self.finish, self.abort)

    # Update all the options in global_vars and close the screen
    # If one of the options cannot be updated, create a pop-up message and don't close the screen
    def finish(self):
        # These can't error, since their values are determined by radios or checkboxes (predetermined possibilities)
        global_vars.options["User Feedback"] = self.radio.user_feedback.get()
        global_vars.options["Fuzzy Matches"] = self.radio.fuzzy_matches.get()
        global_vars.options["OCR Technique"] = self.radio.ocr_technique.get()
        self.toggles.apply_toggles()

        # The fuzziness threshold is a user-entered value
        # Must be an int, but the user could enter any string
        # If the user didn't enter an int between 0 and 100, create a pop-up and don't close the screen
        try:
            threshold = int(self.fuzziness_threshold.entry.get())
            if 0 <= threshold <= 100:
                global_vars.options["Fuzziness Threshold"] = threshold
            else:
                raise Exception
        except Exception:
            messagebox.showinfo('ERROR','Fuzziness Threshold must be an integer between 0 and 100')
            return

        # Confirmation Tolerance works similarly to fuzziness threshold
        try:
            tolerance = int(self.confirmation_tolerance.entry.get())
            if 0 <= tolerance <= 100:
                global_vars.options["Confirmation Tolerance"] = tolerance
            else:
                raise Exception
        except Exception:
            messagebox.showinfo('ERROR','Confirmation Tolerance must be an integer between 0 and 100')
            return

        # ... as does the Cropping Buffer
        try:
            buffer = int(self.cropping_buffer.entry.get())
            global_vars.options["Cropping Buffer"] = buffer
        except Exception:
            messagebox.showinfo('ERROR','Cropping Buffer must be an integer')
            return

        # Validate that the specified label format is valid
        label_formatting = self.label_formatting.get()
        if label_formatting is None:
            messagebox.showinfo('ERROR', "Invalid Label Format")
            return


        # Validate that the Working Folder exists
        if not os.path.isdir(global_vars.parameters["Working Folder"]):
            messagebox.showinfo('ERROR', '"Working Folder" must be an existing folder')
            return

        # Create all the necessary directories
        global_vars.init_working_folder()

        # Validate that the datafile exists in the working folder
        if not os.path.isfile(global_vars.parameters["Data File"]):
            messagebox.showinfo('ERROR', '"data.csv" must exist in the Working Folder')
            return


        # Validate that the specified label format contains valid column names in the data file
        label_format, elements = label_formatting
        df = pd.read_csv(global_vars.parameters.get("Data File"))
        cols = df.columns
        for element in elements:
            if element not in cols:
                messagebox.showinfo('ERROR', f"Column '{element}' not found in Data File")
                return

        label_format = label_format.replace('{', '{0[')
        label_format = label_format.replace('}', ']}')
        global_vars.options["Label Format"] = label_format
            

        # Initialize the feedback queue if feedback is enabled
        if global_vars.options.get("User Feedback") != "None":
            paths = glob.glob(global_vars.parameters.get("Feedback Folder") + "/*.JPG")
            for path in paths:
                try:
                    headstone = Headstone.load(path)
                    e = headstone.error
                    if global_vars.options["User Feedback"] == "Full" or \
                    e is None or \
                    e.situation in (exceptions.LabelError.Situations.Multiple_Perfect, exceptions.LabelError.Situations.Debugging) or \
                    e.situation in (exceptions.LabelError.Situations.Fuzzy, exceptions.LabelError.Situations.Fuzzy_Tie) and global_vars.options["User Feedback"] != "Reject":
                        global_vars.feedback_queue.append(path)
                except Exception as e:
                    traceback.print_exc()

        global_vars.initialized = True
        self.lock.release()
        self.destroy()

    # Close the program without starting
    def abort(self):
        self.lock.release()
        self.destroy()
        self.master.destroy()