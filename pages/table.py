# pages/table.py
import dash
from dash import html, dash_table, callback, Input, Output, State, dcc, ALL
import pandas as pd
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc
import re

# Register this file as a page
dash.register_page(__name__, path="/", title="Table View")

# Define the layout of the table page
layout = dmc.MantineProvider([
    html.H1("GWAS Catalog summary statistic harmonisation status"),
    
    # Container for filter dropdowns
    html.Div(id='filter-container', className='filter-container'),
    
    html.Div([
    # Flex container with space-between to push popover and download to the right
    html.Div([
        # Left-side buttons container
        html.Div([
            # Apply filters button
            dmc.Button(
                'Apply Filters', 
                id='apply-filters-button', 
                n_clicks=0,
                variant="outline",
                style={'marginRight': '10px'}
            ),
            
            # Clear filters button
            dmc.Button(
                'Clear Filters', 
                id='clear-filters-button', 
                n_clicks=0,
                variant="outline"
            )
        ], style={
            'display': 'flex',
            'alignItems': 'center'
        }),
        
        # Right-side container for popover and download
        html.Div([
            # Popover with column selector
            dmc.Popover(
                width=300,
                position="bottom",
                withArrow=True,
                shadow="md",
                children=[
                    dmc.PopoverTarget(
                        dmc.Button(
                            "Select columns to display", 
                            variant="outline",
                            style={'marginRight': '10px'}
                        )
                    ),
                    dmc.PopoverDropdown(
                        dmc.MultiSelect(
                            id="column-selector",
                            label="Select columns to display",
                            placeholder="Pick columns",
                            data=[],
                            comboboxProps={"withinPortal": False},
                        )
                    ),
                ],
            ),
            dmc.Button(
                "Update Table",
                id="update-table-button",
                n_clicks=0,
                variant="outline",
                style={'marginLeft': '10px'}
                ),
            
            # Download button
            dcc.Download(id='download-tsv-component'),
            dmc.Button(
                'Download TSV', 
                id='download-tsv-button', 
                n_clicks=0,
                variant="outline"
            )
        ], style={
            'display': 'flex',
            'alignItems': 'center'
            })
        ], style={
            'display': 'flex',  # Use flexbox 
            'justifyContent': 'space-between',  # Push right-side content to the right
            'alignItems': 'center',  # Vertically center the items
            'width': '100%'  # Full width
            })
        ], style={
            'width': '100%',  # Full width container
            'padding': '10px'  # Optional padding
            }),

    # Main data table
    dash_table.DataTable(
        id='harmonised-studies',
        columns=[],
        data=[],
        editable=False,
        filter_action="native",  # Keep native filtering enabled
        sort_action="native",
        sort_mode="multi",
        row_selectable="multi",
        row_deletable=False,
        selected_rows=[],
        selected_columns=[],
        page_action="native",
        page_current=0,
        page_size=10,
        style_table={'height': 500, 'overflowY': 'auto', 'overflowX': 'auto'},
        style_cell={
            'height': 'auto',
            # all three widths are needed
            'minWidth': '100px',
            'maxWidth': '200px',
            'whiteSpace': 'normal',
            'overflowWrap': 'break-word'
            },
        style_data={
        'color': 'black',
        'backgroundColor': 'white',
        'whiteSpace': 'normal',
        'height': 'auto',
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(220, 220, 220)',
                }
                ],
        style_header={
            'backgroundColor': 'rgb(210, 210, 210)',
            'color': 'black',
            'fontWeight': 'bold',
            'whiteSpace': 'normal',
            'height': 'auto',
            'textAlign': 'center'
            }
        ),
    
    html.Br(),
    dcc.Checklist(
        id='datatable-use-page-count',
        options=[
            {'label': 'Use page_count', 'value': 'True'}
        ],
        value=['True']
    ),
    'Page count: ',
    dcc.Input(
        id='datatable-page-count',
        type='number',
        min=1,
        max=29,
        value=20
    ),
    html.Div(id='datatable-interactivity-container'),
    
    # Store component to hold the data
    dcc.Store(id='table-data-store')
])

# Load data and update stores
@callback(
    Output('table-data-store', 'data'),
    Output('column-selector', 'data'),
    Output('column-selector', 'value'),  # Default: Select all columns
    Input('shared-data', 'data')
)
def load_data(data):
    if not data:
        return [], [], []

    df = pd.DataFrame(data)

    # Prepare the column options for the MultiSelect component
    column_options = [{"label": col, "value": col} for col in df.columns]
    
    # Return data, column options, and default selection (all columns)
    return data, column_options, df.columns.tolist() # Default: all selected

