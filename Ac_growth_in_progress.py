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

# ----------------- S C R I P T   S E T T I N G S  -------------------------- #

Adjustable_Ratio = False
Fudge_Factor = 1.56
Reaction_Rate_Modification_Factor = 1.0
mGy_min_watt = 1.3 #mGy/minute/Watt loosely calibrated last run for IC position

# ------------------ H E L P E R  F U N C T I O N S ------------------------- #
def parse_dates(Series):
    new_series = []
    for d in Series:
        new_series.append(parse_date(d))

    return(pd.Series(new_series))

def parse_date(date):
    d,t = date.split(" ")
    m,D,Y = d.split("/")
    H,M = t.split(":")
    return(DT.datetime(int(Y),int(m),int(D),int(H),int(M)))

def reaction_calculator(df,ra_225_init,ac_225_init):
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
    df["reaction rate per gram"] = reaction_rate_calculator(df["Energy (MeV)"])
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
    
def reaction_rate_calculator(energy):
    '''Reaction rates given in rxns/g/e for Green Curve Geometry at 1.0 ml solution volume'''
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


def dose_to_accumulated_power(dose,dt):
    '''takes a dose measurement in Gy and a time step in seconds from the
    previous measurement and estimates an integrated power in kWhr required to
    produce that dose.'''
    return dose/mGy_min_watt/60

def power_to_integrated_power(power,dt):
    '''takes power in W and dt in seconds and returns kwHr of integrated power'''
    return(power/1000*dt/3600)

def main(beam_data):
    
        
    # ------------------- R E T R I E V E   D A T A  ---------------------------- #

    # Import data from file
    with open("Ac_growth_meta.txt","r") as f:
        meta = json.load(f)
        
    DF = pd.read_csv(beam_data,parse_dates=True)
    DFmeas = pd.read_csv("Target measurements.csv")

    DF["Date and Time"] = parse_dates((DF["Date and Time"]))
    DF["Elapsed time (s)"] = (DF["Date and Time"] - DF["Date and Time"][0]).dt.total_seconds()
    delta = []
    for i,t in enumerate(DF["Elapsed time (s)"]):
        if i==0:
            delta.append(DF["Elapsed time (s)"][0])
        else:
            delta.append(t-DF["Elapsed time (s)"][i-1])

    DF["dt (s)"] = delta

    # Create calculated data
