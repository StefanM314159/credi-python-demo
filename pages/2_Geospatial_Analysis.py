import streamlit as st
import pandas as pd
import plotly.express as px
import requests

st.set_page_config(page_title="Geospatial Analysis", page_icon="🗺️", layout="wide")

st.title("Geospatial Analysis")
st.markdown("""
Spatial data is everywhere in economics; regional inequality, trade flows, unemployment by area. 
In Stata, mapping requires external tools, shapefiles, and significant setup. 
In Python, interactive maps are a few lines of code.
""")

st.divider()

#Section 1: Choropleth maph
st.header("Chloropleth Map - Country-level indicators over time")
st.markdown("""
A choropleth shades each region by a data value. Combined with a **time slider**, 
it lets you animate how an indicator evolves year by year.
            
We pull data from the **World Bank API** for all Western Balkans countries across a range of years, 
then pass it directly to `px.choropleth()` with the year as an animation frame
""")

st.code("""
#All we need is a dataframe with:
# - ISO country code column
# - a value column (e.g unemployment rate)
# - a year column


fig = px.choropleth(
    df,
    locations="iso_code",          # column with ISO-3 country codes
    color="value",                 # column to colour by
    animation_frame="year",        # creates the time slider
    scope="europe",                # zoom to Europe
    color_continuous_scale="Reds",
    title="Unemployment Rate — Western Balkans"
)
fig.show()       
""", language="python")

indicator_options = {
    "GDP per capita (US$)" : ("NY.GDP.PCAP.CD" , "Blues"),
    "Unemployement rate" : ("SL.UEM.TOTL.ZS", "Reds"),
    "Inflation, consumer prices (%)" : ("FP.CPI.TOTL.ZG", "Oranges"),
}

wb_countries = {
    "Albania": ("AL", "ALB"),
    "Bosnia and Herzegovina": ("BA", "BIH"),
    "Kosovo": ("XK", "XKX"),
    "Montenegro": ("ME", "MNE"),
    "North Macedonia": ("MK", "MKD"),
    "Serbia": ("RS", "SRB"),
}

col1, col2 = st.columns([1,1])
with col1:
    indicator_name = st.selectbox("Select an indicator", list(indicator_options.keys()))
    indicator_code, color_scale = indicator_options[indicator_name]
with col2:
    year_range = st.slider("Year range", 2010, 2023, (2016, 2023))

@st.cache_data(show_spinner=False)
def fetch_choropleth_data(indicator_code, indicator_name, year_range):
    all_data = []

    for country_name, (iso2, iso3) in wb_countries.items():
        url = (
            f"https://api.worldbank.org/v2/country/{iso2}/indicator/{indicator_code}"
            f"?format=json&per_page=100"
        )
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        records = response.json()[1]

        if records:
            for r in records:
                if r['value'] is not None:
                    year = int(r['date'])
                    if year_range[0] <= year <= year_range[1]:
                        all_data.append({
                            "Country" : country_name,
                            "iso_code" : iso3,
                            "Year" : str(year),
                            indicator_name: round(r['value'], 3)
                        })
    return pd.DataFrame(all_data).sort_values("Year")

if st.button("Generate Choropleth map", type="primary"):
    with st.spinner("Accessing World Bank API"):
        try:
            df = fetch_choropleth_data(indicator_code, indicator_name, year_range)

            if df.empty:
                st.error("No data returned")
            else:
                st.success(f"Fetched {len(df)} data points across {df['Country'].nunique()} countries")

                fig = px.choropleth(
                    df,
                    locations="iso_code",
                    color=indicator_name,
                    animation_frame="Year",
                    hover_data={indicator_name: True, "iso_code" : False},
                    hover_name="Country",
                    scope='europe',
                    color_continuous_scale=color_scale,
                    title=f"{indicator_name} - Western Balkans ({year_range[0]}-{year_range[1]})",
                    labels={indicator_name : indicator_name},
                )
                fig.update_geos(
                    fitbounds = 'locations',
                    showcoastlines = True,
                    coastlinecolor = 'white',
                    showland = True,
                    landcolor = "lightgray",
                    showocean = True,
                    oceancolor = 'lightblue',
                    showframe = True,
                    showcountries = True,
                    countrycolor = 'white'
                )
                fig.update_layout(
                    height=550,
                    margin= {"r" : 0, 't' : 50, "l" : 0, "b" : 0},
                    coloraxis_colorbar = {"title" : indicator_name[:20]}
                )

                st.plotly_chart(fig, use_container_width=True)
                st.caption("Drag the slider to animate through years. Hover over country to see exact value")

                with st.expander("View underlying data"):
                    pivot_df = df.groupby(["Country", "Year"])[indicator_name].mean().reset_index()
                    st.dataframe(
                        pivot_df.pivot(index="Country", columns="Year", values=indicator_name),
                        use_container_width=True
                    )

        except Exception as e:
            import traceback
            st.error("Failed to fetch: {e}")
            st.code(traceback.format_exc())

st.divider()

