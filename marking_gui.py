import pandas as pd
import streamlit as st
from securities.graph import get_security

def fx_surface_table():
    """vol surface input"""
    products = ["RR10", "RR25", "ATM", "BF10", "BF25"]
    tenors = ['1D', '1W', '1M', '2M', '3M', '6M', '9M', '1Y']

    columns = products
    data = pd.DataFrame(columns=columns, index=tenors)
    data = data.fillna(0.0)
    return data

def submit_vols(security):
    st.write("Vol Surface")
    sec =get_security(security)
    if hasattr(sec.obj,'vol_surface_by_strike'):
        vs = sec.obj.vol_surface_by_strike
    else:
        vs = fx_surface_table()
    vs.index = ['1D', '1W', '1M', '2M', '3M', '6M', '9M', '1Y']
    vol_surface = st.data_editor(vs).to_dict()

    if st.button("Submit Vols"):
        sec.obj.load_vol_surface(vol_surface, by_strike=True)
        sec.obj.vol_surface = pd.DataFrame()
        sec.obj.complete_surface_from_marks()
        sec.save()
        st.success('Submitted vols!')

def forward_curve_table():
    """forward curve input"""
    tenors  = ['1D', '1W', '1M', '2M', '3M', '6M', '9M', '1Y']
    columns = ["% Spot", "Value"]
    data = pd.DataFrame(columns=columns, index=tenors)
    data = data.fillna(0.0)
    return data

def submit_forwards(security):
    st.write("Forward Curve")
    sec = get_security(security)
    if hasattr(sec.obj,'forward_curve'):
        forward_curve = sec.obj.forward_curve
    else:
        forward_curve = forward_curve_table()
    forward_curve = pd.DataFrame(forward_curve)
    forward_curve.index = ['1D', '1W', '1M', '2M', '3M', '6M', '9M', '1Y']
    forward_curve = st.data_editor(forward_curve).to_dict()

    if st.button("Submit fwd") :
        sec.obj.load_forward_curve(forward_curve)
        sec.save()
        st.success('Submitted fwd!')

def daily_decay_curve():
    """decay curve input"""
    tenors  = range(1, 25)
    columns = ["Weight", "Cumulative"]
    data = pd.DataFrame(columns=columns, index=tenors)
    data["Weight"] = 1/24
    data["Cumulative"] = data["Weight"].cumsum()
    return data.transpose()

def submit_decay(security):
    st.write("Decay curve")
    sec = get_security(security)
    if hasattr(sec.obj,'intraday_weights'):
        weights = sec.obj.intraday_weights
        weights = pd.DataFrame(weights).transpose()
        weights = st.data_editor(weights).to_dict()
    else:
        weights = daily_decay_curve()
        weights = pd.DataFrame(weights).transpose()
        weights = st.data_editor(weights).to_dict()

    if st.button("Submit Decay"):
        sec.obj.load_intraday_weights(weights)
        sec.save()
        st.success('Submitted weights!')

def main(security):
    st.markdown(
        """
        <style>
        .st-ct {
            width: 150%;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.title("Bolthub")
    st.write(security)

    submit_vols(security)
    submit_forwards(security)
    submit_decay(security)

if __name__ == "__main__":
    import sys
    security = sys.argv[1]
    main(security)
