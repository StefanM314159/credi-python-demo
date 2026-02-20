import streamlit as st
import pandas as pd
import io
from datetime import datetime
import plotly.express as px
import plotly.io as pio
import requests
import tempfile
import os

st.set_page_config(page_title= "Automation", page_icon="⚙️", layout="wide")

st.title("Automation")
st.markdown("""
Python is great at **automating repetitive tasks**.
            
Instead of running the same analysis manually for each country — you write the logic once and let Python 
loop over everything.
We'll demonstrate two things: **batch processing** multiple country datasets at once, 
then using those results to **generate a formatted PDF report** with a single click.
""")

st.divider()

st.header("Batch Processing")
st.markdown("""
As the logic for computing statistics is the same for every country we only need to write the logic once 
            and just collect the results into a single clean dataframe.
""")

st.code("""
# Define the analysis once as a function
def analyse_country(country_code, country_name, indicator, years):
    url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/{indicator}?format=json"
    data = requests.get(url).json()[1]
    df = pd.DataFrame([(r["date"], r["value"]) for r in data if r["value"]], 
                       columns=["Year", "Value"])
    return {
        "Country": country_name,
        "Mean":    df["Value"].mean(),
        "Min":     df["Value"].min(),
        "Max":     df["Value"].max(),
        "Latest":  df.sort_values("Year").iloc[-1]["Value"]
    }

# Then just loop over all countries 
results = [analyse_country(code, name, indicator) for name, code in countries.items()]
summary = pd.DataFrame(results)
""", language="python")

st.markdown("Select an indicator and click **Run Batch Analyis** to do the analysis for all 6 WB countries.")

wb_countries = {
    "Albania": ("AL", "ALB"),
    "Bosnia and Herzegovina": ("BA", "BIH"),
    "Kosovo": ("XK", "XKX"),
    "Montenegro": ("ME", "MNE"),
    "North Macedonia": ("MK", "MKD"),
    "Serbia": ("RS", "SRB"),
}

indicators = {
    "GDP per capita (current US$)": "NY.GDP.PCAP.CD",
    "Unemployment (% of labour force)": "SL.UEM.TOTL.ZS",
    "Inflation, consumer prices (%)": "FP.CPI.TOTL.ZG",
}

col1, col2 = st.columns([1,1])
with col1:
    selected_indicator = st.selectbox("Select indicator", list(indicators.keys()))
with col2:
    year_range = st.slider("Year range", 2010, 2023, (2016, 2023))

@st.cache_data(show_spinner=False)
def fetch_country_data(iso2, iso3, country_name, indicator_code, year_range):
    """Fetch and summarize for one country"""
    url = (
        f"https://api.worldbank.org/v2/country/{iso2}/indicator/{indicator_code}"
        f"?format=json&per_page=100"
    )
    response = requests.get(url, timeout = 30)
    raw = response.json()

    if len(raw) < 2 or not raw[1]:
        return None
    
    records = [
        {"Year" : int(r["date"]), "Value" : r['value']}
        for r in raw[1]
        if r['value'] is not None and year_range[0] <= int(r['date']) <= year_range[1]
    ]

    if not records:
        return None
    
    df = pd.DataFrame(records).sort_values("Year")

    return {
        "Country" : country_name,
        "Mean" : round(df['Value'].mean(), 2),
        "Min" : round(df['Value'].min(), 2),
        "Max" : round(df['Value'].max(), 2),
        "Latest value" : round(df.iloc[-1]['Value'], 2),
        "Latest year" : round(df.iloc[-1]["Year"], 2),
        "_data": df
    }

