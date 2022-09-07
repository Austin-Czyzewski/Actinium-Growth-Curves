''' Python Plotting Template
 Glenn Clapp
 Austin Czyzewski
 23 April 2022

 Based on work by
 Chad Denbrock
 December 2020
 
 Niowave, Inc.
 '''
# ------------------- L I B R A R Y   I M P O R T S ------------------------- #

import random
from matplotlib import pyplot as plt
from matplotlib import transforms  
import matplotlib 
import numpy as np 
from scipy import interpolate
import datetime as DT
from matplotlib.dates import DateFormatter
import pandas as pd
import json
import warnings
warnings.filterwarnings("ignore", message="FixedFormatter should only be used together with FixedLocator")

# ------------------- P L O T   S E T T I N G S  ---------------------------- #

matplotlib.rcParams['savefig.dpi']  = 300
matplotlib.rcParams['font.size']    = 16
matplotlib.rcParams['mathtext.fontset'] = 'stix'
matplotlib.rcParams['font.family'] = 'STIXGeneral'

# ------------------ H E L P E R  F U N C T I O N S ------------------------- #
def parse_dates(DF, date_col, time_col):
    new_series = []
    
    for i,row in DF.iterrows():
        new_datetime = parse_date(row[date_col],row[time_col])
        new_series.append(new_datetime)

    return(pd.Series(new_series))

def parse_date(date, time):
    try:
        m,D,Y = date.split("/")
        H,M = time.split(":")
        return(DT.datetime(int(Y),int(m),int(D),int(H),int(M)))
    except:
        print("Failed to parse date. Expected a date and time, received: {} {}".format(date, time))

def calculate_delta(df):
    delta = []
    for i,t in enumerate(df["Elapsed time (s)"]):
        if i==0:
            delta.append(df["Elapsed time (s)"][0])
        else:
            delta.append(t-df["Elapsed time (s)"][i-1])

    df["dt (s)"] = delta
    
def reaction_calculator(df,ra_225_init,ac_225_init,Reaction_Rate_Modification_Factor):
    '''Takes a data frame with "Integrated Power (kWhr from Acc)", "dt (s)",
    "Energy (MeV)", and "Radium target mass (g)" columns and appends "power",
    "electrons", "reaction rate per gram", "reactions per second", "Radium-225",
    "Actinium-225", "Radium-225 Activity (mCi)", and "Actinium-225 Activity (mCi)"
    '''

    # ------------------- D E C A Y   R A T E S  ---------------------------- #
    ac_225_hl = 8.57e5 # 9.9 days
    ra_225_hl = 1.29e6 # 14.9 days

    ac_225_l = np.log(2)/ac_225_hl
    ra_225_l = np.log(2)/ra_225_hl
    
    df["power"] = df["Integrated Power (kWhr from Acc)"] / (df["dt (s)"] / 3600)*1000
    df["electrons"] = df["power"]/(df["Energy (MeV)"]* 1e6 * 1.6e-19)
    df["reaction rate per gram"] = reaction_rate_calculator(df["Energy (MeV)"],Reaction_Rate_Modification_Factor)
    df["reactions per second"] = df["reaction rate per gram"] * df["Radium target mass (g)"] * df["electrons"]

    Ra225 = []
    Ac225 = []
    
    for i,row in df.iterrows():
        if i > 0:
            R = row["reactions per second"]
            Ra225decays = ra_225_l*Ra225[-1]
            Ra225.append(Ra225[-1] + (R-Ra225decays)*row["dt (s)"])
            Ac225decays = ac_225_l * Ac225[-1]
            try:
                if row['Extraction'].lower() == 'yes':
                    Ac225.append(0)
                else:
                    Ac225.append(Ac225[-1] + (Ra225decays - Ac225decays)*row["dt (s)"])
            except:
                Ac225.append(Ac225[-1] + (Ra225decays - Ac225decays)*row["dt (s)"])
                
            else:
                pass
        else:
            Ra225.append(ra_225_init)
            Ac225.append(ac_225_init)            
            
    df["Radium-225"] = Ra225
    df["Actinium-225"] = Ac225
    df["Radium-225 Activity (mCi)"] = df["Radium-225"] * ra_225_l / 3.7e7
    df["Actinium-225 Activity (mCi)"] = df["Actinium-225"] * ac_225_l / 3.7e7
        
    df.reset_index()
    
