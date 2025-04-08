# app.py
import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import requests
#import dash_extensions as de

# Initialize the Dash app with Bootstrap
app = dash.Dash(__name__, 
                external_stylesheets=[dbc.themes.BOOTSTRAP],
                use_pages=True)  # Enable pages
app.title = "Harmstatus Dashboard"

# Fetch the data from the FastAPI endpoint

def get_data():
    all_data = []
    page = 1  # Initial page number (adjust if necessary based on the API's pagination)
    
    while True:
        try:
            response = requests.get(f"https://harm-status-api.onrender.com/?page={page}")  # Include pagination in the URL if needed
            data = response.json()
            
            if not data:  # No more data, break the loop
                break
            
            all_data.extend(data)  # Accumulate the data from this page
            
            page += 1  # Move to the next page
            
        except requests.exceptions.RequestException:
            break  # Exit the loop if there's a request error

    return all_data


# Define the layout of the app
app.layout = dbc.Container([
    dcc.Store(id='shared-data', data=get_data()),

    dbc.NavbarSimple(
        brand="Harmstatus Dashboard",
        color="primary",
        dark=True,
        children=[
            dbc.NavItem(dcc.Link("Table", href="/", className="nav-link")),
            dbc.NavItem(dcc.Link("Summary Plot", href="/plot", className="nav-link")),
        ]
    ),
    dash.page_container  # This will display the current page content
], fluid=True)

if __name__ == "__main__":
    app.run(debug=True)