#Section 2: Bubble map
st.header("Bubble map - City-level point data")
st.markdown("""
While the choropleth shows country-level aggregates, a **bubble map** lets us zoom into 
167specific locations. Each point is a latitude/longitude coordinate — Python treats these 
as just another two columns in a dataframe. No GIS software, no shapefiles required.

Here we plot the **capital cities** of the Western Balkans with bubbles sized by population 
and coloured by a selected economic indicator. This technique scales to any point data - as long as it has the latitude and longitude.
""")

st.code("""
import plotly.express as px
        
# City data is just a dataframe with lat, lon, and a chosen value
df_cities = pd.DataFrame([
    {"city": "Tirana",   "lat": 41.33, "lon": 19.82, "population": 800_000},
    {"city": "Belgrade", "lat": 44.80, "lon": 20.46, "population": 1_700_000},
    ...
])

fig = px.scatter_mapbox(
    df_cities,
    lat="lat", lon="lon",          # coordinate columns
    size="population",             # bubble size
    color="gdp_per_capita",        # bubble colour
    hover_name="city",
    zoom=5
)
""", language="python")

cities = pd.DataFrame([
    {
        "City": "Tirana", "Country": "Albania",
        "lat": 41.33, "lon": 19.82,
        "Population": 800_000,
        "GDP per capita (US$)": 6_800,
        "Unemployment (%)": 11.2,
        "FDI Inflows (USD million)": 1_104,
    },
    {
        "City": "Sarajevo", "Country": "Bosnia & Herzegovina",
        "lat": 43.85, "lon": 18.39,
        "Population": 420_000,
        "GDP per capita (US$)": 7_100,
        "Unemployment (%)": 15.8,
        "FDI Inflows (USD million)": 412,
    },
    {
        "City": "Pristina", "Country": "Kosovo",
        "lat": 42.67, "lon": 21.17,
        "Population": 210_000,
        "GDP per capita (US$)": 5_300,
        "Unemployment (%)": 12.4,
        "FDI Inflows (USD million)": 635,
    },
    {
        "City": "Podgorica", "Country": "Montenegro",
        "lat": 42.44, "lon": 19.26,
        "Population": 180_000,
        "GDP per capita (US$)": 9_800,
        "Unemployment (%)": 15.3,
        "FDI Inflows (USD million)": 738,
    },
    {
        "City": "Skopje", "Country": "North Macedonia",
        "lat": 41.99, "lon": 21.43,
        "Population": 590_000,
        "GDP per capita (US$)": 6_600,
        "Unemployment (%)": 14.5,
        "FDI Inflows (USD million)": 320,
    },
    {
        "City": "Belgrade", "Country": "Serbia",
        "lat": 44.80, "lon": 20.46,
        "Population": 1_700_000,
        "GDP per capita (US$)": 10_400,
        "Unemployment (%)": 9.4,
        "FDI Inflows (USD million)": 4_110,
    },
])

city_indicators = ["GDP per capita (US$)" , "Unemployment (%)", "FDI Inflows (USD million)"]
city_colors = {
    "GDP per capita (US$)" : "Blues",
    "Unemployment (%)" : "Reds",
    "FDI Inflows (USD million)" : "Greens",
}

col1, col2 = st.columns([1,1])
with col1:
    bubble_size = st.selectbox("Bubble size represents", ["Population"] + city_indicators)
with col2:
    bubble_color = st.selectbox("Bubble color represents", city_indicators)

fig_bubble = px.scatter_mapbox(
    cities,
    lat ="lat",
    lon = 'lon',
    size=bubble_size,
    color=bubble_color,
    hover_name="City",
    hover_data={
        "Country" : True,
        "Population" : True,
        "GDP per capita (US$)" : True,
        "Unemployment (%)" : True,
        "FDI Inflows (USD million)" : True,
        "lat" : False,
        "lon" : False,
    },
    color_continuous_scale=city_colors.get(bubble_color, "Blues"),
    mapbox_style="carto-positron",
    zoom=5.2,
    center={"lat" : 43.0, "lon" : 20.5},
    title="Western Balkans Capital Cities",
    size_max=60,
)

fig_bubble.update_layout(
    height=550,
    margin = {"r" : 0, "t" : 50, "l" : 0, "b" : 0},
)

st.plotly_chart(fig_bubble, use_container_width=True)
st.caption("Adjust dropdowns to change what bubble size and color represent")

st.info("City level data used here is used for illustrative purposes")

st.markdown("""
**Where does this go next?**

- **Regional inequality mapping** — a choropleth at municipality level rather than country level reveals local disparities.
- **EU accession progress** — map rule of law scores, trade integration, and regulatory alignment spatially to show which countries and policy areas are lagging in a way that's readable by non-technical audiences.
- **Migration and brain drain** — overlay emigration rates by region with economic indicators to reveal whether people are leaving the poorest areas or whether the pattern is more nuanced.
- **Infrastructure gaps** — map road connectivity, broadband access, or healthcare coverage against population density.
- **Funding overlap and gaps** — map project locations to visualize which areas receive the most investment.
- **Spatial joins** — assign each project to the municipality it falls in and aggregate automatically — total investment per region, population served per intervention. A single line of code in `geopandas`.
""")

st.divider()
st.caption("Next tab: Automation")