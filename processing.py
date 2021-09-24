import tkinter as tk
import color_palette
import global_vars
from feedback import Feedback_Screen

color = color_palette.color_pallette
global_vars = global_vars.global_vars


# Informs user of program progress, or of current state while shutting down
class Progress_Label(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=color.bg)
        self.pack(padx=20, pady=(20,0))

        self.current_image = 0
        self.text = "Processing Image\t{}\tof\t{}"

        self.label = tk.Label(self, bg=color.bg, fg=color.fg, padx=10)
        self.label.pack(side="left")


    # Following three methods:
    # Update the text on the label either to match the program's progress or indicate shutdown state
    
    def update(self):
        self.label.config(text=self.text.format(global_vars.current_image, global_vars.num_images))

    def abort(self):
        self.label.config(text="Aborting... please wait")

    def done(self):
        self.label.config(text="Done")


# Informs user of the number of images waiting for user feedback
class Feedback_Queue_Label(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=color.bg)
        self.pack(padx=20, pady=(15, 0))

        self.text = "Feedback Queue Length:\t{}"

        self.label = tk.Label(self, bg=color.bg, fg=color.fg, padx=10)
        self.label.pack(side="left")

    # Update the value on the label to match the length of the feedback queue
    def update(self):
        self.label.config(text=self.text.format(len(global_vars.feedback_queue)))


# Switches between the processing screen and the feedback screen
# Only shown when there are images in the feedback queue
class Switch_To_Feedback_Button(tk.Frame):
    def __init__(self, master, command):
        super().__init__(master, bg=color.bg)
        self.pack(padx=20, pady=(15, 0))

        self.master = master

        self.btn = tk.Button(self, text="Provide Feedback", command=command, 
                             highlightthicknes=0, bg=color.accent, fg=color.fg,
                             activeforeground=color.bg, activebackground=color.fg)

    # Dynamically display the button depending on if there are images in the feedback queue
    def update(self):
        if len(global_vars.feedback_queue) > 0:
            self.btn.pack()
        else:
            self.btn.pack_forget()


# Button for user to prematurely halt the program, or close it once it has been halted
class Abort_Button(tk.Frame):
    def __init__(self, master, command_1, command_2):
        super().__init__(master, bg=color.bg)
        self.pack(padx=20, pady=(15,20))
        
        self.master = master
        self.command_2 = command_2

        self.btn = tk.Button(self, text="Abort Processing", command=command_1,
                            highlightthickness=0, bg="#6D0000", fg="#E6B8DF", 
                            activeforeground="#760000", activebackground="#E6B8DF")
        self.btn.pack()

    def abort(self):
        self.btn.pack_forget()

    def done(self):
        self.btn.config(text="Close", command=self.command_2)

        if not self.btn.winfo_ismapped():
            self.btn.pack()


# Displays to the user the current progress on processing the images and
# the number of images waiting for user feedback (if feedback is enabled)
# User can switch into feedback mode, or abort the program altogether
class Processing_Screen(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=color.bg)
        self.master = master
        self.pack(fill="both", expand=True)
        self.feedback_screen = Feedback_Screen(master, self)

        self.state = "Running"

        self.progress_label = Progress_Label(self)

        if global_vars.options["User Feedback"] != "None":
            self.feedback_queue_label = Feedback_Queue_Label(self)
            self.feedback_button = Switch_To_Feedback_Button(self, self.switch_to_feedback_screen)

        self.abort_button = Abort_Button(self, self.abort, self.close)

        self.update()


    # Changes the appearance of the interface so the user knows the system is aborting
    def abort(self):
        if self.state == "Running":
            self.state = "Aborting"
            self.progress_label.abort()
            self.abort_button.abort()


    # Changes the appearance of the interface so the user knows the system has finished processing
    def done(self):
        self.state = "Done"
        self.progress_label.done()
        self.abort_button.done()
        

    # Closes the user interface
    def close(self):
        if self.state == "Done":
            self.feedback_screen.destroy()
            self.destroy()
            self.master.destroy()


    # Switch the entire UI to the Feedback Screen
    def switch_to_feedback_screen(self):
        self.feedback_screen.update()
        self.pack_forget()
        self.feedback_screen.pack(fill="both", expand=True)


    # Called by the driver to update the progress
    # Returns True if the program is aborting, so the driver knows not to process another image
    def update(self):
        if self.state == "Aborting":
            return True

        self.progress_label.update()

        if global_vars.options["User Feedback"] != "None":
            self.feedback_queue_label.update()
            self.feedback_button.update()

        return False