if st.button("Run Batch Analysis", type="primary"):
    results = []
    full_series = {}

    progress = st.progress(0, text="Starting batch process...")

    for i, (country_name, (iso2, iso3)) in enumerate(wb_countries.items()):
        progress.progress((i) / len(wb_countries), text=f"Processing {country_name}...")
        result = fetch_country_data(iso2, iso3, country_name, indicators[selected_indicator], year_range)
        if result:
            full_series[country_name] = result.pop("_data")
            results.append(result)

    progress.progress(1.0, text="Batch processing complete!")

    if results:
        summary_df = pd.DataFrame(results).set_index("Country")

        st.success(f"Processed {len(results)} countries in one pass")
        st.markdown("**Summary statistics across all countries:**")
        st.dataframe(summary_df, use_container_width=True)

        #Comparison chart
        combined = pd.concat(
            [df.assign(Country = name) for name, df in full_series.items()],
            ignore_index=True
        )

        fig = px.line(
            combined, x="Year", y="Value", color="Country",
            title=f"{selected_indicator} - All Western Balkans Countries",
            markers=True
        )
        fig.update_layout(plot_bgcolor = 'white', yaxis_title=selected_indicator)
        st.plotly_chart(fig, use_container_width=True)

        #Store results
        st.session_state['batch_results'] = summary_df
        st.session_state['batch_series'] = combined
        st.session_state['batch_indicator'] = selected_indicator
        st.session_state['batch_year_range'] = year_range

st.divider()

#Section 2: PDF Report Generation
st.header("PDF Report Generation")
st.markdown("""
Once you have your results, Python can package them into a **formatted PDF report** automatically. 
This uses the `fpdf2` library to build a structured document with a title page, summary table, 
and charts.
         
""")

st.code("""
from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
        
#Title
pdf.set_font("Helvetica", "B", size = 20)
pdf.cell(0,10, "Western Balkans Economic Report", ln = True)
    
#Table of results
pdf.set_font("Helvetica", size = 10)
for country, row in summary_df.iterrows():
        pdf.cell(0, 8, f"{country} : Mean = {row['Mean']:.2f}", ln=True)

#Save
pdf.output("report.pdf")
""", language="python")

if "batch_results" not in st.session_state:
    st.info("Run Batch Analysis to enable report generation")

