import tkinter as tk
from tkinter.filedialog import askopenfile
from tkinter import ttk
import os
from datetime import datetime
from Ac_growth import *
import json

class GUI:
    def __init__(self,master,version,mod_date):
        self.version = version
        self.mod_date = mod_date

        self.master = master

        # GUI variable definitions
        self.date = tk.StringVar(value = datetime.today().strftime('%y%m%d'))
        self.hour = tk.StringVar(value="23") # If IntVar, leading zeroes are interpreted as octal numbers
        self.minute = tk.StringVar(value="59") # If IntVar, leading zeroes are interpreted as octal numbers
        self.dose = tk.DoubleVar()
        self.extraction = tk.BooleanVar(value=False)
        self.targetmass = tk.DoubleVar()
        self.energy  = tk.DoubleVar()
        self.beamPath = tk.StringVar()
        self.last_data_datetime = tk.StringVar(value=" ")
        self.custom_power = tk.DoubleVar()
        self.sim_length = tk.IntVar()
        self.movingAvgLen = tk.IntVar()

        # Frame creation
        self.dir_frame()
        self.dose_frame()
        self.sim_frame()

        # Frame placement
        self.dirFR.grid(row=0,column=0,padx=2,pady=2)
        self.simFR.grid(row=1,column=0,padx=2,pady=2)
        self.doseFR.grid(row=2,column=0,padx=2,pady=2)

        self.dirFR.grid_columnconfigure(1,weight=1)
        self.simFR.grid_columnconfigure(1,weight=1)
        self.doseFR.grid_columnconfigure(1,weight=1)
        
# --------------------- H E L P E R   F U N C T I O N S --------------------- #
    def get_last_data(self,path):
        try:
            df = pd.read_csv(path)
            last_line = df.tail(1)
            print(last_line["Energy (MeV)"].item())
            self.energy.set(last_line["Energy (MeV)"].item())
            self.targetmass.set(last_line["Radium target mass (g)"].item())
            last_date = parse_date(last_line["Date"].item(),
                                   last_line["Time"].item())
            
            last_time = last_line["Time"].item()
            last_str = "Last data point: "+last_date.strftime('%y%m%d')+" "+last_time
            self.last_data_datetime.set(last_str)
        except Exception as ex:
            print("Failed to retrieve last line\nException: {}".format(ex))

# ----------------- P U S H   B U T T O N   C O M M A N D S ----------------- #
    def dir_cmd(self):
        self.beamPath.set(askopenfile().name)
        print("Beam path set to {}".format(self.beamPath.get()))

        # Open the data base and retrieve recent data for form autofill
        self.get_last_data(self.beamPath.get())

    def report_cmd(self):
        Ac_growth(self.beamPath.get())

    def submit_data_cmd(self):
        
        submit_day = datetime.strptime(self.date.get(), '%y%m%d').day
        submit_month = datetime.strptime(self.date.get(), '%y%m%d').month
        submit_year = datetime.strptime(self.date.get(), '%y%m%d').year
        
        submit_hour = str(self.hour.get()).zfill(2)
        
        if int(submit_hour) > 23:
            print("Hour must be between 0 and 23")
            return()

        
        submit_minute = str(self.minute.get()).zfill(2)
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
        # Open the data base and retrieve recent data for form autofill
        self.get_last_data(self.beamPath.get())

    def apply_sim_settings(self):
        with open ("Ac_growth_meta.txt","r") as f:
            meta = json.load(f)
        with open ("Ac_growth_meta.txt","w") as f:
            meta["Custom projection power"] = self.custom_power.get()
            meta["Project length (days)"] = self.sim_length.get()
            meta["Moving avg length"] = self.movingAvgLen.get()
            json.dump(meta,f,indent=4)
    
# ------------------- L A B E L   F R A M E   S E T U P S ------------------- #
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

    def sim_frame(self):
        self.simFR = tk.LabelFrame(self.master,
                                   text="Simulation settings")

        # Create elements
        self.customPowerLabel = ttk.Label(self.simFR,
                                          text="Enter custom power in Watts")
        self.customPowerEntry = ttk.Entry(self.simFR,
                                          textvariable=self.custom_power)
        self.simLengthLabel = ttk.Label(self.simFR,
                                        text="Enter the length of the simulation in days")
        self.simLengthEntry = ttk.Entry(self.simFR,
                                        textvariable=self.sim_length)
        self.movingAvgLenLabel = ttk.Label(self.simFR,
                                           text="Enter the length of the moving average in data points")

        self.movingAvgLenEntry = ttk.Entry(self.simFR,
                                           textvariable=self.movingAvgLen)
        self.applyPB = ttk.Button(self.simFR,
                                  text="Apply",
                                  command=self.apply_sim_settings)

        # Place elements
        self.customPowerLabel.grid(column=0,row=0,padx=2,pady=2)
        self.customPowerEntry.grid(column=1,row=0,padx=2,pady=2)

        self.simLengthLabel.grid(column=0,row=1,padx=2,pady=2)
        self.simLengthEntry.grid(column=1,row=1,padx=2,pady=2)

        self.movingAvgLenLabel.grid(column=0,row=2,padx=2,pady=2)
        self.movingAvgLenEntry.grid(column=1,row=2,padx=2,pady=2)

        self.applyPB.grid(column=0,row=3,padx=2,pady=2)
        
    def dose_frame(self):
        # Create elements
        self.doseFR = tk.LabelFrame(self.master,
                                    text="Dose data entry")

        self.last_data_label = ttk.Label(self.doseFR,
                                         textvariable=self.last_data_datetime)
        
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
                                   command=self.submit_data_cmd)

        # Place elements
        self.last_data_label.grid(column=0, row=0)
        self.date_label.grid(column=0, row=1)
        self.dateEntry.grid(column=1, row=1)
        
        self.end_time_label.grid(column=0,row=2)
        self.hourEntry.grid(column=1, row=2)
        self.colon_label.grid(column=2,row=2)
        self.minEntry.grid(column=3,row=2)
        
        
        self.dose_label.grid(column=0,row=3)
        self.doseEntry.grid(column=1,row=3)
        
        self.extraction_label.grid(column=0,row=4)
        self.extractionCB.grid(column=1,row=4)
        
        self.target_mass_label.grid(column=0,row=5)
        self.targetEntry.grid(column=1,row=5)
        
        self.energy_label.grid(column=0, row=6)
        self.energyEntry.grid(column=1, row=6)
        
        self.submitPB.grid(column=0,row=7,columnspan=5)
        
if __name__ == '__main__':

    __version__ = "0.0.1"
    last_modified = "10-August-2022"

    root = tk.Tk()

    app = GUI(root,__version__,last_modified)
    root.mainloop()
    root.destroy()
