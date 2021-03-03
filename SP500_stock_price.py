import streamlit as st
import pandas as pd
import base64
import matplotlib.pyplot as plt
import yfinance as yf

# configurate layout
st.set_page_config(layout="wide",initial_sidebar_state="expanded")

# title and description
st.title("S&P 500 prices")
st.markdown("""
This python application retrieves the list of the **Standard & Poor´s 500**. You can select companies on the sidebar and press the button to get more detailed data and its corresponding stock closing price and volume (year to date). 
""")

expander_bar = st.beta_expander("About")
expander_bar.markdown("""
* **Python libraries: streamlit, pandas, base 64, matplotlib, yfinance**
* **Source of data: [Wikipedia](https://en.wikipedia.org/wiki/List_of_S%26P_500_companies) and yfinance**
""")

st.sidebar.header("User Input Features")

# web scraping of S&P 500 data from wikipedia
@st.cache   # such that we don't have to redownload data every time 
def load_data():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    html = pd.read_html(url, header = 0)
    df = html[0]
    return df

df = load_data()
sector = df.groupby("GICS Sector")

# sidebar - sector selection
sorted_sector_unique = sorted(df["GICS Sector"].unique() )
selected_sector = st.sidebar.multiselect("Filter by Sector", sorted_sector_unique)

# filter data if one or more sectors are selected
if len(selected_sector) > 0:
    df_selected_sector = df[(df["GICS Sector"].isin(selected_sector))]
else:
    df_selected_sector = df # we choose everything, if no filter is applied

# display data
st.header("Display companies in selected sector:")
st.write("Data Dimension: " + str(df_selected_sector.shape[0]) + " rows and " + str(df_selected_sector.shape[1]) + " columns.")
st.dataframe(df_selected_sector)

# sidebar - select companies
selected_companies = st.sidebar.multiselect("Choose companies to plot detailed graphs", df.Security)

# download S&P500 data https://discuss.streamlit.io/t/how-to-download-file-in-streamlit
def filedownload(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()   # strings <-> 
    href = f'<a href="data:file/csv;base64,{b64}" download="SP500.csv">Download CSV File (with respect to filtered sectors)</a>'
    return href

st.markdown(filedownload(df_selected_sector), unsafe_allow_html=True)

if st.button("Get more data from yfinance and show plots for selected companies"):
    
    # https://pypi.org/project/yfinance/
    if len(selected_companies) == 1:
        selected_companies2 = selected_companies + [df.Security[0]]   # workaround, if only one company is selected we have to add another one to keep feature
        df_selected_companies = df[(df["Security"].isin(selected_companies2))] 
        data = yf.download(
            tickers= list(df_selected_companies.Symbol),
            period= "ytd",
            interval= "1d",
            group_by= "ticker",
            auto_adjust= True,
            prepost= True,
            threads= True,
            proxy= None
        )
    elif len(selected_companies) > 1:
        df_selected_companies = df[(df["Security"].isin(selected_companies))]
        data = yf.download(
            tickers= list(df_selected_companies.Symbol),
            period= "ytd",
            interval= "1d",
            group_by= "ticker",
            auto_adjust= True,
            prepost= True,
            threads= True,
            proxy= None
        )
    else:
        df_selected_companies = df[(df["Security"].isin(selected_companies))]
        data = []

    # plot the closing price and valume of query security (company name)
    def price_plot(symbol,security):
        fig, (ax1,ax2) = plt.subplots(2,1)
        fig.suptitle(symbol + " - " + security, fontweight="bold")
        plt.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=None, hspace=0.68)

        df = pd.DataFrame(data[symbol].Close)
        df["Date"] = df.index
        ax1.fill_between(df.Date, df.Close, color="purple", alpha=0.2)
        ax1.plot(df.Date, df.Close, color="purple", alpha=0.8)
        ax1.set(xlabel="Date", ylabel="Closing Price of Stock")
        plt.setp(ax1.get_xticklabels(), rotation=90)

        df2 = pd.DataFrame(data[symbol].Volume)
        df2["Date"] = df2.index
        ax2.fill_between(df2.Date, df2.Volume, color="skyblue", alpha=0.2)
        ax2.plot(df2.Date, df2.Volume, color="skyblue", alpha=0.8)
        ax2.set(xlabel="Date", ylabel="Volume of Stock")
        plt.setp(ax2.get_xticklabels(), rotation=90)
        return st.pyplot(fig)

    
    st.header("Closing Prices and Volumes of selected Stocks:")
    
    # if we don't have choosen any company
    if len(selected_companies) == 0:
        st.write("Choose at least one company first (Sidebar to the left).")
    # if we only have one selected company, skip the dummy entry
    elif len(selected_companies) == 1:
        price_plot(list(df_selected_companies.Symbol)[1],list(df_selected_companies.Security)[1]) 
    # else loop over and plot the whole selection 
    else:
        st.write(df_selected_companies)
        for k in range(len(df_selected_companies.Symbol)):
            price_plot(list(df_selected_companies.Symbol)[k],list(df_selected_companies.Security)[k])