def reaction_rate_calculator(energy,Reaction_Rate_Modification_Factor):
    '''Reaction rates given in rxns/g/e for Green Curve Geometry at 10 ml
    flat RaT solution volume'''
    # energy_list         = [10.0,        11.0,       12.0,       13.0,       14.0,       15.0]
    energy_list         = [9,10,11,12,13,14,15,16,17,18,19,20]
    # reaction_rate_list  = [9.970e-7,    2.058e-6,   3.862e-6,   6.494e-6,   9.636e-6,   1.283e-5]
    reaction_rate_list  = [1.506e-7,3.412e-7,6.668e-7,1.206e-6,1.982e-6,\
                           2.909e-6,3.872e-6,4.810e-6,5.752e-6,6.621e-6,\
                           7.450e-6,8.315e-6]
        
    reaction_rate_list = [original * Reaction_Rate_Modification_Factor for original in reaction_rate_list]

    interpolate_func    = interpolate.interp1d(energy_list,reaction_rate_list)
    reaction_rate       = interpolate_func(energy)
    return reaction_rate


def dose_to_accumulated_power(dose,mGy_min_watt):
    '''takes a dose measurement in Gy and estimates an integrated power in kWhr
    required to produce that dose. Based on historical measurements.'''
    return dose/mGy_min_watt/60

def power_to_integrated_power(power,dt):
    '''takes power in W and dt in seconds and returns kwHr of integrated power'''
    return(power/1000*dt/3600)

def createPowerProjection(df,mean_power,std_power,stds_from_avg,include_schedule=False):
    '''Takes a mean power from historical data, a standard deviation of power
    from historical data and populates the integrated power column of the given
    data frame'''
    Schedule = "Schedule.csv"
    SchDF = pd.read_csv(Schedule)
    SchDF["Start date and time"] = parse_dates(SchDF,"Start date","Start time")
    SchDF["End date and time"] = parse_dates(SchDF,"End date","End time")
    print(SchDF.head())

    sims = []
    for i in range(10):
        power = []
        extraction = []
        for d in df["Date and Time"]:
            for i,row in SchDF.iterrows():
                if row["Start date and time"] < d <= row["End date and time"]:
                    new_power = 0
                    if row["Extraction"] == "YES":
                        extraction.append("YES")
                    
                    else:
                        extraction.append("NO")
                    break
                else:
                    new_power = -1
                    while new_power < 0:
                        new_power = random.normalvariate(mean_power,std_power)
                    extraction.append("NO")
                    
            power.append(new_power)
        sims.append(power)
    tempDF = pd.DataFrame(sims)

    mean_power = []
    upper_power = []
    lower_power = []
    for col in tempDF:
        mean = tempDF[col].mean()
        sd = tempDF[col].std()
        
        mean_power.append(mean)
        upper_power.append(mean+stds_from_avg*sd)
        lower_power.append(mean-stds_from_avg*sd)

    return(upper_power,mean_power,lower_power,extraction)

def Ac_growth(beam_data):
    # ------------------- R E T R I E V E   D A T A  ---------------------------- #

    # Import data from file
    with open("Ac_growth_meta.txt","r") as f:
        meta = json.load(f)

    # ----------------- S C R I P T   S E T T I N G S  -------------------------- #

    Adjustable_Ratio = meta["Adjustable ratio"]
    Fudge_Factor = meta["Fudge factor"]
    Reaction_Rate_Modification_Factor = meta["Reaction rate modification factor"]
    mGy_min_watt = meta["mGy per min per watt"]

    DF = pd.read_csv(beam_data,parse_dates=True)
    DFmeas = pd.read_csv("Target measurements.csv")

    DF["Date and Time"] = parse_dates(DF,"Date","Time")
    DF["Elapsed time (s)"] = (DF["Date and Time"] - DF["Date and Time"][0]).dt.total_seconds()
    calculate_delta(DF)

    # Create calculated data
    DF["Integrated Power (kWhr from Acc)"] = dose_to_accumulated_power(DF["Accumulated Dose"],
                                                                       mGy_min_watt)/Fudge_Factor

    phase1end = DT.datetime(2022,8,19,9,0)
