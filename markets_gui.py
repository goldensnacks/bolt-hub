import streamlit as st
from securities.graph import get_security
from tradables import Underlier, MarketTable
def display_markets():
    #get tradable
    tradables = get_security("tradables")
    df = tradables.obj.get_table()
    df['hours_to_expiry'] = df['hours_to_expiry'].astype(int)
    expires = df['hours_to_expiry'].unique()
    underliers = df['underlier'].unique()
    # Create an empty list to store the dataframes
    dataframes_list = []
    for expire in expires:
        # Create a dataframe for the current 'hours_to_expiry' value
        for underlier in underliers:
            df_for_expire = df[(df['hours_to_expiry'] == expire) & (df['underlier'] == underlier)].copy()
            df_for_expire = df_for_expire.set_index('delta')
            df_for_expire = df_for_expire.drop('title', axis=1)
            st.write('expires')
            st.dataframe(df_for_expire)


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