else:
    st.success("Batch Results Ready - you can generate a report")

    report_title = st.text_input("Report title", value="Western Balkans Economic Report")
    report_author = st.text_input("Author / Organisation", value="CREDI")

    if st.button("Generate PDF Report", type='primary'):
        with st.spinner("Generating report"):
            try:
                from fpdf import FPDF

                summary_df = st.session_state['batch_results']
                combined = st.session_state['batch_series']
                indicator = st.session_state['batch_indicator']
                year_range = st.session_state['batch_year_range']
                
                #Generate chart as image - matplotlib
                import matplotlib
                matplotlib.use("Agg")
                import matplotlib.pyplot as plt
                import tempfile, os

                fig_mpl, ax = plt.subplots(figsize=(9,4))
                for country in combined['Country'].unique():
                    country_data = combined[combined['Country'] == country]
                    ax.plot(country_data['Year'], country_data['Value'], marker = 'o', label = country)
                ax.set_title(indicator)
                ax.set_xlabel("Year")
                ax.set_ylabel("Country")
                ax.legend(fontsize = 8)
                ax.grid(True, alpha = 0.3)
                plt.tight_layout()

                chart_path = os.path.join(tempfile.gettempdir(), "chart.png")
                fig_mpl.savefig(chart_path, dpi = 150, bbox_inches = "tight")
                plt.close(fig_mpl)

                # Build PDF
                pdf = FPDF()
                pdf.set_auto_page_break(auto=True, margin=15)

                #Title page
                pdf.add_page()
                pdf.set_fill_color(30,60,114)
                pdf.rect(0,0,210,60, 'F')

                pdf.set_text_color(255,255,255)
                pdf.set_font("Helvetica", "B", size = 22)
                pdf.set_y(18)
                pdf.cell(0,10,report_title, ln=True, align="C")

                pdf.set_font("Helvetica", size=12)
                pdf.cell(0,8, f"Prepared by: {report_author}", ln=True, align="C")
                pdf.cell(0,8, f"Generated: {datetime.now().strftime("%d %B %Y")}", ln=True, align="C")

                pdf.set_text_color(0,0,0)
                pdf.set_y(75)

                #Introduction
                pdf.set_font("Helvetica", "B",size = 14)
                pdf.cell(0, 10, "Overview", ln=True)
                pdf.set_font("Helvetica", size=11)
                pdf.multi_cell(0, 7, (
                    f"This report summarises {indicator} across the Western Balkans "
                    f"for the period {year_range[0]}-{year_range[1]}. "
                    f"Data sourced from the World Bank Open Data API."
                ))
                pdf.ln(5)

                # -- Summary table --
                pdf.set_font("Helvetica", "B", size=14)
                pdf.cell(0, 10, "Summary Statistics", ln=True)

                # Table header
                pdf.set_fill_color(30, 60, 114)
                pdf.set_text_color(255, 255, 255)
                pdf.set_font("Helvetica", "B", size=10)
                col_widths = [55, 30, 30, 30, 30, 15]
                headers = ["Country", "Mean", "Min", "Max", "Latest", "Year"]
                for w, h in zip(col_widths, headers):
                    pdf.cell(w, 8, h, border=1, fill=True)
                pdf.ln()

                # Table rows
                pdf.set_text_color(0, 0, 0)
                pdf.set_font("Helvetica", size=10)
                for i, (country, row) in enumerate(summary_df.iterrows()):
                    fill = i % 2 == 0
                    pdf.set_fill_color(240, 245, 255) if fill else pdf.set_fill_color(255, 255, 255)
                    pdf.cell(col_widths[1], 8, str(row["Mean"]), border=1, fill=fill, align="C")
                    pdf.cell(col_widths[0], 8, country, border=1, fill=fill)
                    pdf.cell(col_widths[3], 8, str(row["Max"]), border=1, fill=fill, align="C")
                    pdf.cell(col_widths[2], 8, str(row["Min"]), border=1, fill=fill, align="C")
                    pdf.cell(col_widths[4], 8, str(row["Latest value"]), border=1, fill=fill, align="C")
                    pdf.cell(col_widths[5], 8, str(row["Latest year"]), border=1, fill=fill, align="C")

                    pdf.ln()
                pdf.ln(8)

                # -- Chart --
                pdf.set_font("Helvetica", "B", size=14)
                pdf.cell(0, 10, "Trend Chart", ln=True)
                pdf.image(chart_path, x=10, w=185)

                # -- Footer on each page --
                pdf.set_font("Helvetica", "I", size=8)
                pdf.set_y(-15)
                pdf.set_text_color(150, 150, 150)
                pdf.cell(0, 10, f"{report_author} - {report_title} - {datetime.now().strftime('%Y')}", align="C")

                # ── Output to bytes ──────────────────────────────────────────
                # pdf_bytes = pdf.output()
                import io
                buffer = io.BytesIO()
                pdf.output(buffer)
                buffer.seek(0)
                pdf_bytes = buffer.read()
                
                st.success("✅ Report generated successfully!")
                st.download_button(
                    label="⬇️ Download PDF Report",
                    data=pdf_bytes,
                    mime="application/pdf",
                    file_name=f"western_balkans_report_{datetime.now().strftime('%Y%m%d')}.pdf",
                    type="primary"
                )
            except ImportError:
                st.error("fpdf not installed")
            except Exception as e:
                import traceback
                st.error(f"Report failed: {e}")
                st.code(traceback.format_exc())

st.divider()
st.markdown("""
**Where does this go next?**
                      
- **Scheduled reports** — run automatically every week using `schedule` or a cron job
- **Bulk data cleaning** — apply the same cleaning pipeline to 100 CSV files at once  
- **Email distribution** — send reports automatically using `smtplib`
- **Excel exports** — generate formatted multi-sheet Excel files using `openpyxl`
""")
                    