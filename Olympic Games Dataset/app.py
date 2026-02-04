
import streamlit as st
import pandas as pd
import plotly.express as px

# Set page configuration
st.set_page_config(page_title="Olympic Games Analysis", layout="wide")

# Title and Introduction
st.title("Olympic Games Data Analysis")
st.markdown("""
This dashboard provides an in-depth analysis of the Olympic Games dataset.
Explore trends in medals, participation, and key insights across history.
""")

# --- Data Loading & Cleaning ---
@st.cache_data
def load_data():
    try:
        # Load datasets
        summer = pd.read_csv("SummerSD.csv")
        winter = pd.read_csv("WinterSD.csv")
        countries = pd.read_csv("CountriesSD.csv")

        # Clean Winter data: Rename 'Country' to 'Code' to match Summer/Countries
        # In WinterSD, 'Country' column holds the 3-letter code (e.g., FRA)
        winter.rename(columns={"Country": "Code"}, inplace=True)

        # Add Season column
        summer['Season'] = 'Summer'
        winter['Season'] = 'Winter'

        # Concatenate Summer and Winter
        # Note: Summer has a 'Country' column (Name), Winter does not (it has Code).
        # We will drop the 'Country' name from Summer before merge to avoid confusion,
        # and rely on CountriesSD for the canonical name.
        if 'Country' in summer.columns:
            summer = summer.drop(columns=['Country'])
        
        olympics = pd.concat([summer, winter], ignore_index=True)

        # Merge with CountriesSD to get Country Name, Population, GDP
        # CountriesSD: Country,Code,Population,GDP per Capita
        # We merge on 'Code'
        data = pd.merge(olympics, countries, on="Code", how="left")

        # Fill missing Country names with Code if not found
        data['Country'] = data['Country'].fillna(data['Code'])

        return data
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

df = load_data()

if df is not None:
    # --- Sidebar Filters ---
    st.sidebar.header("Filters")
    years = sorted(df['Year'].unique())
    selected_year = st.sidebar.multiselect("Select Year", years, default=years)
    
    seasons = df['Season'].unique()
    selected_season = st.sidebar.multiselect("Select Season", seasons, default=seasons)

    filtered_df = df[ (df['Year'].isin(selected_year)) & (df['Season'].isin(selected_season)) ]

    # --- Key Metrics ---
    st.header("Snapshot")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Editions", filtered_df['Year'].nunique())
    col2.metric("Total Athletes (Entries)", filtered_df['Athlete'].nunique()) # Approx, as names might duplicate
    col3.metric("Total Countries", filtered_df['Country'].nunique())
    col4.metric("Total Medals", filtered_df['Medal'].count())

    # --- 1. Medal Tally ---
    st.header("Medal Tally")
    # Pivot table for medals
    medal_tally = filtered_df.groupby(['Country', 'Medal']).size().unstack(fill_value=0)
    # Ensure Gold, Silver, Bronze columns exist
    for m in ['Gold', 'Silver', 'Bronze']:
        if m not in medal_tally.columns:
            medal_tally[m] = 0
            
    medal_tally['Total'] = medal_tally['Gold'] + medal_tally['Silver'] + medal_tally['Bronze']
    medal_tally = medal_tally.sort_values(by='Total', ascending=False)
    
    st.dataframe(medal_tally)

    # --- 2. Participation Trends ---
    st.header("Trends Over Time")
    
    tab1, tab2 = st.tabs(["Nations Participating", "Gender Participation"])
    
    with tab1:
        nations_over_time = df.groupby(['Year', 'Season'])['Code'].nunique().reset_index()
        fig_nations = px.line(nations_over_time, x='Year', y='Code', color='Season', 
                              title='Number of Participating Nations over Time',
                              labels={'Code': 'Count of Nations'})
        st.plotly_chart(fig_nations, use_container_width=True)
        
    with tab2:
        gender_over_time = df.groupby(['Year', 'Season', 'Gender']).size().reset_index(name='Count')
        fig_gender = px.line(gender_over_time, x='Year', y='Count', color='Gender', symbol='Season',
                             title='Male vs Female Participation (Medal Events) over Time')
        st.plotly_chart(fig_gender, use_container_width=True)

    # --- 3. Top Sports ---
    st.header("Top Sports")
    top_sports = filtered_df['Sport'].value_counts().head(10).reset_index()
    top_sports.columns = ['Sport', 'Medal Count']
    fig_sports = px.bar(top_sports, x='Sport', y='Medal Count', title="Top 10 Sports by Medal Count")
    st.plotly_chart(fig_sports, use_container_width=True)

    # --- 4. Country Analysis ---
    st.header("Country Profile")
    country_list = sorted(df['Country'].unique().astype(str))
    selected_country = st.selectbox("Select a Country to Analyze", country_list)
    
    country_df = df[df['Country'] == selected_country]
    
    if not country_df.empty:
        c_col1, c_col2 = st.columns(2)
        
        # Medals by Sport
        sport_medals = country_df.groupby('Sport')['Medal'].count().reset_index().sort_values(by='Medal', ascending=False).head(10)
        fig_c_sports = px.pie(sport_medals, values='Medal', names='Sport', title=f"Top Sports for {selected_country}")
        c_col1.plotly_chart(fig_c_sports, use_container_width=True)
        
        # Medals over time
        medals_time = country_df.groupby('Year')['Medal'].count().reset_index()
        fig_c_time = px.bar(medals_time, x='Year', y='Medal', title=f"Medals Timeline for {selected_country}")
        c_col2.plotly_chart(fig_c_time, use_container_width=True)
    else:
        st.info("No data for selected country in current filter.")

else:
    st.warning("Data could not be loaded. Please check file paths.")
