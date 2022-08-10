import tkinter as tk
from tkinter.filedialog import askopenfile
from tkinter import ttk
import os
from datetime import datetime

def get_last_data(path):
    with open(path,'r') as f:
        lines = f.readlines()
        last_line = lines[-1]
        
        try:              
            print(last_line)
            last_energy = float(last_line.split(",")[3])
            print(last_energy)
            last_target_mass = float(last_line.split(",")[-2])*1000
            print(last_target_mass)
            
        except:
            print("Failed to extract last line data")
            last_energy = 15
            last_target_mass = 100
        return(last_energy, last_target_mass)


class GUI:
    def __init__(self,master,version,mod_date):
        self.version = version
        self.mod_date = mod_date

        self.master = master

        # GUI variable definitions
        self.date = tk.StringVar(value = datetime.today().strftime('%y%m%d'))
        self.hour = tk.DoubleVar(value=23)
        self.minute = tk.DoubleVar(value=59)
        self.dose = tk.DoubleVar()
        self.extraction = tk.BooleanVar(value=False)
        self.targetmass = tk.DoubleVar()
        self.energy  = tk.DoubleVar()
        self.beamPath = tk.StringVar()

        # Frame creation
        self.dose_frame()
        self.dir_frame()

        # Frame placement
        self.dirFR.grid(row=0,column=0)
        self.doseFR.grid(row=1,column=0)

        self.dirFR.grid_columnconfigure(1,weight=1)
        self.doseFR.grid_columnconfigure(1,weight=1)
        
    def dir_cmd(self):
        self.beamPath.set(askopenfile().name)
        print("Beam path set to {}".format(self.beamPath.get()))
        energy, mass = get_last_data(self.beamPath.get())
        self.energy.set(energy)
        self.targetmass.set(mass)
        
    def dir_frame(self):
        self.dirFR = tk.LabelFrame(self.master,
                                   text="Choose a beam data file")

        # Create elements
        self.beamdirLabel = ttk.Label(self.dirFR,
                                      text="Beam data database: ")
        self.ask_filePB = ttk.Button(self.dirFR,
                                     text="Select",
                                     command=self.dir_cmd)
        self.reportPB = ttk.Button(self.dirFR,
                                   text="Create Report",
                                   command=self.report_cmd)

        # Place elements
        self.beamdirLabel.grid(column=0,row=0)
        self.ask_filePB.grid(column=1,row=0,padx=2,pady=2)
        self.reportPB.grid(column=2,row=0,padx=2,pady=2)

    def report_cmd(self):
        pass
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
        self.energy_label.grid(column=0, row=5)
        self.energyEntry.grid(column=1, row=5)
        
        self.submitPB.grid(column=0,row=6,columnspan=5)

    def submit_data(self):
        
        submit_day = datetime.strptime(self.date.get(), '%y%m%d').day
        submit_month = datetime.strptime(self.date.get(), '%y%m%d').month
        submit_year = datetime.strptime(self.date.get(), '%y%m%d').year
        
        submit_hour = str(int(self.hour.get())).zfill(2)
        
        if int(submit_hour) > 23:
            print("Hour must be between 0 and 23")
            return()
            
        submit_minute = str(int(self.minute.get())).zfill(2)
        submit_energy = self.energy.get()
        submit_dose = self.dose.get()
        submit_target_mass = self.targetmass.get()/1000
        submit_extraction = ("YES" if self.extraction.get() == True else "NO")
        
        with open(self.beamPath.get(), 'a') as file:
            file.write(f"{submit_month}/{submit_day}/{submit_year} {submit_hour}:{submit_minute},")
            file.write(f"{submit_month}/{submit_day}/{submit_year},")
            file.write(f"{submit_hour}:{submit_minute},")
            file.write(f"{submit_energy},{submit_dose},0,{submit_target_mass},")
            file.write(f"{submit_extraction}\n")
            
        self.dose.set(0)
                                   
if __name__ == '__main__':

    __version__ = "0.0.1"
    last_modified = "10-August-2022"

    root = tk.Tk()

    app = GUI(root,__version__,last_modified)
    root.mainloop()
    root.destroy()
