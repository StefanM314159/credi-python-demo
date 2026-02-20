import streamlit as st

st.set_page_config(
    page_title="Python for Economists",
    page_icon = "📊",
    layout = "wide"
)

st.title("Pyhton Showcase")
st.subheader("Practical demo for Stata users")

st.markdown("""
Welcome! This dashboard demonstrates three areas where Python goes beyond what's easily possible in Stata.

Use the **sidebar** to navigate between modules:

| Module | What it shows |
|---|---|
| **Data and Text Analysis** | APIs, web scraping, and text analysis |
| **Geospatial Analysis** | Interactive maps and spatial data |
| **Automation** | Batch processing and report generation |
| **Interactive Dashboards** | Conclusions and some honourable mentions |
---
*Data sources: World Bank API, Wikipedia, Frankfurter*
""")