##    DF["Integrated Power (kWhr from Acc)"] = DF["Accumulated Dose"].apply(dose_to_accumulated_power)
    
    DF["Integrated Power (kWhr from Acc)"] = dose_to_accumulated_power(DF["Accumulated Dose"],DF["dt (s)"])
    Integrated_power_list = list(DF["Integrated Power (kWhr from Acc)"])
    
    start_time = DF["Date and Time"][0].to_pydatetime()

    # Scale power data because reasons... Ask Chad about this
    index_of_3_18_measurement   = 38
    index_of_ra_addition        = 183
    Acc_Iso_power_ratio         = [1.56, 2.7, 1.56] # 1.56 up to 3/18 measurement
                                            # 2.0 from 3/18 to 4/5
                                            # 1.56 again projecting
                                    
    Integrated_power_list   = np.array(Integrated_power_list)

    if Adjustable_Ratio:
        
        for i,v in enumerate(Integrated_power_list):
            if i < index_of_3_18_measurement:
                Integrated_power_list[i] /= Acc_Iso_power_ratio[0]
                
            if i >= index_of_3_18_measurement and i < index_of_ra_addition:
                Integrated_power_list[i] /= Acc_Iso_power_ratio[1]
                
            if i >= index_of_ra_addition:
                Integrated_power_list[i] /= Acc_Iso_power_ratio[2]
        
    else:
        Integrated_power_list = Integrated_power_list/Fudge_Factor

    DF["Integrated Power (kWhr from Acc)"] = Integrated_power_list

    latest_time = DF["Date and Time"].tail(1).item().to_pydatetime()

    # ------------------------ Calculation Algorithm          ---------------- #

    # initial_ra_225_N = 32.4 * 3.7e4 / ra_225_l # Measured activity prior to start
    # initial_ac_225_N = 10.0 * 3.7e4 / ac_225_l # Measured activity prior to start
    initial_ra_225_N = 0
    initial_ac_225_N = 0
    reaction_calculator(DF,
                        initial_ra_225_N,
                        initial_ac_225_N)

    latest_Ac225 = DF["Actinium-225 Activity (mCi)"].tail(1).item()

    print("Total integrated beam power: {:4.2f} kWhr".format(DF["Integrated Power (kWhr from Acc)"].sum()))
    print("Activity of Ac-225 at the last reported time: {:4.3f} mCi".format(latest_Ac225))

    # ------------------------ Projection Algorithm          ---------------- #
    #######################


    mask = (DF['Extraction'] == 'NO')
    masked_df = DF[mask]

    Projected_power = masked_df["Integrated Power (kWhr from Acc)"].tail(meta["Moving avg length"]).mean()
    Power_std = masked_df["Integrated Power (kWhr from Acc)"].tail(meta["Moving avg length"]).std()

    End = DF["Date and Time"].tail(1).item().to_pydatetime() # Get the last date
    # Create a series of datetime objects with parameters from meta data for projection
    dates = [End + DT.timedelta(seconds=x*meta["Project dt (s)"]) for x in range(int(86400*meta["Project length (days)"]/meta["Project dt (s)"]))]
    DF_proj = pd.DataFrame(columns=masked_df.columns)


    #######################
    DF_proj["Date and Time"] = dates
    DF_proj["Integrated Power (kWhr from Acc)"] = Projected_power
    DF_proj["Energy (MeV)"] = float(meta["Project energy"])
    DF_proj["Radium target mass (g)"] = float(meta["Radium target mass (g)"])
    DF_proj["Elapsed time (s)"] = (DF_proj["Date and Time"] - DF["Date and Time"][0]).dt.total_seconds()

    delta = []
    for i,t in enumerate(DF_proj["Elapsed time (s)"]):
        if i==0:
            delta.append(t-DF.tail(1)["Elapsed time (s)"].item())
        else:
            delta.append(t-DF_proj["Elapsed time (s)"][i-1])

    DF_proj["dt (s)"] = delta
    DF_custom = DF_proj.copy()
    DF_lower = DF_proj.copy()
    DF_upper = DF_proj.copy()

    Interval = meta["Standard deviations from average"]*Power_std
    DF_lower["Integrated Power (kWhr from Acc)"] = Projected_power - Interval
    DF_upper["Integrated Power (kWhr from Acc)"] = Projected_power + Interval

    DF_custom["Integrated Power (kWhr from Acc)"] = meta["Custom projection power"]

    reaction_calculator(DF_proj,
                        DF.tail(1)["Radium-225"].item(),
                        DF.tail(1)["Actinium-225"].item())

    reaction_calculator(DF_lower,
                        DF.tail(1)["Radium-225"].item(),
                        DF.tail(1)["Actinium-225"].item())

    reaction_calculator(DF_upper,
                        DF.tail(1)["Radium-225"].item(),
                        DF.tail(1)["Actinium-225"].item())

    reaction_calculator(DF_custom,
                        DF.tail(1)["Radium-225"].item(),
                        DF.tail(1)["Actinium-225"].item())

    DF.to_csv("output.csv")
    DF_proj.to_csv("projection.csv")

    # ------------------- B E G I N   P L O T T I N G ---------------------------- #

    fig, ax = plt.subplots(1,1,figsize=(11,8.5)) 

    ax.plot(DF["Date and Time"], DF["Radium-225 Activity (mCi)"],'r')
    ax.plot(DF["Date and Time"], DF["Actinium-225 Activity (mCi)"],'g')
        
    # Plot projections
    ax.plot(DF_proj["Date and Time"], DF_proj["Radium-225 Activity (mCi)"],'r--')
    ax.plot(DF_proj["Date and Time"], DF_proj["Actinium-225 Activity (mCi)"],'g--')
    ax.plot(DF_proj["Date and Time"], DF_custom["Radium-225 Activity (mCi)"],'r:')
    ax.plot(DF_proj["Date and Time"], DF_custom["Actinium-225 Activity (mCi)"],'g:')


    ax.fill_between(DF_upper["Date and Time"],
                    DF_upper["Radium-225 Activity (mCi)"], DF_lower["Radium-225 Activity (mCi)"],
                    color='red',alpha=0.2)


    # Plotting black dashed line at last reported data
    ylim    = (0,0.5)
    ax.plot([latest_time,latest_time],[ylim[0],ylim[1]],'k--')
    ax.set_ylim(0.0,ylim[1])

    # Plot target measurements
    try:
        for index,pt in DFmeas.iterrows():
            m,d,y = pt["Date"].split("/")
            h,M = pt["Time"].split(":")
            date = DT.datetime(int(y),int(m),int(d),int(h),int(M))
            data = pt["Ac-225"]
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
         title      = r'Niowave R&D milestones $^{225}$Ac Campaign',
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
                                                                                                                                      meta["Custom projection power"]*1000))
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
    main("irradiation log.csv")
##    main("Beam data.csv")
