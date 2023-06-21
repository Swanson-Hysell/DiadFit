import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import patches
import lmfit
from lmfit.models import GaussianModel, VoigtModel, LinearModel, ConstantModel
from scipy.signal import find_peaks
import os
import re
from os import listdir
from os.path import isfile, join
import pickle
encode="ISO-8859-1"

## Cornell densimeters
def calculate_density_cornell(*, temp='SupCrit', Split, split_err=None):
    """ This function converts Diad Splitting into CO$_2$ density using the densimeters of DeVitre et al. (2021)
    This should only be used for the Cornell Raman, not other Ramans at present

    Parameters
    -------------
    temp: str
        'SupCrit' if measurements done at 37C
        'RoomT' if measurements done at 24C

    Split: int, float, pd.Series, np.array

    Returns
    --------------
    pd.DataFrame
        Prefered Density (based on different equatoins being merged), and intermediate calculations




    """

    #if temp is "RoomT":
    LowD_RT=-38.34631 + 0.3732578*Split
    HighD_RT=-41.64784 + 0.4058777*Split- 0.1460339*(Split-104.653)**2

    # IF temp is 37
    LowD_SC=-38.62718 + 0.3760427*Split
    MedD_SC=-47.2609 + 0.4596005*Split+ 0.0374189*(Split-103.733)**2-0.0187173*(Split-103.733)**3
    HighD_SC=-42.52782 + 0.4144277*Split- 0.1514429*(Split-104.566)**2

    if isinstance(Split, pd.Series) or isinstance(Split, np.ndarray):

        df=pd.DataFrame(data={'Preferred D': 0,
        'in range': 'Y',
                                'Notes': 'not in range',
                                'LowD_RT': LowD_RT,
                                'HighD_RT': HighD_RT,
                                'LowD_SC': LowD_SC,
                                'MedD_SC': MedD_SC,
                                'HighD_SC': HighD_SC,
                                'Temperature': temp,
                                'Splitting': Split,

                                })

    else:
        df=pd.DataFrame(data={'Preferred D': 0,
        'in range': 'Y',
                                'Notes': 'not in range',
                                'LowD_RT': LowD_RT,
                                'HighD_RT': HighD_RT,
                                'LowD_SC': LowD_SC,
                                'MedD_SC': MedD_SC,
                                'HighD_SC': HighD_SC,
                                'Temperature': temp,
                                'Splitting': Split,

                                }, index=[0])


    roomT=df['Temperature']=="RoomT"
    SupCrit=df['Temperature']=="SupCrit"
    # If splitting is 0
    zero=df['Splitting']==0

    # Range for SC low density
    min_lowD_SC_Split=df['Splitting']>=102.72
    max_lowD_SC_Split=df['Splitting']<=103.16
    # Range for SC med density
    min_MD_SC_Split=df['Splitting']>103.16
    max_MD_SC_Split=df['Splitting']<=104.28
    # Range for SC high density
    min_HD_SC_Split=df['Splitting']>=104.28
    max_HD_SC_Split=df['Splitting']<=104.95
    # Range for Room T low density
    min_lowD_RoomT_Split=df['Splitting']>=102.734115670188
    max_lowD_RoomT_Split=df['Splitting']<=103.350311768435
    # Range for Room T high density
    min_HD_RoomT_Split=df['Splitting']>=104.407308904012
    max_HD_RoomT_Split=df['Splitting']<=105.1
    # Impossible densities, room T
    Imposs_lower_end=(df['Splitting']>103.350311768435) & (df['Splitting']<103.88)
    # Impossible densities, room T
    Imposs_upper_end=(df['Splitting']<104.407308904012) & (df['Splitting']>103.88)
    # Too low density
    Too_Low_SC=df['Splitting']<102.72
    Too_Low_RT=df['Splitting']<102.734115670188

    df.loc[zero, 'Preferred D']=0
    df.loc[zero, 'Notes']=0


    # If room T, low density, set as low density
    df.loc[roomT&(min_lowD_RoomT_Split&max_lowD_RoomT_Split), 'Preferred D'] = LowD_RT
    df.loc[roomT&(min_lowD_RoomT_Split&max_lowD_RoomT_Split), 'Notes']='Room T, low density'
    # If room T, high density
    df.loc[roomT&(min_HD_RoomT_Split&max_HD_RoomT_Split), 'Preferred D'] = HighD_RT
    df.loc[roomT&(min_HD_RoomT_Split&max_HD_RoomT_Split), 'Notes']='Room T, high density'

    # If SupCrit, high density
    df.loc[ SupCrit&(min_HD_SC_Split&max_HD_SC_Split), 'Preferred D'] = HighD_SC
    df.loc[ SupCrit&(min_HD_SC_Split&max_HD_SC_Split), 'Notes']='SupCrit, high density'
    # If SupCrit, Med density
    df.loc[SupCrit&(min_MD_SC_Split&max_MD_SC_Split), 'Preferred D'] = MedD_SC
    df.loc[SupCrit&(min_MD_SC_Split&max_MD_SC_Split), 'Notes']='SupCrit, Med density'

    # If SupCrit, low density
    df.loc[ SupCrit&(min_lowD_SC_Split&max_lowD_SC_Split), 'Preferred D'] = LowD_SC
    df.loc[SupCrit&(min_lowD_SC_Split&max_lowD_SC_Split), 'Notes']='SupCrit, low density'

    # If Supcritical, and too low
    df.loc[SupCrit&(Too_Low_SC), 'Preferred D']=LowD_SC
    df.loc[SupCrit&(Too_Low_SC), 'Notes']='Below lower calibration limit'
    df.loc[SupCrit&(Too_Low_SC), 'in range']='N'


    # If RoomT, and too low
    df.loc[roomT&(Too_Low_RT), 'Preferred D']=LowD_RT
    df.loc[roomT&(Too_Low_RT), 'Notes']='Below lower calibration limit'
    df.loc[roomT&(Too_Low_RT), 'in range']='N'

    #if splitting is zero
    SplitZero=df['Splitting']==0
    df.loc[SupCrit&(SplitZero), 'Preferred D']=np.nan
    df.loc[SupCrit&(SplitZero), 'Notes']='Splitting=0'
    df.loc[SupCrit&(SplitZero), 'in range']='N'

    df.loc[roomT&(SplitZero), 'Preferred D']=np.nan
    df.loc[roomT&(SplitZero), 'Notes']='Splitting=0'
    df.loc[roomT&(SplitZero), 'in range']='N'


    # If impossible density, lower end
    df.loc[roomT&Imposs_lower_end, 'Preferred D'] = LowD_RT
    df.loc[roomT&Imposs_lower_end, 'Notes']='Impossible Density, low density'
    df.loc[roomT&Imposs_lower_end, 'in range']='N'

    # If impossible density, lower end
    df.loc[roomT&Imposs_upper_end, 'Preferred D'] = HighD_RT
    df.loc[roomT&Imposs_upper_end, 'Notes']='Impossible Density, high density'
    df.loc[roomT&Imposs_upper_end, 'in range']='N'


    #df.loc[zero, 'in range']='Y'
    # If high densiy, and beyond the upper calibration limit
    Upper_Cal_RT=df['Splitting']>105.1
    Upper_Cal_SC=df['Splitting']>104.95

    df.loc[roomT&Upper_Cal_RT, 'Preferred D'] = HighD_RT
    df.loc[roomT&Upper_Cal_RT, 'Notes']='Above upper Cali Limit'
    df.loc[roomT&Upper_Cal_RT, 'in range']='N'

    df.loc[SupCrit&Upper_Cal_SC, 'Preferred D'] = HighD_SC
    df.loc[SupCrit&Upper_Cal_SC, 'Notes']='Above upper Cali Limit'
    df.loc[SupCrit&Upper_Cal_SC, 'in range']='N'

    if split_err is not None:
        df2=calculate_dens_error(temp, Split, split_err)

        df.insert(1, 'dens+1σ', df2['max_dens'])
        df.insert(1, 'dens-1σ', df2['min_dens'])
        df.insert(3, '1σ', (df2['max_dens']-df2['min_dens'])/2 )

    return df

