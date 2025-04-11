# pages/plot.py
import dash
from dash import html, dcc, callback, Input, Output
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objs as go
from datetime import datetime, timedelta
import requests

# Register this file as a page
dash.register_page(__name__, path="/plot", title="Summary Plot")

# Define the layout - don't run data fetch during import

layout = html.Div([
    html.H2("Summary Plot"),
    dcc.Graph(id="Status-Distribution-plot"),
    dcc.Graph(id="Newly-harmonised-plot"),
    dcc.Graph(id="Dropping-rate-plot"),
    html.Div(id="plot-error-message"),
    dcc.Interval(
        id="interval-update",
        interval=5 * 1000,  # Update every 5 seconds (adjust as needed)
        n_intervals=0,
    )
    ],
    style={
        'width': '100%', 
        'height': '100vh', 
        'display': 'flex', 
        'flexDirection': 'column'}
)

def get_data(route): 
    try:
        base="http://127.0.0.1:8000/"
        URL = base + route
        response = requests.get(URL)
        return pd.DataFrame(response.json())
    except requests.exceptions.RequestException:
        return []

# Create callback to load the data and generate the plot
@callback(
    Output("Status-Distribution-plot", "figure"),
    Output("Newly-harmonised-plot", "figure"),
    Output("Dropping-rate-plot", "figure"),
    Output("plot-error-message", "children"),
    Input("Status-Distribution-plot", "id")
)


def update_plots(_):
    # Status Distribution Plot
    status_table=get_data("plotly/status_bar")
    status_table['Harm_status'] = status_table['Harm_status'].str.strip()

    fig1 = px.bar(
        status_table,
        x='Harm_status', 
        y='num_unique_studies', 
        text='num_unique_studies',
        title='Current Harmonisation Status',
        labels={'Harm_status': 'Status', 'num_unique_studies': 'Count'},
        color='Harm_status'
        )
    fig1.update_layout(xaxis={'categoryorder':'total descending'}) 
    
    # Newly Harmonised Plot 
    # Newly harmonised data in the last 6 month (Bar Chart)
    newly_harmonised = get_data("plotly/harmed_six_month")

    fig2 = px.bar(
        newly_harmonised, 
        x='month',
        y='num_studies',
        text='num_studies',
        title='Newly Harmonised Sumstats (Recent 6 months)'
        )
    
    # Dropping Rate Plot by year
    # Fig3.1: For sequencing data
    # Fig 3.2: For Array data
    # Fig 3.3: For combined data

    fig3 = make_subplots(rows=1, cols=3, subplot_titles=["Array Drop Rate", "Sequencing Drop Rate", "mix Drop Rate"])

    # Subplot 1: Drop Rate by Account
    array_data=get_data("plotly/drop_rate/array")
    array_data['Harm_drop_rate'] =  array_data['Harm_drop_rate'].astype(float)
    array_data['year'] =  array_data['year'].astype(int)
    sequencing_data=get_data("plotly/drop_rate/sequencing")
    sequencing_data['Harm_drop_rate'] =  sequencing_data['Harm_drop_rate'].astype(float)
    sequencing_data['year'] =  sequencing_data['year'].astype(int)
    mix_data=get_data("plotly/drop_rate/mix")
    mix_data['Harm_drop_rate'] =  mix_data['Harm_drop_rate'].astype(float)
    mix_data['year'] =  mix_data['year'].astype(int)

    fig3.add_trace(
        go.Scatter(
            y=array_data["Harm_drop_rate"],
            x=array_data["year"],
            name="Array Drop Rate",
            mode='markers',  # Show markers with text labels
            text=array_data['Study'],  # Show study names
            textposition='top center',  # Position text labels
            marker=dict(
                size=8,  # Size of markers
                color=array_data["Harm_drop_rate"], 
                colorscale='Viridis',  # Color scale
                #showscale=True  # Show color scale
                ),
            ),
        row=1, col=1
    )

    fig3.add_hline(
        y=0.15,  # 0.2 corresponds to 20%
        line=dict(
            color='red',  # Color of the line
            width=2,  # Line width
            dash='dash'  # Line style, e.g., 'dash', 'dot', 'solid'
            ),
            row=1, col=1  # Add to the 1st subplot (Array Drop Rate)
            )
    
     # Subplot 2: Drop Rate by Study

    fig3.add_trace(
        go.Scatter(
            y=sequencing_data["Harm_drop_rate"],
            x=sequencing_data["year"],
            name="Array Drop Rate",
            mode='markers',  # Show markers with text labels
            text=array_data['Study'],  # Show study names
            textposition='top center',  # Position text labels
            marker=dict(
                size=8,  # Size of markers
                color=array_data["Harm_drop_rate"], 
                colorscale='Viridis',  # Color scale
                #showscale=True  # Show color scale
                ),
            ),
        row=1, col=2
    )

    fig3.add_hline(
        y=0.2,  # 0.2 corresponds to 20%
        line=dict(
            color='red',  # Color of the line
            width=2,  # Line width
            dash='dash'  # Line style, e.g., 'dash', 'dot', 'solid'
            ),
            row=1, col=2  # Add to the 1st subplot (Array Drop Rate)
            )
    
    # Subplot 3: Drop Rate by Date
    
    fig3.add_trace(
        go.Scatter(
            y=mix_data["Harm_drop_rate"],
            x=mix_data["year"],
            name="Array Drop Rate",
            mode='markers',  # Show markers with text labels
            text=array_data['Study'],  # Show study names
            textposition='top center',  # Position text labels
            marker=dict(
                size=8,  # Size of markers
                color=array_data["Harm_drop_rate"], 
                colorscale='Viridis',  # Color scale
                #showscale=True  # Show color scale
                ),
            ),
        row=1, col=3
    )

    fig3.update_yaxes(
    tickformat='.2%'
    )

    fig3.update_layout(
        title_text="Harmonisation Drop Rate Plots (Past 10 Years) with dropping rate > 0.15", 
        showlegend=False,
        xaxis = dict(
            tickmode='array',  # Use an array for tick values
            tickvals=array_data['year'].dropna().unique(),  # Set the tick positions to unique years
            ticktext=[str(year) for year in array_data['year'].dropna().unique()],  # Use year as text labels
            title="Year"
        ),  # Rotate x-axis labels for better readability
        xaxis2 = dict(
            tickmode='array',  # Use an array for tick values
            tickvals=sequencing_data['year'].dropna().unique(),  # Set the tick positions to unique years
            ticktext=[str(year) for year in sequencing_data['year'].dropna().unique()],  # Use year as text labels
            title="Year"
        ),
        xaxis3 = dict(
            tickmode='array',  # Use an array for tick values
            tickvals=mix_data['year'].dropna().unique(),  # Set the tick positions to unique years
            ticktext=[str(year) for year in mix_data['year'].dropna().unique()],  # Use year as text labels
            title="Year"
        ),
    )

    return fig1,fig2,fig3,""