##    for i,row in DF.iterrows():
##        if row["Date and Time"].to_pydatetime() < phase1end:
##            DF.at[i,"Integrated Power (kWhr from Acc)"] = DF.at[i,"Integrated Power (kWhr from Acc)"]*Fudge_Factor/1
##        else:
##            DF.at[i,"Integrated Power (kWhr from Acc)"] = DF.at[i,"Integrated Power (kWhr from Acc)"]*Fudge_Factor/1
    DF["Dose rate (Gy/s)"] = DF["Accumulated Dose"]/DF["dt (s)"]
    
    start_time = DF["Date and Time"][0].to_pydatetime()

    latest_time = DF["Date and Time"].tail(1).item().to_pydatetime()

    # ------------------------ Calculation Algorithm          ---------------- #

    # initial_ra_225_N = 32.4 * 3.7e4 / ra_225_l # Measured activity prior to start
    # initial_ac_225_N = 10.0 * 3.7e4 / ac_225_l # Measured activity prior to start
    initial_ra_225_N = 0
    initial_ac_225_N = 0
    reaction_calculator(DF,
                        initial_ra_225_N,
                        initial_ac_225_N,
                        Reaction_Rate_Modification_Factor)

    latest_Ac225 = DF["Actinium-225 Activity (mCi)"].tail(1).item()

    print("Total integrated beam power: {:4.2f} kWhr".format(DF["Integrated Power (kWhr from Acc)"].sum()))
    print("Activity of Ac-225 at the last reported time: {:4.3f} mCi".format(latest_Ac225))

    # ------------------------ Projection Algorithm          ---------------- #
    #######################
    # Projection settings #
    #######################

    mask = (DF['Extraction'] == 'NO')
    masked_df = DF[mask]

    Dose_mean = meta["Project dt (s)"]*masked_df["Dose rate (Gy/s)"].tail(meta["Moving avg length"]).mean()
    Dose_std = meta["Project dt (s)"]*masked_df["Dose rate (Gy/s)"].tail(meta["Moving avg length"]).std()
    
    Projected_power = dose_to_accumulated_power(Dose_mean,mGy_min_watt)/Fudge_Factor
    Power_std = dose_to_accumulated_power(Dose_std,mGy_min_watt)/Fudge_Factor

    End = DF["Date and Time"].tail(1).item().to_pydatetime() # Get the last date
    
    # Create a series of datetime objects with parameters from meta data for projection
    dates = [End + DT.timedelta(seconds=x*meta["Project dt (s)"]) for x in range(int(86400*meta["Project length (days)"]/meta["Project dt (s)"]))]

    #######################
    # Projections         #
    #######################
    DF_proj = pd.DataFrame(columns=masked_df.columns)
    DF_proj["Date and Time"] = dates
    upper, mean, lower, extraction = createPowerProjection(DF_proj,
                                                           Projected_power,
                                                           Power_std,
                                                           meta["Standard deviations from average"],
                                                           include_schedule=False)
    
    DF_proj["Energy (MeV)"] = float(meta["Project energy"])
    DF_proj["Radium target mass (g)"] = float(meta["Radium target mass (g)"])
    DF_proj["Elapsed time (s)"] = (DF_proj["Date and Time"] - DF["Date and Time"][0]).dt.total_seconds()
    calculate_delta(DF_proj)
    DF_proj["Extraction"] = extraction

    DF_custom = DF_proj.copy()
    DF_lower = DF_proj.copy()
    DF_upper = DF_proj.copy()
    
    DF_proj["Integrated Power (kWhr from Acc)"] = mean
    DF_lower["Integrated Power (kWhr from Acc)"] = lower
    DF_upper["Integrated Power (kWhr from Acc)"] = upper

    Interval = meta["Standard deviations from average"]*Power_std
                           
    DF_custom["Integrated Power (kWhr from Acc)"] = meta["Custom projection power"]*(DF_custom["dt (s)"]/3600)/1000

    reaction_calculator(DF_proj,
                        DF.tail(1)["Radium-225"].item(),
                        DF.tail(1)["Actinium-225"].item(),
                        Reaction_Rate_Modification_Factor)

    reaction_calculator(DF_lower,
                        DF.tail(1)["Radium-225"].item(),
                        DF.tail(1)["Actinium-225"].item(),
                        Reaction_Rate_Modification_Factor)

    reaction_calculator(DF_upper,
                        DF.tail(1)["Radium-225"].item(),
                        DF.tail(1)["Actinium-225"].item(),
                        Reaction_Rate_Modification_Factor)

    reaction_calculator(DF_custom,
                        DF.tail(1)["Radium-225"].item(),
                        DF.tail(1)["Actinium-225"].item(),
                        Reaction_Rate_Modification_Factor)

    DF.to_csv("output.csv")
    DF_proj.to_csv("projection.csv")

    # ------------------- B E G I N   P L O T T I N G ---------------------------- #

    fig, ax = plt.subplots(1,1,figsize=(11,8.5)) 

    ax.plot(DF["Date and Time"], DF["Radium-225 Activity (mCi)"],'r')
    ax.plot(DF["Date and Time"], DF["Actinium-225 Activity (mCi)"],'g')
        
    # Plot projections
    ax.plot(DF_proj["Date and Time"], DF_proj["Radium-225 Activity (mCi)"],'r--')
    ax.plot(DF_proj["Date and Time"], DF_proj["Actinium-225 Activity (mCi)"],'g--')
    ax.plot(DF_custom["Date and Time"], DF_custom["Radium-225 Activity (mCi)"],'r:')
    ax.plot(DF_custom["Date and Time"], DF_custom["Actinium-225 Activity (mCi)"],'g:')


    ax.fill_between(DF_upper["Date and Time"],
                    DF_upper["Radium-225 Activity (mCi)"], DF_lower["Radium-225 Activity (mCi)"],
                    color='red',alpha=0.2)

    ax.fill_between(DF_upper["Date and Time"],
                    DF_upper["Actinium-225 Activity (mCi)"], DF_lower["Actinium-225 Activity (mCi)"],
                    color='green',alpha=0.2)


    # Plotting black dashed line at last reported data
    ylim    = (0,meta["plot y-scale"])
    ax.plot([latest_time,latest_time],[ylim[0],ylim[1]],'k--')
    ax.set_ylim(0.0,ylim[1])

    # Plot target measurements
    try:
        for index,pt in DFmeas.iterrows():
            m,d,y = pt["Date"].split("/")
            h,M = pt["Time"].split(":")
            date = DT.datetime(int(y),int(m),int(d),int(h),int(M))
            data = pt["Ac-225"]
            print(date,data)
            ax.plot(date,float(data),'kx',ms=10)
            ax.text(date,float(data),data,ha='right',va='center',fontsize = 10) 

    except:
        print("#"*60+'\n',"No measurements to display",'\n'+"#"*60)

    caption_text = "{:.3f}".format(latest_Ac225)
    ax.annotate(caption_text,xy = (latest_time,latest_Ac225),
                xytext = (20,-20),
                textcoords='offset points',
                arrowprops=dict(arrowstyle="->"),
                ha = 'left',
                va = 'center',
                fontsize = 16)
                
    ax.set_xticklabels(ax.get_xticklabels(), rotation = 45, fontsize = 14);
    ax.set(
         title      = r'Niowave Production Milestones $^{225}$Ac Campaign',
         ylabel     = r'Activity (mCi)',
         ylim       = ylim,
         yscale     = 'linear'
    )
    date_form = DateFormatter("%m/%d")
    ax.xaxis.set_major_formatter(date_form)

    ax.xaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator(3))
    ax.yaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator(5))
    ax2 = ax.twinx()
    ax2.set_ylim(ylim)
    ax2.yaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator(5))

    ax.yaxis.grid(True, which = 'major')
    ax.xaxis.grid(True, which = 'major')
    ax.yaxis.grid(True, which = 'minor', alpha = 0.25)
    ax.xaxis.grid(True, which = 'minor', alpha = 0.25)
    legend_list = [r'$^{225}$Ra',r'$^{225}$Ac']
    ax.legend(legend_list,loc = 'upper left')

    # Add caption below xlabel
    caption_text = ("The black dotted line shows the date of the most recent irradiation data. \n\
    Assumptions for projection: {:2.0f} mg RaT, {:3.0f} +/- {:3.0f} W and {:3.0f} W with proper beam steering.".format(1000*meta["Radium target mass (g)"],
                                                                                                                                      Projected_power*1000,
                                                                                                                                      Interval*1000,
                                                                                                                                      meta["Custom projection power"]))
    trans = transforms.blended_transform_factory(
         ax.transAxes, fig.transFigure
    )              # Makes x axis 'axes' coordinates and y axis 'figure' coordinates
    ax.text(0.5, 0.03, caption_text, ha = 'center', va = 'top', fontsize = 12, transform = trans)

    # Add current date to upper right corner of plot

    date_string = DT.date.today().strftime('%B %d, %Y')
    ax.text(1.00,1.001,date_string,fontsize = 8, ha = 'right', va = 'bottom', transform = ax.transAxes)

    # Save figure as a png
    date_string_2   = DT.date.today().strftime('%Y%m%d')
    file_name = f'{date_string_2}_ac_225_growth_curve.png'
    plt.savefig(file_name, bbox_inches = 'tight')
    plt.savefig("current_ac_225_growth_curve.png")

    # ------------------- P O W E R   P L O T T I N G ---------------------------- #

    fig, ax = plt.subplots(1,1,figsize=(11,8.5))
        
    ax.plot(DF["Date and Time"],DF["power"])

    ylim = (0.0,ax.get_ylim()[1])

    ax.set_xticklabels(ax.get_xticklabels(), rotation = 45, fontsize = 16);
    ax.set(
         title      = r'Niowave R&D milestones $^{225}$Ac Campaign - Beam Power',
         ylabel     = r'Power (W)',
         ylim       = ylim,
         yscale     = 'linear'
    )
    date_form = DateFormatter("%m/%d")
    ax.xaxis.set_major_formatter(date_form)

    ax.xaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator(2))
    ax.yaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator(2))
    ax2 = ax.twinx()
    ax2.set_ylim(ylim)
    ax2.yaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator(2))

    ax.yaxis.grid(True, which = 'major')
    ax.xaxis.grid(True, which = 'major')
    ax.yaxis.grid(True, which = 'minor', alpha = 0.25)
    ax.xaxis.grid(True, which = 'minor', alpha = 0.25)

    # Add caption below xlabel

    caption_text = f'''Projected power taken averaging after 3/24 at 10:28 am.'''
    trans = transforms.blended_transform_factory(
         ax.transAxes, fig.transFigure
    )              # Makes x axis 'axes' coordinates and y axis 'figure' coordinates

    # Add current date to upper right corner of plot
    date_string = DT.date.today().strftime('%B %d, %Y')
    ax.text(1.00,1.001,date_string,fontsize = 8, ha = 'right', va = 'bottom', transform = ax.transAxes)


    # Save figure as a png
    date_string_2   = DT.date.today().strftime('%Y%m%d')
    file_name = f'{date_string_2}_ac_225_growth_curve_power.png'
    plt.savefig(file_name, bbox_inches = 'tight')

if __name__ == '__main__':
    Ac_growth("irradiation log.csv")
