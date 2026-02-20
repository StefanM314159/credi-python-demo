import streamlit as st
import pandas as pd

st.set_page_config(page_title="Interactive Dashboard", page_icon="X", layout='wide')

st.title("Interactive Dashboard")
st.subheader("How was this dashboard made?")

st.markdown("""
The most powerful feature of Python isn't any specific command; rather that it's a **General Purpose Language**.
This means that everything you have interacted on this dashboard was built entirely in Python with the **Streamlit** library.
""")

st.divider()

col1, col2 = st.columns([1,1])

with col1: 
    st.header("The Tech Used")
    st.markdown("""
    * **Streamlit**: The framework that turns simple files into dashboards
    * **Pandas & Requests**: DB managament and Handling API calls
    * **Plotly**: Creates the interactive visuals
    * **FPDF**: Turns the data into PDFs
    * **NLTK**: Library used to implement the VADER sentiment analysis
    """)

with col2:
    st.header("Why this is better than STATA for reports?")
    st.markdown("""
    **Interactive vs Static**: Instead of generating PDF repors, you can host a dashboard similar to this one.
    """)

st.divider()
st.header("Honorable Mentions")

tab1, tab2, tab3 = st.tabs(["Machine Learning", "High-Performance Data", "Advanced Econometrics"])
with tab1:
    st.markdown("### Machine Learning & Predictions")
    st.markdown("""
    Python has access to machine learning tools that offer much more predicitve value than causal models.
    
    * **Scikit-Learn**: The industry standard for predictive modeling.
    * **XGBoost / Random Forests**: Advanced models that handle non-linear relationships.
    * **Time-Series Forecasting**: Libraries like `Prophet` (by Meta) or `sktime` for complex forecasting.
    """)
with tab2:
    st.markdown("### Handling Big Data")
    st.markdown("""
    Python has access to tools that allow for easy handling of large datasets.  
            
    * **Dask**: Allows you to run analysis on datasets that are larger than your computer's memory.
    * **Database Integration**: Direct connection to various database types.
    """)
with tab3:
    st.markdown("### Modern Econometrics")
    st.markdown("""
    In addition to the advanced predictive models, Python also has access to advanced causal inference techniques.

    * **PyFixest**: High-performance fixed effects.
    * **DoubleML**: Double Machine Learning for causal inference.
    * **CausalPy**: Bayesian causal inference for "Difference-in-Differences" and "Synthetic Control" methods.   
""")