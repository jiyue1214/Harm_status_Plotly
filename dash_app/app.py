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
server = app.server
app.title = "Harmstatus Dashboard"

# Define the layout of the app
app.layout = dbc.Container([
    dcc.Store(id='shared-data'),
    dcc.Interval(id='trigger-load', interval=500, n_intervals=0, max_intervals=1),

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

# Callback to fetch the data
@app.callback(
    Output("shared-data", "data"),
    Input("trigger-load", "n_intervals"),
    prevent_initial_call="initial_duplicate"
)
def load_data(n):
    print("⚡ Callback triggered...")
    try:
        db_path = os.path.join(os.path.dirname(__file__), 'Data', 'Harm_sumstats_status.db')
        print("Looking for DB at:", db_path)
        print("Exists?", os.path.exists(db_path))
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM studies")
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        result = [dict(zip(columns, row)) for row in rows]
        print("Fetched rows:", len(result))

        conn.close()
        return result
    except sqlite3.DatabaseError as e:
        print(f"Error loading data: {e}")
        return []


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))  # Render provides PORT env
    app.run(host="0.0.0.0", port=port)