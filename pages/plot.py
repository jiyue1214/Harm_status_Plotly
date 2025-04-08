# pages/plot.py
import dash
from dash import html, dcc, callback, Input, Output
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objs as go
from datetime import datetime, timedelta

# Register this file as a page
dash.register_page(__name__, path="/plot", title="Summary Plot")

# Define the layout - don't run data fetch during import

layout = html.Div([
    html.H2("Summary Plot"),
    dcc.Graph(id="Status-Distribution-plot"),
    dcc.Graph(id="Newly-harmonised-plot"),
    dcc.Graph(id="Dropping-rate-plot"),
    html.Div(id="plot-error-message")
    ],
    style={
        'width': '100%', 
        'height': '100vh', 
        'display': 'flex', 
        'flexDirection': 'column'}
)

# Create callback to load the data and generate the plot
@callback(
    Output("Status-Distribution-plot", "figure"),
    Output("Newly-harmonised-plot", "figure"),
    Output("Dropping-rate-plot", "figure"),
    Output("plot-error-message", "children"),
    Input("shared-data", "data")
)

def update_plots(data):
    
    if not data:
        return px.bar(), px.bar(), px.bar(), "Error: No data found or unable to connect to FastAPI."
    
    df = pd.DataFrame(data)
    
    # Status Distribution Plot
    # Showing the distribution of harmonised data, pending data, failed data (+) in the last 6 month (Pie Chart)

    fig1 = px.bar(
        df['Harm_status'].value_counts().reset_index(),
        x='Harm_status', 
        y='count', 
        text='count',
        title='Current Harmonisation Status',
        labels={'Harm_status': 'Status', 'count': 'Count'},
        color='Harm_status'
        )
    
    # Newly Harmonised Plot 
    # Newly harmonised data in the last 6 month (Bar Chart)
    df['Latest_harm_start_date'] = pd.to_datetime(df['Latest_harm_start_date'],errors='coerce')

    six_months_ago = datetime.now() - timedelta(days=6 * 30) 
    df_six_month = df[df['Latest_harm_start_date'] >= six_months_ago]
    df_six_month['year_month'] = df_six_month['Latest_harm_start_date'].dt.to_period('M').astype(str)

    fig2 = px.bar(
        df_six_month['year_month'].value_counts().reset_index(), 
        x='year_month',
        y='count',
        text='count',
        title='Newly Harmonised Sumstats (Recent 6 months)'
        )
    
    # Dropping Rate Plot by year
    # Fig3.1: For sequencing data
    # Fig 3.2: For Array data
    # Fig 3.3: For combined data
    df_drop_rate = df[df['Harm_drop_rate'] != 'NA']
    df_drop_rate['Harm_drop_rate'] = df_drop_rate['Harm_drop_rate'].astype(float)

    df_drop_rate['Publication_date'] = pd.to_datetime(df['Publication_date'],errors='coerce')

    df_drop_rate['year'] = df_drop_rate['Publication_date'].dt.year.astype('Int64')
    ten_years_ago= datetime.today().year - 10

    fig3 = make_subplots(rows=1, cols=3, subplot_titles=["Array Drop Rate", "Sequencing Drop Rate", "mix Drop Rate"])

    # Subplot 1: Drop Rate by Account
    array_data = df_drop_rate[
        (df_drop_rate["Genotyping_type"] == "array") & 
        (df_drop_rate['year'] > ten_years_ago)
        ]

    fig3.add_trace(
        go.Box(
            y=array_data["Harm_drop_rate"],
            x=array_data["year"],
            name="Array Drop Rate",
            boxmean=True
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
    sequencing_data = df_drop_rate[
        (df_drop_rate["Genotyping_type"] == "sequencing") &
        (df_drop_rate['year'] > ten_years_ago)
        ]

    fig3.add_trace(
        go.Box(
            y=sequencing_data["Harm_drop_rate"],
            x=sequencing_data["year"], 
            name="Sequencing Drop Rate",
            boxmean=True
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
    mix_data = df_drop_rate[
        (df_drop_rate["Genotyping_type"] == "mix") & 
        (df_drop_rate['year'] > ten_years_ago)
        ]
    
    fig3.add_trace(
        go.Box(
            y=mix_data["Harm_drop_rate"],
            x=mix_data["year"], 
            name="Mix Drop Rate",
            boxmean=True
            ),
        row=1, col=3
    )

    fig3.update_yaxes(
    tickformat='.2%'
    )

    fig3.update_layout(
        title_text="Harmonisation Drop Rate Plots (Past 10 Years)", 
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
  
    return fig1, fig2, fig3, ""