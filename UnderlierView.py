import streamlit as st
import Securities as Sc


if __name__ == "__main__":
    st.title("Underlier viewer")
    #select box between EURUSD and USDJPY
    security = st.selectbox("Underlier", ["EURUSD", "USDJPY"])

    sec = Sc.get_security(security)
    #display vol surface
    st.write("Vol surface")
    vs = sec.obj.vol_surface_by_strike
    vs.index = ['1D', '1W', '1M', '2M', '3M', '6M', '9M', '1Y']
    st.dataframe(vs)

    #display forward curve
    st.write("Forward curve")
    fc = sec.obj.forward_curve
    st.dataframe(fc)

    #display decay curve
    st.write("Decay curve")
    dc = sec.obj.intraday_weights
    st.dataframe(dc)
