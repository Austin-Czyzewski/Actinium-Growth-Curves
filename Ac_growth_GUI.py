import tkinter as tk
from tkinter import ttk
import glob
import os

global beam_data_path
beam_data_path = glob.glob("beam*.csv")[0]
from datetime import datetime

# print(datetime.strptime(test_time, '%y%m%d').day)

class GUI:
    def __init__(self,master,version,mod_date):
        self.version = version
        self.mod_date = mod_date

        self.master = master
        

        # GUI variable definitions
        self.date = tk.StringVar(value = datetime.today().strftime('%y%m%d'))
        self.hour = tk.DoubleVar(value=24)
        self.minute = tk.DoubleVar(value=59)
        self.dose = tk.DoubleVar()
        self.extraction = tk.BooleanVar(value=False)
        self.targetmass = tk.DoubleVar(value=38.0)
        self.energy  = tk.DoubleVar(value = 13.6)

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
        
        self.date_label = ttk.Label(self.doseFR,
                                    text = "Date (YYMMDD)")
        
        self.dateEntry = ttk.Entry(self.doseFR, 
                                   textvariable=self.date)
        
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
        
        self.energy_label = ttk.Label(self.doseFR,
                                      text = "Beam Energy (MeV)")
        
        self.energyEntry = ttk.Entry(self.doseFR,
                                     textvariable = self.energy)
        
        self.submitPB = ttk.Button(self.doseFR,
                                   text="Submit",
                                   command=self.submit_data)

        # Place elements
        self.date_label.grid(column=0, row=0)
        self.dateEntry.grid(column=1, row=0)
        
        self.end_time_label.grid(column=0,row=1)
        self.hourEntry.grid(column=1, row=1)
        self.colon_label.grid(column=2,row=1)
        self.minEntry.grid(column=3,row=1)
        
        
        self.dose_label.grid(column=0,row=2)
        self.doseEntry.grid(column=1,row=2)
        
        self.extraction_label.grid(column=0,row=3)
        self.extractionCB.grid(column=1,row=3)
        
        self.target_mass_label.grid(column=0,row=4)
        self.targetEntry.grid(column=1,row=4)
        self.energy_label.grid(column=2, row=4)
        self.energyEntry.grid(column=3, row=4)
        
        self.submitPB.grid(column=0,row=5,columnspan=5)

    def submit_data(self):
        
        submit_day = datetime.strptime(self.date.get(), '%y%m%d').day
        submit_month = datetime.strptime(self.date.get(), '%y%m%d').month
        submit_year = datetime.strptime(self.date.get(), '%y%m%d').year
        submit_hour = str(int(self.hour.get())).zfill(2)
        submit_minute = str(int(self.minute.get())).zfill(2)
        submit_energy = self.energy.get()
        submit_dose = self.dose.get()
        submit_target_mass = self.targetmass.get()
        submit_extraction = ("YES" if self.extraction.get() == True else "NO")
        
        with open(beam_data_path, 'a') as file:
            file.write(f"{submit_month}/{submit_day}/{submit_year} {submit_hour}:{submit_minute},")
            file.write(f"{submit_month}/{submit_day}/{submit_year},")
            file.write(f"{submit_hour}:{submit_minute},")
            file.write(f"{submit_energy},{submit_dose},0,{submit_target_mass},")
            file.write(f"{submit_extraction}\n")
        pass
                                   
if __name__ == '__main__':

    __version__ = "0.0.1"
    last_modified = "26-July-2022"

    root = tk.Tk()

    app = GUI(root,__version__,last_modified)
    root.mainloop()
    root.destroy()