# load the table data
@callback(
    Output('harmonised-studies', 'columns'),
    Output('harmonised-studies', 'data'),
    Input('table-data-store', 'data'),
    prevent_initial_call=True  # Allow the callback to trigger on page load
)
def update_selected_table(data):
    if not data:
        raise PreventUpdate

    df = pd.DataFrame(data)

    initial_columns=["Study","PMID","Genotyping_type", 
                    "Effect_size_type","Raw_N_variants",
                    "Harm_status","Latest_harm_start_date",
                    "Harm_drop_rate","Liftover_drop_rate"]
    columns = [{"name": col, "id": col} for col in initial_columns]  # Only include selected columns
    table_data = df.to_dict('records')

    return columns, table_data

# Update the columns based on selection (hidden unwanted columns)
@callback(
    Output('harmonised-studies', 'hidden_columns'),
    Input('update-table-button', 'n_clicks'),
    State('table-data-store', 'data'),
    State('column-selector', 'value'),
    prevent_initial_call=True  # Allow the callback to trigger on page load
)
def update_table_columns(n_clicks, data, selected_columns):
    
    if not data:
        raise PreventUpdate

    df = pd.DataFrame(data)

    column_not_show=list(set(df.columns) - set(selected_columns))
    return column_not_show

# Create filter dropdowns for each column
@callback(
    Output('filter-container', 'children'),
    Input('table-data-store', 'data')
)
def create_filter_dropdowns(data):
    """
    Create dynamic filter dropdowns based on column characteristics
    """
    if not data:
        raise PreventUpdate
    
    df = pd.DataFrame(data)
    filter_elements = []
    
    # Define special handling for specific column types
    text_input_columns = ['PMID', 'First_author']
    comparison_columns = [
        'Raw_N_variants', 
        'Harm_drop_rate', 
        'Liftover_drop_rate'
    ]
    dropdown_columns = [
        'Effect_size_type',
        'Raw_genome_build',
        'Raw_coordinate_system',
        'Harm_status',
        'Harm_account', 
        'Harm_exitcode', 
        'Harm_failstep'
    ]
    
    # Dropdown columns (categorical selection)
    for col in dropdown_columns:
        unique_values = df[col].dropna().unique()
        
        # Only create dropdowns for columns with a reasonable number of unique values
        if len(unique_values) <= 20:  # Increased limit to 20
            filter_elements.append(
                html.Div([
                    html.Label(f"Filter by {col}:"),
                    dcc.Dropdown(
                        id={'type': 'filter-dropdown', 'column': col},
                        options=[{'label': str(val), 'value': str(val)} for val in sorted(unique_values)],
                        multi=True,
                        placeholder=f"Select {col} values"
                    )
                ], style={'width': '250px', 'display': 'inline-block', 'margin': '10px'})
            )

    # Text input columns (free text search)
    for col in text_input_columns:
        filter_elements.append(
            html.Div([
                dmc.TextInput(
                    label=f"Search in {col}:",
                    id={'type': 'text-filter', 'column': col},
                    placeholder=f'Search {col}',
                    style={'width': '250px'}
                )
            ], style={'display': 'inline-block', 'margin': '10px'})
        )

    # Comparison columns (numeric comparison)
    for col in comparison_columns:
        filter_elements.append(
            html.Div([
                html.Label(f"Filter {col}:"),
                html.Div([
                    dcc.Dropdown(
                        id={'type': 'comparison-operator', 'column': col},
                        options=[
                            {'label': '>', 'value': '>'},
                            {'label': '<', 'value': '<'},
                            {'label': '=', 'value': '=='}
                        ],
                        placeholder='Comparison',
                        style={'width': '100px', 'display': 'inline-block'}
                    ),
                    dcc.Input(
                        id={'type': 'comparison-value', 'column': col},
                        type='number',
                        placeholder='Value',
                        style={'width': '140px', 'display': 'inline-block', 'marginLeft': '10px'}
                    )
                ])
            ], style={'display': 'inline-block', 'margin': '10px'})
        )

    return filter_elements

