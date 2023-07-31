# StreamlitGui.py

import streamlit as st

def main():
    # Set a title for your web app
    st.title("My Streamlit Web App")

    # Add some text to the app
    st.header("Welcome to my first Streamlit app!")
    st.write("This is a basic template for a Streamlit web application.")

    # Add some interactive widgets
    name = st.text_input("Enter your name:", "John Doe")
    age = st.slider("Select your age:", 0, 100, 25)

    # Show the user's input
    st.write(f"Hello, {name}! You are {age} years old.")

    # Add a plot or visualization
    st.subheader("Sample Chart")
    chart_data = {"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]}
    st.line_chart(chart_data)

    # Add some explanations or additional information
    st.info("This is just a simple example to get you started.")

if __name__ == "__main__":
    main()