import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from collections import Counter
import re

st.set_page_config(page_title="Data and Text Analysis",
                   page_icon="📡", layout="wide")

st.title("Data and Text Analysis")
st.markdown("Python can pull data from the web in two ways: **APIs** and **webscraping**. " \
"Always check if API is available first.")

st.divider()

#Section 1: API or Scraping
st.header("Getting the data")

has_api = st.radio(
    "Does your data source have an API?",
    ["Yes - Use the API", "No - Scrape it instead"],
    help="API is a structured way to request data directly from the source. It is much more realiable than scraping."
)

if has_api == "Yes - Use the API": 
    st.success("Great - clean data, with minimal code")

    st.markdown("""
    We will use the **World Bank API** - free and no key required.
    
    ```python
    import requests
    url = "https://api.worldbank.org/v2/country/US/indicator/NY.GDP.MKTP.CD?format=json&per_page=20"
    response = requests.get(url)
    data = response.json()
    ```
                
    """)

    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        country_options = {
            "Albania" : "AL",
            "Bosnia and Herzegovina" : "BA",
            "Kosovo" : "XK",
            "Montenegro" : "ME",
            "North Macedonia" : "MK",
            "Serbia" : "RS"
        }
        country_name = st.selectbox("Select a country", list(country_options.keys()))
        country_code = country_options[country_name]

    with col2: 
        indicator_options = {
            "GDP (US$)": "NY.GDP.MKTP.CD",
            "GDP per capita (US$)" : "NY.GDP.PCAP.CD",
            "Inflation, consumer prices (%)" : "FP.CPI.TOTL.ZG",
            "Unemployment" : "SL.UEM.TOTL.ZS"
        }
        indicator_name = st.selectbox("Select an indicator", list(indicator_options.keys()))
        indicator_code = indicator_options[indicator_name]

    with col3:
        years = st.slider("Year range", 2010, 2023, (2016, 2023))

    @st.cache_data(show_spinner=False)
    def fetch_wb_data(country_code, indicator_code, indicator_name):
        url = (
                    f"https://api.worldbank.org/v2/country/{country_code}/indicator/{indicator_code}"
                    f"?format=json&per_page=30"
                )
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        raw = response.json()

        #API returns
        records = raw[1]
        df = pd.DataFrame([
            {"Year" : int(r["date"]), indicator_name: r['value']}
            for r in records if r["value"] is not None 
        ]).sort_values("Year")

        return df

    if st.button("Fetch from World Bank API", type = "primary"):
        with st.spinner("Calling from API"):
            try:
                df = fetch_wb_data(country_code, indicator_code, indicator_name)
                df = df[(df["Year"] >= years[0]) & (df["Year"] <= years[1])]

                st.success(f"Fetched {len(df)} records for {country_name}")

                col_table, col_chart = st.columns([1,2])
                with col_table:
                    st.dataframe(df.set_index("Year"), use_container_width=True)
                with col_chart:
                    fig = px.line(
                        df, x = 'Year', y = indicator_name,
                        title = f"{indicator_name} - {country_name}",
                        markers=True,
                        color_discrete_sequence=["#2563eb"]
                    )
                    fig.update_layout(
                        plot_bgcolor = "white",
                        yaxis_title = indicator_name,
                        xaxis_title = "Year"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                #For text analysis
                st.session_state["api_df"] = df
                st.session_state["api_country"] = country_name
                st.session_state['api_indicator'] = indicator_name

            except Exception as e:
                st.error(f"API call failed: {e}")
                st.error("This is why we have a scraping fallback")

else:
    st.warning("No API available - we use scraping instead. \n" \
    "Note: Much more fragile and heavily depends on the website's structure")

    st.markdown("""
    We will scrape a table of economic data from **Wikipedia** using "requests" + "pandas"
    """)

    #Step 1: Naive attempt
    st.markdown("First approach should be to point 'pandas' directly to the url")

    st.code("""
    
    import pandas as pd
    
    url = "https://en.wikipedia.org/wiki/List_of_countries_by_GDP_(nominal)"
    tables = pd.read_html(url) #List of all tables on the page
    df = tables[2] #Pick the right table
                   
    """, language='python')

    if st.button("Scrape Wikipedia", type = "primary"):
        with st.spinner("Scraping Wikipedia..."):
            try:
                tables = pd.read_html("https://en.wikipedia.org/wiki/List_of_countries_by_GDP_(nominal)")
                st.success("Sometimes websites allow this")
                st.session_state["naive_scrape_run"] = True
            except Exception as e:
                st.error(f"Failed: {e}")
                st.markdown("""
                **As we can see the request failed!**
                **Why did it fail?** Wikipedia's servers detected that this request did not come from a browser,
                so it got blocked with a 403 Forbidden error.
                This is extremely common when trying to scrape.
                """)
                st.session_state["naive_scrape_run"] = True

    #Step 2: Actual scrape
    if st.session_state.get("naive_scrape_run", False):
        st.markdown("The fix: pretend we are a browser")
        st.markdown("""
        We use **headers**, we tell the website a browser is making this request rather than a script.
        """)

        st.code("""
        import requests, pandas as pd
        from io import StringIO

        #Tell the server we are a browser:
        headers = {"User-Agent" : "Mozzila/5.0"}  

        url = "https://en.wikipedia.org/wiki/List_of_countries_by_GDP_(nominal)"
        response = requests.get(url, headers = headers)
        tables = pd.read_html(StringIO(response.text))
        df = tables[2]
        """, language="python")

        if st.button("Run fixed scraping algorithm", type="primary"):
            with st.spinner("Scrapin in progress..."):
                try:
                    from io import StringIO
                    wb_countries = ['Albania', 'Bosnia and Herzegovina', 'Kosovo', 'Montenegro', 'Macedonia', 'Serbia']

                    headers = {"User-Agent" : "Mozilla/5.0"}
                    url = "https://en.wikipedia.org/wiki/List_of_countries_by_GDP_(nominal)"
                    response = requests.get(url, headers=headers, timeout=30)
                    response.raise_for_status()
                    tables = pd.read_html(StringIO(response.text))

                    df = None
                    for t in tables:
                        cols = [str(c).lower() for c in t.columns.get_level_values(0)]
                        if any("imf" in c or "country" in c or "region" in c for c in cols):
                            if len(t) > 50:
                                df = t
                                break
                    
                    if df is None:
                        df = tables[2]

                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = [' '.join(str(c) for c in col if "Unnamed" not in str(c)).strip() for col in df.columns]

                    country_col = next((c for c in df.columns if "country" in c.lower() or 'economy' in c.lower()), df.columns[0])
                    mask = df[country_col].astype(str).str.contains("|".join(wb_countries), case=False, na=False)
                    df_filtered = df[mask]

                    if df_filtered.empty:
                        st.warning("Couldn't find any WB countries in this table - showing top 30 instead")
                        df_filtered = df.head(30)

                    st.success(f"Scraped and filtered to {len(df_filtered)} Western Balkans countries")
                    st.dataframe(df_filtered, use_container_width=True)
                    # st.caption("Look at column names compared to the API fetched data!!")

                except Exception as e:
                    st.error(f"Scraping failed: {e}")
                    st.info("Even with the fix scraping can break if a website changes it structure. This is exactly why APIs are preffered")
        
        st.markdown("""
        As you can see when calling on the API we aquire more data with less code, here with more code we only acquire one table.
""")
st.divider()

st.header("Function APIs ")
st.markdown("""
The World Bank API we used earlier is a **data API** — it stores information and returns it when asked. 
But there's a second type: **function APIs**, where you send an input and the server *computes* 
something for you in real time.
            
A clear example is currency conversion. The **Frankfurter API** doesn't just store a table of rates — 
it computes the conversion between any two currencies when you call it. 
You're calling a function on a remote server, exactly like calling a function in your own code, 
except it runs somewhere else and you get the result back over the internet.
""")

st.code("""
import requests

# Send: base currency, target currency, amount
# Receive: computed conversion — calculated in real time, not looked up from a table
url = "https://api.frankfurter.app/latest?from=USD&to=EUR&amount=1000"
response = requests.get(url)
data = response.json()
        
converted = data['rates']['EUR]
""", language='python')

currencies = {
    "Euro (EUR)": "EUR",
    "US Dollar (USD)": "USD",
    "British Pound (GBP)": "GBP",
    "Swiss Franc (CHF)": "CHF",
    "Japanese Yen (JPY)": "JPY",
    "Canadian Dollar (CAD)" : "CAD"
}

st.markdown("Pick two currencies and enter the ammount:")

col1, col2, col3 = st.columns([1,1,1])
with col1:
    from_currency = st.selectbox("From currency", list(currencies.keys()), index=0)
    from_code = currencies[from_currency]
with col2:
    to_currency = st.selectbox("To currency", list(currencies.keys()), index = 1)
    to_code = currencies[to_currency]
with col3:
    amount = st.number_input("Amount", min_value=0.0, value=1000.0, step=100.0)

@st.cache_data(show_spinner=False, ttl=3600)
def fetch_exchange_rate(from_code, to_code, amount):
    """"Call Frankfurter API and compute the exchange rate"""
    url = f"https://api.frankfurter.app/latest?from={from_code}&to={to_code}&amount={amount}"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()

if st.button("Convert Currency", type="primary"):
    with st.spinner("Calling Frankfurter API"):
        try:
            if from_code == to_code:
                st.warning("Please select two different currencies!")
            else:
                data = fetch_exchange_rate(from_code, to_code, amount)
                converted = data['rates'][to_code]
                rate = converted / amount
                date = data['date']

                col1, col2, col3 = st.columns([1,1,1])
                with col1:
                    st.metric("Exchange Rate", f"1 {from_code} = {rate:.4f} {to_code}")
                with col2:
                    st.metric(f"Amount ({from_code})", f"{amount:,.2f}")
                with col3:
                    st.metric(f"Converted ({to_code})", f"{converted:,.2f}")

                st.caption(f"Rate as of {date} - data from Frankfurter API")
                st.info("""
                As we can see the call to the World Bank API simply **retrieved** stored data, while the call to the Frankfurter API
                    **computed** a result.
                 """)
        except Exception as e:
            import traceback
            st.error(f"Conversion failed: {e}")
            st.code(traceback.format_exc())

st.divider()

st.header("Text Analysis")
st.markdown("""
Once we have unstructured text, wheter scraped or pulled from an API or loaded in from documents; Python makes is straightforward
to analyse. Here, a simple pipeline is shown that can be easily scaled to thousands of documents


We are going to go **step by step**, using a set of generated economic headlines.
""")

headlines = [
    "Federal Reserve raises interest rates amid inflation concerns",
    "Global GDP growth slows as trade tensions escalate",
    "Unemployment falls to record low despite inflation pressures",
    "Central banks signal pause in rate hike cycle after inflation data",
    "IMF warns of recession risk as growth forecasts downgraded",
    "Consumer prices rise sharply driven by energy and food costs",
    "Labour market remains resilient despite higher borrowing costs",
    "China GDP growth disappoints as property sector woes continue",
    "Eurozone inflation eases but core prices remain stubbornly high",
    "World Bank cuts global growth outlook citing debt distress",
    "US Federal Reserve holds rates steady watching inflation data",
    "Emerging markets face capital outflows as dollar strengthens",
    "Supply chain disruptions ease but inflation remains elevated",
    "Fiscal deficit widens as governments face higher debt servicing costs",
    "Strong jobs report complicates Federal Reserve rate cut plans",
]

stopwords = {
    "the", "a", "an", "as", "at", "by", "in", "of", "on", "to", "up",
   "and", "but", "for", "its", "is", "are", "be", "amid", "after",
    "despite", "while", "with", "from", "that", "has", "have", "also",
    "remain", "remains", "cut", "cuts", "face", "faces", "but", "or"
}

with st.expander("Our news  headlines"):
    for i, h in enumerate(headlines, 1):
        st.markdown(f"`{i}`.`{h}`")


st.markdown("---")

#Step 1: Tokenisation

st.markdown("#### Step 1 - Tokenisation")
st.markdown("""
The first step is **tokenisation** - splitting raw text into individual words(tokens).
We also lowercase everything so that `Inflation` and `inflation` are treated the same.
""")

st.code("""
import re

#Combine all headlines into one string, convert to lowercase
all_text = " ".join(headlines).lower()
        
#Use regex to extract only alphabetics words
# \\b = word boundary, [a-z]+ = one or more letters
tokens = re.findall(r'\\b[a-z]+\\b', all_text)

""", language="python")

all_text = " ".join(headlines).lower()
all_tokens = re.findall(r'\b[a-z]+\b', all_text)

with st.expander(f"See raw tokens ({len(all_tokens)} total)"):
    st.write(all_tokens)

st.markdown("---")

#Step 2: Stopword removal
st.markdown("#### Step 2 - Stopword removal")
st.markdown("""
Raw tokens include a lot of common words like *"the"*, *"and"*, *"as"* that carry no analytical meaning. 
We refer to them as **stopwords**. We filter them out, along with very short words.
""")

st.code("""
stopwords = {
    "the", "a", "an", "as", "at", "by", "in", "of", "on", "to", "up",
   "and", "but", "for", "its", "is", "are", "be", "amid", "after",
    "despite", "while", "with", "from", "that", "has", "have", "also",
    "remain", "remains", "cut", "cuts", "face", "faces", "but", "or"
}

#Keep a token only if it's not a stopword and long enough to have meaning
min_length = 4
        
tokens_clean = [t for t in tokens if t not in stopwords and len(t) >= min_length]
        
""", language="python")

min_word_len = st.slider("Minimum word length to include", 3, 8, 4)
tokens_clean = [t for t in all_tokens if t not in stopwords and len(t) >= min_word_len]

col1, col2 = st.columns([1,1])
with col1:
    st.metric("Tokens before filtering", len(all_tokens))
with col2:
    st.metric("Tokens after filtering", len(tokens_clean))

with st.expander("See cleaned tokens"):
    st.write(tokens_clean)

st.markdown("---")


#Step 3: Frequency count + unigrams
st.markdown("#### Step 3 - Frequency analysis (unigrams)")
st.markdown("""
Now we count how often each term appears using a built in Python function.
This gives us the most prominent **single words** (unigrams) across all headlines.
""")

st.code("""
from collections import Counter

#Count occurrences of each token
counts = Counter(tokens_clean)
        
#Get the N most common terms as a list of tuples (word, counts)
top_terms = counts.most_common(10)
""", language="python")

top_n = st.slider("Number of top terms to show", 5, 20, 10)
counts = Counter(tokens_clean)
top_terms = counts.most_common(top_n)
freq_df = pd.DataFrame(top_terms, columns=['Term', "Frequency"])

fig_uni = px.bar(
    freq_df.sort_values("Frequency"),
    x = "Frequency", y = "Term",
    orientation="h",
    title="Most Frequent Single Terms (Unigrams)",
    color="Frequency",
    color_continuous_scale="Reds"
)
fig_uni.update_layout(
    plot_bgcolor = 'white',
    showlegend = False,
    coloraxis_showscale = False,
    yaxis_title = "",
)


st.plotly_chart(fig_uni, use_container_width=True)

st.markdown("---")

#Step 4: Bigrams
st.markdown('#### Step 4 - Bigrams (Two-word phrases)')
st.markdown("""
Single words can be ambigous - *bank* can mean many things. So to expand our analysis we us **Bigrams**, these are pairs of consecutive
            words that carry meaning together - **central bank** or **interest rate**.
This is the point where analyzing text is useful for economic research.
""")

st.code("""
#Bigram is a pair of adjacent tokens
#zip(tokens, tokens[1:]) pairs each word with the next one
bigrams = list(zip(tokens_clean, tokens_clean[1:]))
        
#Count them the same way as unigrams
bigram_counts = Counter(bigrams).most_common(10)
        
#Format for display
bigram_df = pd.DataFrame(
    [(" ".join(b), c) for b, c in bigram_counts],
    columns=["Bigram", "Frequency"]
)
""", language="python")

bigrams = list(zip(tokens_clean, tokens_clean[1:]))
bigram_counts = Counter(bigrams).most_common(top_n)
bigram_df = pd.DataFrame(
    [(" ".join(b), c) for b, c in bigram_counts],
    columns=["Bigram", "Frequency"]
)

fig_bi = px.bar(
    bigram_df.sort_values("Frequency"),
    x="Frequency", y="Bigram",
    orientation="h",
    title="Most Frequent Two-Word Phrases (Bigrams)",
    color="Frequency",
    color_continuous_scale="Greens",
)
fig_bi.update_layout(
    plot_bgcolor="white",
    showlegend=False,
    coloraxis_showscale=False,
    yaxis_title="",
)
st.plotly_chart(fig_bi, use_container_width=True)

st.markdown("---")

#Step 5: Sentiment Analysis
st.markdown("#### Step 5 - Sentiment Analysis")
st.markdown("""
By using the steps above we performed a **frequency analysis** allowing us to estimate which are the most mentioned topics. 
However, the same 15 headlines we've been analysing can  be passed through a completely 
different type of analysis — **sentiment scoring**. 
Instead of counting words, we can assess wheter the headline is positive, negative, or neutral!

            

We use **VADER** (Valence Aware Dictionary and sEntiment Reasoner) from the `nltk` library. 
VADER is designed specifically for short texts like news headlines. It returns a **compound score** 
between **-1** (very negative) and **+1** (very positive).
""")

st.code("""
from nltk.sentiment.vader import SentimentIntensityAnalyzer

analyser = SentimentIntensityAnalyzer()

for headline in headlines:
    scores = analyser.polarity_scores(headline)
    compound = scores["compound"]  # -1 (very negative) → 0 (neutral) → +1 (very positive)
""", language="python")

try:
    import nltk
    from nltk.sentiment.vader import SentimentIntensityAnalyzer


    nltk.download("vader_lexicon", quiet=True)
    analyzer = SentimentIntensityAnalyzer()

    sentiment_data = []
    for headline in headlines:
        scores = analyzer.polarity_scores(headline)
        compound = scores['compound']
        if compound > 0.05:
            label = "Positive"
        elif compound < -0.05:
            label = "Negative"
        else:
            label = "Neutral"
        
        sentiment_data.append({
            "Headline" : headline,
            "Score" : round(compound, 3),
            "Sentiment" : label
        })

    sentiment_df = pd.DataFrame(sentiment_data)

    #Chart 
    fig_sent = px.bar(
        sentiment_df.sort_values("Score"),
        x="Score", y="Headline",
        orientation='h',color="Score",
        color_continuous_scale='RdYlGn', color_continuous_midpoint=0,
        title="Sentiment Score per Headline"
    )
    fig_sent.update_layout(
        plot_bgcolor = 'white', coloraxis_showscale = True,
        coloraxis_colorbar = {"title" : "Compound"}, yaxis_title = "",
        xaxis_title = "Polarity Score (-1 = Negative, +1 = Positive)",
        height = 500, margin = {"l" : 300}
    )
    fig_sent.add_vline(x=0, line_dash = "dash", line_color = "grey")
    st.plotly_chart(fig_sent, use_container_width=True)

    #Table
    with st.expander("Full Sentiment Scores"):
        st.dataframe(sentiment_df, use_container_width=True)
    
    #Summary metrics
    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        n_pos = sum(1 for r in sentiment_data if r['Score'] > 0.05)
        st.metric("Positive headlines", n_pos)
    with col2:
        n_neu = sum(1 for r in sentiment_data if -0.05 <= r['Score'] <= 0.05)
        st.metric("Neutral headlines", n_neu)
    with col3:
        n_neg = sum(1 for r in sentiment_data if r["Score"] < -0.05)
        st.metric("Negative headline", n_neg)

    st.caption("""
    In steps 1-4 we preformed frequency analysis and in step 5 we perform sentiment analysis. 
               This is done on the same dataset without any reformatting or new data.
                This is the power of Python's libraries - they plug into each other allowing for an in depth analysis.
    """)
    st.info("""
    **Vader** is a general purpose tool for news headlines, so it has some limitations in financial contexts.
            It was chosen because its lightweight and easy to implement for demo purposes. 
    """)

except ImportError:
    st.error("TextBlob not installed")

st.markdown("---")
st.markdown("""
This pipeline - tokenise, clean, count - is the foundation of more advanced techniques that can be implemented:

- **Topic modelling** - discover themes across hundreads of documents
- **Named entity recognition** - Exctract countries, organisations and people from text
- **TF-IDF** - find terms that are distinctive to a document
            
All of these are possible by using Python libraries and within a few lines of code.
""") 

st.divider()
st.caption("Next tab: Geospatial analysis")