# Apply filters from dropdowns to the table
@callback(
    Output('harmonised-studies', 'filter_query'),
    [
        Input('apply-filters-button', 'n_clicks'),
        # Dropdown filters
        State({'type': 'filter-dropdown', 'column': ALL}, 'value'),
        State({'type': 'filter-dropdown', 'column': ALL}, 'id'),
        # Text input filters
        State({'type': 'text-filter', 'column': ALL}, 'value'),
        State({'type': 'text-filter', 'column': ALL}, 'id'),
        # Comparison filters
        State({'type': 'comparison-operator', 'column': ALL}, 'value'),
        State({'type': 'comparison-value', 'column': ALL}, 'value'),
        State({'type': 'comparison-operator', 'column': ALL}, 'id')
    ],
    prevent_initial_call=True
)
def update_table_filters(
    n_clicks, 
    dropdown_values, dropdown_ids, 
    text_values, text_ids, 
    comparison_operators, comparison_values, comparison_op_ids
):
    if not n_clicks:
        raise PreventUpdate
    
    # Initialize filter conditions list
    filter_conditions = []
    
    # Handle dropdown filters
    for i, filter_val in enumerate(dropdown_values):
        if filter_val and len(filter_val) > 0:
            col_name = dropdown_ids[i]['column']
            # Build AND conditions for each selected value in this column
            value_conditions = [f'{{{col_name}}} eq "{val}"' for val in filter_val]
            column_condition = f"({' && '.join(value_conditions)})"
            print(column_condition)
            filter_conditions.append(column_condition)
    
    # Handle text search filters
    for i, text_val in enumerate(text_values):
        if text_val and text_val.strip():
            col_name = text_ids[i]['column']
            value_conditions = [f'{{{col_name}}} eq "{text_val}"']
            column_condition = f"({' && '.join(value_conditions)})"
            print(column_condition)
            filter_conditions.append(column_condition)
    
    # Handle numeric comparison filters
    for i, (operator, value) in enumerate(zip(comparison_operators, comparison_values)):
        if operator and value is not None:
            col_name = comparison_op_ids[i]['column']
            filter_conditions.append(f"{{{col_name}}} != NA")
            # Map comparison operators to filter query syntax
            op_map = {
                '>': 'gt',   # greater than
                '<': 'lt',   # less than
                '==': 'eq'   # equal to
            }
            
            if operator in op_map:
                value_conditions = [f'{{{col_name}}} {operator} "{value}"']
                column_condition = f"({' && '.join(value_conditions)})"
                print(column_condition)
                filter_conditions.append(column_condition)
    
    # Combine all conditions with AND
    if filter_conditions:
        return ' && '.join(filter_conditions)
    
    return ''

# Clear all filters
@callback(
    Output({'type': 'filter-dropdown', 'column': ALL}, 'value'),
    Output({'type': 'text-filter', 'column': ALL}, 'value'),
    Output({'type': 'comparison-operator', 'column': ALL}, 'value'),
    Output({'type': 'comparison-value', 'column': ALL}, 'value'),
    Output('harmonised-studies', 'filter_query', allow_duplicate=True),
    Input('clear-filters-button', 'n_clicks'),
    State({'type': 'filter-dropdown', 'column': ALL}, 'id'),
    State({'type': 'text-filter', 'column': ALL}, 'id'),
    State({'type': 'comparison-operator', 'column': ALL}, 'id'),
    State({'type': 'comparison-value', 'column': ALL}, 'id'),
    prevent_initial_call=True
)
def clear_filters(n_clicks, dropdown_filter_ids, text_filter_ids, comparison_operator_ids, comparison_value_ids):
    if not n_clicks:
        raise PreventUpdate

    # Return empty values for all dropdowns, text inputs, comparison operators, and comparison values
    return (
        [[] for _ in range(len(dropdown_filter_ids))],  # Reset dropdown values
        ['' for _ in range(len(text_filter_ids))],  # Reset text input values
        [None for _ in range(len(comparison_operator_ids))],  # Reset comparison operators
        [None for _ in range(len(comparison_value_ids))],  # Reset comparison values
        ''  # Reset filter query
    )

# Fix Download Button to Export Filtered Data
@callback(
    Output('download-tsv-component', 'data'),
    Input('download-tsv-button', 'n_clicks'),
    State('table-data-store', 'data'),
    State('harmonised-studies', 'filter_query'),
    State('harmonised-studies', 'hidden_columns'),
    prevent_initial_call=True
)
def download_tsv(n_clicks, stored_data, filter_query, hidden_columns):
    if not stored_data:
        raise PreventUpdate

    df = pd.DataFrame(stored_data)

    # Convert filter_query into actual filtering
    if filter_query:
        for condition in filter_query.split("&&"):
            match = re.search(r'\{([^\}]+)\} eq "([^"]+)"', condition)
            if match:
                column = match.group(1)
                value = match.group(2)
                df = df[df[column] == value]

    # Keep only the selected columns
    selected_columns=list(set(df.columns)-set(hidden_columns))
    df = df[selected_columns]

    # Generate TSV file
    return dict(
        content=df.to_csv(index=False, sep='\t'), 
        filename="GWAS_Catalog_harmstatus.tsv"
    )