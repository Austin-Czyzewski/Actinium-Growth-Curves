import tkinter as tk
from tkinter import ttk

class GUI:
    def __init__(self,master,version,mod_date):
        self.version = version
        self.mod_date = mod_date

        self.master = master
        

        # GUI variable definitions
        self.hour = tk.DoubleVar(value=24)
        self.minute = tk.DoubleVar(value=59)
        self.dose = tk.DoubleVar()
        self.extraction = tk.BooleanVar(value=False)
        self.targetmass = tk.DoubleVar(value=38.0)

        # Frame creation
        self.dose_frame()

        # Frame placement
        self.doseFR.grid(row=0,column=0)
        self.doseFR.grid_columnconfigure(1,weight=1)
        
        
    def dose_frame(self):
        # Create elements
        self.doseFR = tk.LabelFrame(self.master,
                                    text="Dose data entry")
        self.end_time_label = ttk.Label(self.doseFR,
                                        text="End time (24hr format)")
        self.hourEntry = ttk.Entry(self.doseFR,
                                   textvariable=self.hour)
        self.colon_label = ttk.Label(self.doseFR,
                                     text=":")
        self.minEntry = ttk.Entry(self.doseFR,
                                  textvariable=self.minute)
        
        self.dose_label = ttk.Label(self.doseFR,
                                    text="Dose (Gy)")
        self.doseEntry = ttk.Entry(self.doseFR,
                                   textvariable=self.dose)
        self.extraction_label = ttk.Label(self.doseFR,
                                          text="Ac-225 extraction")
        self.extractionCB = ttk.Checkbutton(self.doseFR,
                                         variable=self.extraction)
        self.target_mass_label = ttk.Label(self.doseFR,
                                           text="Target mass (mg)")
        self.targetEntry = ttk.Entry(self.doseFR,
                                     textvariable=self.targetmass)
        self.submitPB = ttk.Button(self.doseFR,
                                   text="Submit",
                                   command=self.submit_data)

        # Place elements
        self.end_time_label.grid(column=0,row=0)
        self.hourEntry.grid(column=1, row=0)
        self.colon_label.grid(column=2,row=0)
        self.minEntry.grid(column=3,row=0)
        
        self.dose_label.grid(column=0,row=1)
        self.doseEntry.grid(column=1,row=1)
        
        self.extraction_label.grid(column=0,row=2)
        self.extractionCB.grid(column=1,row=2)
        
        self.target_mass_label.grid(column=0,row=3)
        self.targetEntry.grid(column=1,row=3)
        
        self.submitPB.grid(column=0,row=4,columnspan=4)

    def submit_data(self):
        pass
                                   
if __name__ == '__main__':

    __version__ = "0.0.1"
    last_modified = "26-July-2022"

    root = tk.Tk()

    app = GUI(root,__version__,last_modified)
    root.mainloop()
    root.destroy()
