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

def get_data():
    try:
        # Connect to the SQLite database (adjust the path as needed)
        db_path = os.path.join(os.path.dirname(__file__), 'Data', 'Harm_sumstats_status.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Query to fetch all data from the 'studies' table
        cursor.execute("SELECT * FROM studies")
        rows = cursor.fetchall()

        # Optionally, you can convert rows into a list of dictionaries or a suitable format
        # Example: converting rows to a list of dictionaries with column names
        columns = [column[0] for column in cursor.description]  # Fetch column names
        result = [dict(zip(columns, row)) for row in rows]

        # Close the connection
        conn.close()

        return result
    except sqlite3.DatabaseError:
        return []


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

# Start data fetching in the background when the app runs
# Callback to fetch the data

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))  # 8050 is just a default fallback
    app.run_server(debug=True, host="0.0.0.0", port=port)