def calculate_dens_error(temp, Split, split_err):

    max_dens=calculate_density_cornell(temp=temp, Split=Split+split_err)
    min_dens=calculate_density_cornell(temp=temp, Split=Split-split_err)
    df=pd.DataFrame(data={
                        'max_dens': max_dens['Preferred D'],
                        'min_dens': min_dens['Preferred D']})

    return df


def propagate_errors_for_splitting(Ne_corr, df_sorted):
    """ This function propagates errors in your Ne correection model and peak fits by quadrature

    """
    Ne_err=(Ne_corr['upper_values']-Ne_corr['lower_values'])/2
    Diad1_err=df_sorted['Diad1_cent_err'].fillna(0)
    Diad2_err=df_sorted['Diad2_cent_err'].fillna(0)
    split_err=(Diad1_err**2 + Diad2_err**2)**0.5
    Combo_err= (((df_sorted['Splitting']* (Ne_err))**2) +  (Ne_corr['preferred_values'] *split_err  )**2 )**0.5

    return Combo_err

## UCBerkeley densimeters
def calculate_density_ucb(*, temp='SupCrit', Split, split_err=None):
    """ This function converts Diad Splitting into CO$_2$ density using densimeters of UCB

    Parameters
    -------------
    temp: str
        'SupCrit' if measurements done at 37C
        'RoomT' if measurements done at 24C

    Split: int, float, pd.Series, np.array

    Returns
    --------------
    pd.DataFrame
        Prefered Density (based on different equatoins being merged), and intermediate calculations




    """

    # #if temp is "RoomT":
    LowD_RT=-38.34631 + 0.3732578*Split
    HighD_RT=-41.64784 + 0.4058777*Split- 0.1460339*(Split-104.653)**2

    # IF temp is 37
    pickle_str='Lowrho_polyfit_data.pkl'
    with open(pickle_str, 'rb') as f:
        lowrho_pickle_data = pickle.load(f)
    pickle_str='Mediumrho_polyfit_data.pkl'
    with open(pickle_str, 'rb') as f:
        medrho_pickle_data = pickle.load(f)
    pickle_str='Highrho_polyfit_data.pkl'
    with open(pickle_str, 'rb') as f:
        highrho_pickle_data = pickle.load(f)

    lowrho_model = lowrho_pickle_data['model']
    medrho_model = medrho_pickle_data['model']
    highrho_model = highrho_pickle_data['model']

    LowD_SC = pd.Series(lowrho_model(Split), index=Split.index)
    MedD_SC = pd.Series(medrho_model(Split), index=Split.index)
    HighD_SC = pd.Series(highrho_model(Split), index=Split.index)
    if isinstance(Split, pd.Series) or isinstance(Split, np.ndarray):

        df=pd.DataFrame(data={'Preferred D': 0,
        'in range': 'Y',
                                'Notes': 'not in range',
                                'LowD_RT': LowD_RT,
                                'HighD_RT': HighD_RT,
                                'LowD_SC': LowD_SC,
                                'MedD_SC': MedD_SC,
                                'HighD_SC': HighD_SC,
                                'Temperature': temp,
                                'Splitting': Split,

                                })

    else:
        df=pd.DataFrame(data={'Preferred D': 0,
        'in range': 'Y',
                                'Notes': 'not in range',
                                'LowD_RT': LowD_RT,
                                'HighD_RT': HighD_RT,
                                'LowD_SC': LowD_SC,
                                'MedD_SC': MedD_SC,
                                'HighD_SC': HighD_SC,
                                'Temperature': temp,
                                'Splitting': Split,

                                }, index=[0])


    roomT=df['Temperature']=="RoomT"
    SupCrit=df['Temperature']=="SupCrit"
    # If splitting is 0
    zero=df['Splitting']==0

    # Range for SC low density
    min_lowD_SC_Split=df['Splitting']>=102.7623598753032
    max_lowD_SC_Split=df['Splitting']<=103.1741034592534
    # Range for SC med density
    min_MD_SC_Split=df['Splitting']>103.0608505403591
    max_MD_SC_Split=df['Splitting']<=104.3836704771313
    # Range for SC high density
    min_HD_SC_Split=df['Splitting']>=104.2538992302499
    max_HD_SC_Split=df['Splitting']<=105.3438707618937
    # Range for Room T low density
    min_lowD_RoomT_Split=df['Splitting']>=102.734115670188
    max_lowD_RoomT_Split=df['Splitting']<=103.350311768435
    # Range for Room T high density
    min_HD_RoomT_Split=df['Splitting']>=104.407308904012
    max_HD_RoomT_Split=df['Splitting']<=105.1
    # Impossible densities, room T
    Imposs_lower_end=(df['Splitting']>103.350311768435) & (df['Splitting']<103.88)
    # Impossible densities, room T
    Imposs_upper_end=(df['Splitting']<104.407308904012) & (df['Splitting']>103.88)
    # Too low density
    Too_Low_SC=df['Splitting']<102.7623598753032
    Too_Low_RT=df['Splitting']<102.734115670188

    df.loc[zero, 'Preferred D']=0
    df.loc[zero, 'Notes']=0


    # If room T, low density, set as low density
    df.loc[roomT&(min_lowD_RoomT_Split&max_lowD_RoomT_Split), 'Preferred D'] = LowD_RT
    df.loc[roomT&(min_lowD_RoomT_Split&max_lowD_RoomT_Split), 'Notes']='Room T, low density'
    # If room T, high density
    df.loc[roomT&(min_HD_RoomT_Split&max_HD_RoomT_Split), 'Preferred D'] = HighD_RT
    df.loc[roomT&(min_HD_RoomT_Split&max_HD_RoomT_Split), 'Notes']='Room T, high density'

    # If SupCrit, high density
    df.loc[ SupCrit&(min_HD_SC_Split&max_HD_SC_Split), 'Preferred D'] = HighD_SC
    df.loc[ SupCrit&(min_HD_SC_Split&max_HD_SC_Split), 'Notes']='SupCrit, high density'
    # If SupCrit, Med density
    df.loc[SupCrit&(min_MD_SC_Split&max_MD_SC_Split), 'Preferred D'] = MedD_SC
    df.loc[SupCrit&(min_MD_SC_Split&max_MD_SC_Split), 'Notes']='SupCrit, Med density'

    # If SupCrit, low density
    df.loc[ SupCrit&(min_lowD_SC_Split&max_lowD_SC_Split), 'Preferred D'] = LowD_SC
    df.loc[SupCrit&(min_lowD_SC_Split&max_lowD_SC_Split), 'Notes']='SupCrit, low density'

    # If Supcritical, and too low
    df.loc[SupCrit&(Too_Low_SC), 'Preferred D']=LowD_SC
    df.loc[SupCrit&(Too_Low_SC), 'Notes']='Below lower calibration limit'
    df.loc[SupCrit&(Too_Low_SC), 'in range']='N'


    # If RoomT, and too low
    df.loc[roomT&(Too_Low_RT), 'Preferred D']=LowD_RT
    df.loc[roomT&(Too_Low_RT), 'Notes']='Below lower calibration limit'
    df.loc[roomT&(Too_Low_RT), 'in range']='N'

    #if splitting is zero
    SplitZero=df['Splitting']==0
    df.loc[SupCrit&(SplitZero), 'Preferred D']=np.nan
    df.loc[SupCrit&(SplitZero), 'Notes']='Splitting=0'
    df.loc[SupCrit&(SplitZero), 'in range']='N'

    df.loc[roomT&(SplitZero), 'Preferred D']=np.nan
    df.loc[roomT&(SplitZero), 'Notes']='Splitting=0'
    df.loc[roomT&(SplitZero), 'in range']='N'


    # If impossible density, lower end
    df.loc[roomT&Imposs_lower_end, 'Preferred D'] = LowD_RT
    df.loc[roomT&Imposs_lower_end, 'Notes']='Impossible Density, low density'
    df.loc[roomT&Imposs_lower_end, 'in range']='N'

    # If impossible density, lower end
    df.loc[roomT&Imposs_upper_end, 'Preferred D'] = HighD_RT
    df.loc[roomT&Imposs_upper_end, 'Notes']='Impossible Density, high density'
    df.loc[roomT&Imposs_upper_end, 'in range']='N'


    #df.loc[zero, 'in range']='Y'
    # If high densiy, and beyond the upper calibration limit
    Upper_Cal_RT=df['Splitting']>105.1
    Upper_Cal_SC=df['Splitting']>105.3438707618937

    df.loc[roomT&Upper_Cal_RT, 'Preferred D'] = HighD_RT
    df.loc[roomT&Upper_Cal_RT, 'Notes']='Above upper Cali Limit'
    df.loc[roomT&Upper_Cal_RT, 'in range']='N'

    df.loc[SupCrit&Upper_Cal_SC, 'Preferred D'] = HighD_SC
    df.loc[SupCrit&Upper_Cal_SC, 'Notes']='Above upper Cali Limit'
    df.loc[SupCrit&Upper_Cal_SC, 'in range']='N'

    if split_err is not None:
        df2=calculate_dens_error_ucb(temp, Split, split_err)

        df.insert(1, 'dens+1σ', df2['max_dens'])
        df.insert(1, 'dens-1σ', df2['min_dens'])
        df.insert(3, '1σ', (df2['max_dens']-df2['min_dens'])/2 )

    return df

def calculate_dens_error_ucb(temp, Split, split_err):

    max_dens=calculate_density_ucb(temp=temp, Split=Split+split_err)
    min_dens=calculate_density_ucb(temp=temp, Split=Split-split_err)
    df=pd.DataFrame(data={
                        'max_dens': max_dens['Preferred D'],
                        'min_dens': min_dens['Preferred D']})

    return df


