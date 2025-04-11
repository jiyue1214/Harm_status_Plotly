# app.py
import os,sys
import dash
from dash import dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import sqlite3

# Initialize the Dash app with Bootstrap
app = dash.Dash(__name__, 
                external_stylesheets=[dbc.themes.BOOTSTRAP],
                use_pages=True)  # Enable pages
app.title = "Harmstatus Dashboard"

# Define the layout of the app
app.layout = dbc.Container([
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
    #port = int(os.environ.get("PORT", 8050))  # Render provides PORT env
    #app.run(host="0.0.0.0", port=port, debug=True)
    app.run(debug=True)