import streamlit as st
import securities as Sc
from tradables import Underlier, MarketTable
def display_markets():
    underlier = Sc.get_security("EURUSD")
    st.write(underlier.obj.get_spot())
    #get tradable
    tradables = Sc.get_security("tradables")
    if isinstance(tradables.obj, str):
        tradables.obj = eval(tradables.obj)
        tradables.save()
    df = tradables.obj.get_table()
    expires = set(df['hours_to_expiry'])
    next_exp = min(expires)

    st.write("next expiry")
    df.set_index('delta', inplace=True)
    # df = df[df['hours_to_expiry'] == next_exp]
    df = df.drop(['title'], axis=1)
    st.dataframe(df)


def main():
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

    st.title("Bolthub Markets")
    display_markets()


if __name__ == "__main__":
    main()
