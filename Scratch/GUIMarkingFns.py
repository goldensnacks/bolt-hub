from Constants.Const import date_offsets, marks
import pandas as pd

def mark_vol_surface():
    pass

def mark_forward_curve():
    pass

def mark_decay_curve():
    return "result"

"""helpers"""
def extract_vol_surface(marks):
    """extract vol surface"""
    vols = marks.drop(index=range(33))
    vols = vols.iloc[0:, :18]
    # get the values of the top row as a series
    new_columns = [5,10,15,20,25,30,35,40,45,50,-40,-35,-30,-25,-20,-15,-10,-5]
    # assign the new column names to the dataframe
    vols.columns = new_columns
    # drop the first row since it's no longer needed as column names
    vols = vols.iloc[1:]
    # set the index to the values in the first column by position
    vols = vols.set_index(vols.columns[0])
    # drop the first column since it's now the index
    vols = vols.drop(columns=[vols.columns[0]])
    vols = vols.rename_axis(index=None).rename_axis(columns=None)
    new_index = [date_offsets[tenor] for tenor in vols.index]
    vols.set_index(pd.Index(new_index), inplace=True)
    return vols

if __name__=="__main__":
    extract_vol_surface(marks)