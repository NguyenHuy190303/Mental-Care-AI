import os
import json
import streamlit as st
import pandas as pd
from datetime import datetime
from src.global_settings import SCORES_FILE
import plotly.graph_objects as go
import src.sidebar as sidebar

st.set_page_config(layout="wide")

# Function to read data from JSON file
def load_scores(file, specific_username):
    if os.path.exists(file) and os.path.getsize(file) > 0:
        with open(file, 'r') as f:
            data = json.load(f)
        # Filter data by specific username
        df = pd.DataFrame(data)
        new_df = df[df["username"] == specific_username]
        return new_df
    else:
        return pd.DataFrame(columns=["username", "Time", "Score", "Content", "Total guess"])

def score_to_numeric(score):
    score = score.lower()
    if score == "poor":
        return 1
    elif score == "average":
        return 2
    elif score == "good":
        return 3
    elif score == "excellent":
        return 4

def plot_scores(df):
    # Convert 'Time' column to datetime type
    df['Time'] = pd.to_datetime(df['Time'])

    # Filter data for the last 7 days from the latest date
    recent_date = df['Time'].max()
    start_date = recent_date - pd.Timedelta(days=6)
    df_filtered = df[(df['Time'] >= start_date) & (df['Time'] <= recent_date)]

    # Sort data by time
    df_filtered = df_filtered.sort_values(by='Time')

    # Define color map
    color_map = {
        'poor': 'red',
        'average': 'orange',
        'good': 'yellow',
        'excellent': 'green'
    }

    # Map 'Score' values to colors
    df_filtered['color'] = df_filtered['Score'].map(color_map)
    
    # Create plot using Plotly
    fig = go.Figure()

    # Plot lines between points over time
    fig.add_trace(go.Scatter(
        x=df_filtered['Time'],
        y=df_filtered['Score_num'],
        mode='lines+markers',
        marker=dict(size=24, color=df_filtered['color']),
        text=df_filtered['Score'],
        line=dict(width=2)
    ))

    # Set chart properties
    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Score',
        xaxis=dict(tickformat='%Y-%m-%d'),
        yaxis=dict(tickvals=[1, 2, 3, 4], ticktext=['poor', 'average', 'good', 'excellent']),
        hovermode='x unified'
    )

    # Display chart in Streamlit
    st.plotly_chart(fig)
    
def main():
    sidebar.show_sidebar()

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if st.session_state.logged_in:
        # Create interface with Streamlit
        st.markdown('# Track Your Mental Health Information')
        
        # Load data from file
        df = load_scores(SCORES_FILE, st.session_state.username)
        if not df.empty:
            df["Time"] = pd.to_datetime(df["Time"])
            df["Score_num"] = df["Score"].apply(score_to_numeric)
            df["Score"] = df["Score"].str.lower()
            # Display mental health score chart
            st.markdown("## Your Mental Health Score Over the Past 7 Days")
            plot_scores(df)
        # Select a date to retrieve information
        st.markdown("## Retrieve Mental Health Information by Date")
        date = st.date_input("Select date", datetime.now().date())
        selected_date = pd.to_datetime(date)
        if not df.empty:
            filtered_df = df[df["Time"].dt.date == selected_date.date()]

            if not filtered_df.empty:
                st.write(f"Information for {selected_date.date()}:")
                for index, row in filtered_df.iterrows():
                    st.markdown(f"""
                    **Time:** {row['Time']}  
                    **Score:** {row['Score']}  
                    **Content:** {row['Content']}  
                    **Total guesses:** {row['Total guess']}  
                    """)
            else:
                st.write(f"No data available for {selected_date.date()}")
        st.markdown("## Detailed Data Table")
        st.table(df)    

if __name__ == "__main__":
    main()
