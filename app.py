"""
Fast Interactive Migration Dashboard using Plotly Dash
Run with: python app.py
Then open http://localhost:8050 in your browser
"""

import pandas as pd
import geopandas as gpd
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import json
import numpy as np

# Load data
print("Loading data...")
migration_df = pd.read_parquet('https://jati-data.s3.ap-south-1.amazonaws.com/migration_2023_2024.parquet')
district_mapping = pd.read_parquet('raw/district_mapping.parquet')
state_centroids = pd.read_parquet('raw/state_centroids.parquet')
district_centroids = pd.read_parquet('raw/district_centroids.parquet')

# Load boundaries
state_gdf = gpd.read_parquet('raw/state_boundaries.parquet')
district_gdf = gpd.read_parquet('raw/district_boundaries.parquet')

# Simplify for faster rendering
state_gdf['geometry'] = state_gdf.simplify(tolerance=0.05, preserve_topology=True)
district_gdf['geometry'] = district_gdf.simplify(tolerance=0.02, preserve_topology=True)

# Merge migration data with district mapping
migration_df = migration_df.merge(
    district_mapping[['state_code', 'district', 'matched_district']],
    on=['state_code', 'district'],
    how='left'
)

# Filter to migration records only
migration_df = migration_df[migration_df['mem_status'].isin(['Emigrated', 'Immigrated'])].copy()

# Create unique ID
migration_df['unique_id'] = migration_df['hh_id'].astype(str) + '_' + migration_df['mem_id'].astype(str)

# Create centroids lookup
state_centroids_dict = dict(zip(state_centroids['state_name'],
                                 zip(state_centroids['lat'], state_centroids['lon'])))
district_centroids_dict = dict(zip(
    district_centroids['district_name'] + '|' + district_centroids['state_name'],
    zip(district_centroids['lat'], district_centroids['lon'])
))

# Get unique filter values (convert to string to avoid categorical issues)
migration_df['caste_category'] = migration_df['caste_category'].astype(str)
migration_df['caste'] = migration_df['caste'].astype(str)
migration_df['religion'] = migration_df['religion'].astype(str)
migration_df['emigration_immigration_reason'] = migration_df['emigration_immigration_reason'].astype(str)

caste_categories = sorted([x for x in migration_df['caste_category'].unique() if x and x != 'nan'])
castes = sorted([x for x in migration_df['caste'].unique() if x and x != 'nan'])
religions = sorted([x for x in migration_df['religion'].unique() if x and x != 'nan'])
reasons = sorted([x for x in migration_df['emigration_immigration_reason'].unique() if x and x != 'nan'])

print("Data loaded successfully!")

# Initialize Dash app
app = Dash(__name__)
server = app.server  # Expose the server for deployment

app.layout = html.Div([
    # Header
    html.Div([
        html.Div([
            html.H1("🗺️ India Migration Patterns Dashboard",
                    style={
                        'color': 'white',
                        'margin': '0',
                        'fontSize': '32px',
                        'fontWeight': '600',
                        'letterSpacing': '-0.5px'
                    }),
            html.P("Interactive visualization of migration flows across states and districts",
                   style={
                       'color': 'rgba(255, 255, 255, 0.9)',
                       'margin': '8px 0 0 0',
                       'fontSize': '16px',
                       'fontWeight': '300'
                   })
        ], style={'maxWidth': '1400px', 'margin': '0 auto'})
    ], style={
        'background': 'linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%)',
        'padding': '32px 24px',
        'marginBottom': '0',
        'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)'
    }),

    # Filters Container
    html.Div([
        html.Div([
            html.Div([
                html.Label('Migration Type', style={
                    'fontWeight': '600',
                    'marginBottom': '8px',
                    'display': 'block',
                    'color': '#2d3748',
                    'fontSize': '14px'
                }),
                dcc.Dropdown(
                    id='migration-status',
                    options=[
                        {'label': 'Emigration', 'value': 'Emigrated'},
                        {'label': 'Immigration', 'value': 'Immigrated'}
                    ],
                    value='Emigrated',
                    clearable=False,
                    className='custom-dropdown'
                )
            ], style={'flex': '1', 'minWidth': '200px'}),

            html.Div([
                html.Label('Analysis Level', style={
                    'fontWeight': '600',
                    'marginBottom': '8px',
                    'display': 'block',
                    'color': '#2d3748',
                    'fontSize': '14px'
                }),
                dcc.Dropdown(
                    id='level-type',
                    options=[
                        {'label': 'State Level', 'value': 'state'},
                        {'label': 'District Level', 'value': 'district'}
                    ],
                    value='state',
                    clearable=False,
                    className='custom-dropdown'
                )
            ], style={'flex': '1', 'minWidth': '200px'}),

            html.Div([
                html.Label('Breakdown By', style={
                    'fontWeight': '600',
                    'marginBottom': '8px',
                    'display': 'block',
                    'color': '#2d3748',
                    'fontSize': '14px'
                }),
                dcc.Dropdown(
                    id='breakdown-type',
                    options=[
                        {'label': 'Overall', 'value': 'overall'},
                        {'label': 'Caste Category', 'value': 'caste_category'},
                        {'label': 'Religion', 'value': 'religion'}
                    ],
                    value='overall',
                    clearable=False,
                    className='custom-dropdown'
                )
            ], style={'flex': '1', 'minWidth': '200px'}),

            html.Div([
                html.Label('Select Value', style={
                    'fontWeight': '600',
                    'marginBottom': '8px',
                    'display': 'block',
                    'color': '#2d3748',
                    'fontSize': '14px'
                }),
                dcc.Dropdown(
                    id='breakdown-value',
                    options=[],
                    value=None,
                    placeholder='All',
                    className='custom-dropdown'
                )
            ], style={'flex': '1', 'minWidth': '200px'}, id='breakdown-value-div'),

            html.Div([
                html.Label('Specific Caste (Jati)', style={
                    'fontWeight': '600',
                    'marginBottom': '8px',
                    'display': 'block',
                    'color': '#2d3748',
                    'fontSize': '14px'
                }),
                dcc.Dropdown(
                    id='caste-filter',
                    options=[],
                    value=None,
                    placeholder='All Castes',
                    clearable=True,
                    className='custom-dropdown'
                )
            ], style={'flex': '1', 'minWidth': '200px'}, id='caste-filter-div'),

            html.Div([
                html.Label('Migration Reason', style={
                    'fontWeight': '600',
                    'marginBottom': '8px',
                    'display': 'block',
                    'color': '#2d3748',
                    'fontSize': '14px'
                }),
                dcc.Dropdown(
                    id='migration-reason',
                    options=[],
                    value=None,
                    placeholder='All Reasons',
                    clearable=True,
                    optionHeight=60,
                    className='custom-dropdown'
                )
            ], style={'flex': '1', 'minWidth': '280px'})

        ], style={
            'display': 'flex',
            'gap': '20px',
            'flexWrap': 'wrap'
        })
    ], style={
        'background': 'white',
        'padding': '28px',
        'marginBottom': '24px',
        'borderRadius': '12px',
        'boxShadow': '0 2px 8px rgba(0, 0, 0, 0.08)',
        'maxWidth': '1400px',
        'margin': '24px auto'
    }),

    # Map Container
    html.Div([
        dcc.Loading(
            id='loading',
            type='default',
            children=[
                dcc.Graph(id='migration-map', style={'height': '700px'})
            ]
        )
    ], style={
        'background': 'white',
        'borderRadius': '12px',
        'boxShadow': '0 2px 8px rgba(0, 0, 0, 0.08)',
        'overflow': 'hidden',
        'maxWidth': '1400px',
        'margin': '0 auto 24px auto'
    }),

    # Info Section
    html.Div(id='info-text', style={
        'padding': '28px',
        'background': 'white',
        'borderRadius': '12px',
        'boxShadow': '0 2px 8px rgba(0, 0, 0, 0.08)',
        'maxWidth': '1400px',
        'margin': '0 auto 24px auto'
    })
], style={
    'fontFamily': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    'background': 'linear-gradient(to bottom, #f7fafc 0%, #edf2f7 100%)',
    'padding': '0 0 40px 0',
    'margin': '0',
    'minHeight': '100vh'
})

# Callback to update breakdown values based on migration status
@app.callback(
    [Output('breakdown-value', 'options'),
     Output('breakdown-value', 'value'),
     Output('breakdown-value-div', 'style')],
    [Input('breakdown-type', 'value'),
     Input('migration-status', 'value')]
)
def update_breakdown_options(breakdown_type, migration_status):
    if breakdown_type == 'overall':
        return [], None, {'flex': '1', 'minWidth': '200px', 'display': 'none'}

    # Filter data based on migration status
    df = migration_df[migration_df['mem_status'] == migration_status].copy()

    # Get available values for the selected breakdown type
    if breakdown_type == 'caste_category':
        available_values = sorted([x for x in df['caste_category'].unique() if x and x != 'nan'])
    elif breakdown_type == 'religion':
        available_values = sorted([x for x in df['religion'].unique() if x and x != 'nan'])
    else:
        available_values = []

    options = [{'label': x, 'value': x} for x in available_values]
    return options, None, {'flex': '1', 'minWidth': '200px', 'display': 'block'}

# Callback to update caste filter options based on caste category selection
@app.callback(
    [Output('caste-filter', 'options'),
     Output('caste-filter', 'value'),
     Output('caste-filter-div', 'style')],
    [Input('breakdown-type', 'value'),
     Input('breakdown-value', 'value'),
     Input('migration-status', 'value')]
)
def update_caste_options(breakdown_type, breakdown_value, migration_status):
    # Only show caste filter when caste category is selected
    if breakdown_type != 'caste_category':
        return [], None, {'flex': '1', 'minWidth': '200px', 'display': 'none'}

    # Filter data based on migration status
    df = migration_df[migration_df['mem_status'] == migration_status].copy()

    # If a specific caste category is selected, filter castes for that category
    if breakdown_value:
        df = df[df['caste_category'] == breakdown_value]

    # Get available castes
    available_castes = sorted([x for x in df['caste'].unique() if x and x != 'nan'])
    options = [{'label': x, 'value': x} for x in available_castes]

    return options, None, {'flex': '1', 'minWidth': '200px', 'display': 'block'}

# Callback to update migration reason options based on previous filters
@app.callback(
    [Output('migration-reason', 'options'),
     Output('migration-reason', 'value')],
    [Input('migration-status', 'value'),
     Input('breakdown-type', 'value'),
     Input('breakdown-value', 'value'),
     Input('caste-filter', 'value')]
)
def update_reason_options(migration_status, breakdown_type, breakdown_value, caste_filter):
    # Filter data based on migration status
    df = migration_df[migration_df['mem_status'] == migration_status].copy()

    # Apply breakdown filter if selected
    if breakdown_type != 'overall' and breakdown_value:
        if breakdown_type == 'caste_category':
            df = df[df['caste_category'] == breakdown_value]
        elif breakdown_type == 'religion':
            df = df[df['religion'] == breakdown_value]

    # Apply caste filter if selected
    if caste_filter:
        df = df[df['caste'] == caste_filter]

    # Get available migration reasons
    available_reasons = sorted([x for x in df['emigration_immigration_reason'].unique() if x and x != 'nan'])
    options = [{'label': x, 'value': x} for x in available_reasons]

    return options, None

# Main callback to update map
@app.callback(
    [Output('migration-map', 'figure'),
     Output('info-text', 'children')],
    [Input('migration-status', 'value'),
     Input('level-type', 'value'),
     Input('breakdown-type', 'value'),
     Input('breakdown-value', 'value'),
     Input('caste-filter', 'value'),
     Input('migration-reason', 'value')]
)
def update_map(migration_status, level_type, breakdown_type, breakdown_value, caste_filter, migration_reason):
    # Filter data
    df = migration_df[migration_df['mem_status'] == migration_status].copy()

    # Define origin and destination FIRST
    if migration_status == 'Emigrated':
        df['origin'] = df['state']
        df['destination'] = df['emigrated_immigrated_state']
        df['origin_district'] = df['matched_district']
        df['destination_district'] = df['emigrated_immigrated_district']
    else:
        df['origin'] = df['emigrated_immigrated_state']
        df['destination'] = df['state']
        df['origin_district'] = df['emigrated_immigrated_district']
        df['destination_district'] = df['matched_district']

    # Apply breakdown filter AFTER defining origin/destination
    if breakdown_type != 'overall' and breakdown_value:
        if breakdown_type == 'caste_category':
            df = df[df['caste_category'] == breakdown_value]
        elif breakdown_type == 'religion':
            df = df[df['religion'] == breakdown_value]

    # Apply caste filter if selected
    if caste_filter:
        df = df[df['caste'] == caste_filter]

    # Apply migration reason filter (independent of breakdown)
    if migration_reason:
        df = df[df['emigration_immigration_reason'] == migration_reason]

    # Aggregate unique individuals
    if level_type == 'state':
        agg_df = df.groupby(['origin', 'destination'], observed=True)['unique_id'].nunique().reset_index()
        agg_df.columns = ['origin', 'destination', 'count']
        centroids_dict = state_centroids_dict
        geojson = json.loads(state_gdf.to_json())
    else:
        # For district level, need to track both district and state
        agg_df = df.groupby(['origin_district', 'destination_district', 'origin', 'destination'], observed=True)['unique_id'].nunique().reset_index()
        agg_df.columns = ['origin', 'destination', 'origin_state', 'destination_state', 'count']
        centroids_dict = district_centroids_dict
        geojson = json.loads(district_gdf.to_json())

    # Create figure
    fig = go.Figure()

    # Add boundaries
    for feature in geojson['features']:
        if feature['geometry']['type'] == 'Polygon':
            coords = feature['geometry']['coordinates'][0]
            lons, lats = zip(*coords)
            fig.add_trace(go.Scattergeo(
                lon=lons,
                lat=lats,
                mode='lines',
                line=dict(width=1, color='#95a5a6' if level_type == 'district' else '#667eea'),
                hoverinfo='skip',
                showlegend=False
            ))
        elif feature['geometry']['type'] == 'MultiPolygon':
            for polygon in feature['geometry']['coordinates']:
                coords = polygon[0]
                lons, lats = zip(*coords)
                fig.add_trace(go.Scattergeo(
                    lon=lons,
                    lat=lats,
                    mode='lines',
                    line=dict(width=1, color='#95a5a6' if level_type == 'district' else '#667eea'),
                    hoverinfo='skip',
                    showlegend=False
                ))

    # Add migration flow lines with arrow indicators
    if len(agg_df) > 0:
        max_count = agg_df['count'].max()

        for _, row in agg_df.iterrows():
            if level_type == 'state':
                origin_coords = centroids_dict.get(row['origin'])
                dest_coords = centroids_dict.get(row['destination'])
            else:
                origin_key = f"{row['origin']}|{row['origin_state']}"
                dest_key = f"{row['destination']}|{row['destination_state']}"
                origin_coords = centroids_dict.get(origin_key)
                dest_coords = centroids_dict.get(dest_key)

            if origin_coords and dest_coords and row['count'] > 0:
                # Skip self-loops
                if origin_coords == dest_coords:
                    continue

                # Calculate line width (logarithmic scale)
                width = max(0.5, (np.log1p(row['count']) / np.log1p(max_count)) * 8)

                # Add flow line
                fig.add_trace(go.Scattergeo(
                    lon=[origin_coords[1], dest_coords[1]],
                    lat=[origin_coords[0], dest_coords[0]],
                    mode='lines',
                    line=dict(width=width, color='#FF6B6B'),
                    hoverinfo='skip',
                    showlegend=False,
                    opacity=0.5
                ))

                # Add small arrow marker near the destination to show direction
                # Calculate position 80% along the line for arrow placement
                arrow_lat = origin_coords[0] + 0.8 * (dest_coords[0] - origin_coords[0])
                arrow_lon = origin_coords[1] + 0.8 * (dest_coords[1] - origin_coords[1])

                # Calculate arrow size based on line width
                arrow_size = max(4, min(width * 1.5, 12))

                fig.add_trace(go.Scattergeo(
                    lon=[arrow_lon],
                    lat=[arrow_lat],
                    mode='markers',
                    marker=dict(
                        size=arrow_size,
                        color='#FF6B6B',
                        symbol='triangle-up',
                        angle=np.degrees(np.arctan2(dest_coords[1] - origin_coords[1],
                                                    dest_coords[0] - origin_coords[0]))
                    ),
                    hoverinfo='skip',
                    showlegend=False,
                    opacity=0.7
                ))

    # Add interactive points showing both origins and destinations
    if len(agg_df) > 0:
        if level_type == 'state':
            # Group by destination to show all origins (inflows/sources)
            dest_summary = agg_df.groupby('destination').apply(
                lambda x: pd.Series({
                    'total_migrants': x['count'].sum(),
                    'origins': '<br>'.join([f"From {row['origin']}: {row['count']:,}" for _, row in x.iterrows()]),
                    'destination': x.name,
                    'lat': centroids_dict.get(x.name, [0, 0])[0],
                    'lon': centroids_dict.get(x.name, [0, 0])[1]
                }), include_groups=False
            ).reset_index(drop=True)

            # Group by origin to show all destinations (outflows)
            origin_summary = agg_df.groupby('origin').apply(
                lambda x: pd.Series({
                    'total_migrants': x['count'].sum(),
                    'destinations': '<br>'.join([f"To {row['destination']}: {row['count']:,}" for _, row in x.iterrows()]),
                    'origin': x.name,
                    'lat': centroids_dict.get(x.name, [0, 0])[0],
                    'lon': centroids_dict.get(x.name, [0, 0])[1]
                }), include_groups=False
            ).reset_index(drop=True)

            # Combine hover info - show both From and To information
            combined_hover = []
            for place in state_centroids_dict.keys():
                dest_info = dest_summary[dest_summary['destination'] == place]
                origin_info = origin_summary[origin_summary['origin'] == place]

                if not dest_info.empty or not origin_info.empty:
                    hover_text = f"<b>{place}</b><br>"

                    if not dest_info.empty:
                        hover_text += f"<br><b>Inflows:</b> {dest_info.iloc[0]['total_migrants']:,} migrants<br>{dest_info.iloc[0]['origins']}"

                    if not origin_info.empty:
                        if not dest_info.empty:
                            hover_text += "<br>"
                        hover_text += f"<br><b>Outflows:</b> {origin_info.iloc[0]['total_migrants']:,} migrants<br>{origin_info.iloc[0]['destinations']}"

                    combined_hover.append({
                        'place': place,
                        'lat': centroids_dict.get(place, [0, 0])[0],
                        'lon': centroids_dict.get(place, [0, 0])[1],
                        'text': hover_text
                    })

            if combined_hover:
                combined_df = pd.DataFrame(combined_hover)
                fig.add_trace(go.Scattergeo(
                    lon=combined_df['lon'],
                    lat=combined_df['lat'],
                    mode='markers',
                    marker=dict(size=10, color='#667eea', line=dict(width=2, color='white')),
                    text=combined_df['text'].tolist(),
                    hoverinfo='text',
                    showlegend=False,
                    name='Migration Points'
                ))
        else:
            # District level - more subtle dots
            dest_summary = agg_df.groupby(['destination', 'destination_state']).apply(
                lambda x: pd.Series({
                    'total_migrants': x['count'].sum(),
                    'origins': '<br>'.join([f"From {row['origin']} ({row['origin_state']}): {row['count']:,}"
                                           for _, row in x.iterrows()]),
                    'destination': x.name[0],
                    'destination_state': x.name[1],
                    'lat': centroids_dict.get(f"{x.name[0]}|{x.name[1]}", [0, 0])[0],
                    'lon': centroids_dict.get(f"{x.name[0]}|{x.name[1]}", [0, 0])[1]
                }), include_groups=False
            ).reset_index(drop=True)

            origin_summary = agg_df.groupby(['origin', 'origin_state']).apply(
                lambda x: pd.Series({
                    'total_migrants': x['count'].sum(),
                    'destinations': '<br>'.join([f"To {row['destination']} ({row['destination_state']}): {row['count']:,}"
                                                for _, row in x.iterrows()]),
                    'origin': x.name[0],
                    'origin_state': x.name[1],
                    'lat': centroids_dict.get(f"{x.name[0]}|{x.name[1]}", [0, 0])[0],
                    'lon': centroids_dict.get(f"{x.name[0]}|{x.name[1]}", [0, 0])[1]
                }), include_groups=False
            ).reset_index(drop=True)

            # Combine hover info for districts
            combined_hover = []
            for key in district_centroids_dict.keys():
                parts = key.split('|')
                if len(parts) == 2:
                    district, state = parts
                    dest_info = dest_summary[(dest_summary['destination'] == district) &
                                            (dest_summary['destination_state'] == state)]
                    origin_info = origin_summary[(origin_summary['origin'] == district) &
                                                 (origin_summary['origin_state'] == state)]

                    if not dest_info.empty or not origin_info.empty:
                        hover_text = f"<b>{district}</b> ({state})<br>"

                        if not dest_info.empty:
                            hover_text += f"<br><b>Inflows:</b> {dest_info.iloc[0]['total_migrants']:,} migrants<br>{dest_info.iloc[0]['origins']}"

                        if not origin_info.empty:
                            if not dest_info.empty:
                                hover_text += "<br>"
                            hover_text += f"<br><b>Outflows:</b> {origin_info.iloc[0]['total_migrants']:,} migrants<br>{origin_info.iloc[0]['destinations']}"

                        combined_hover.append({
                            'place': f"{district} ({state})",
                            'lat': district_centroids_dict[key][0],
                            'lon': district_centroids_dict[key][1],
                            'text': hover_text
                        })

            if combined_hover:
                combined_df = pd.DataFrame(combined_hover)
                fig.add_trace(go.Scattergeo(
                    lon=combined_df['lon'],
                    lat=combined_df['lat'],
                    mode='markers',
                    marker=dict(size=4, color='#667eea', opacity=0.6, line=dict(width=0.5, color='white')),
                    text=combined_df['text'].tolist(),
                    hoverinfo='text',
                    showlegend=False,
                    name='Migration Points'
                ))

    # Update layout
    fig.update_geos(
        scope='asia',
        center=dict(lat=23.5, lon=80.0),
        projection_scale=4,
        showcountries=False,
        showland=True,
        landcolor='#E8F4F8',
        showlakes=False,
        fitbounds='locations'
    )

    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        height=700,
        geo=dict(bgcolor='#f5f7fa'),
        hoverlabel=dict(
            bgcolor='white',
            font_size=13,
            font_family='Segoe UI'
        )
    )

    # Info text
    total_migrants = agg_df['count'].sum()
    num_flows = len(agg_df)
    info = f"Showing {migration_status.lower()} patterns at {level_type} level. "
    info += f"Total unique migrants: {total_migrants:,} across {num_flows:,} migration flows. "

    filters_applied = []
    if breakdown_type != 'overall' and breakdown_value:
        filters_applied.append(f"{breakdown_type.replace('_', ' ')}: {breakdown_value}")
    if caste_filter:
        filters_applied.append(f"Caste: {caste_filter}")
    if migration_reason:
        filters_applied.append(f"Reason: {migration_reason}")

    if filters_applied:
        info += f"Filters: {', '.join(filters_applied)}"

    return fig, html.Div([
        html.H3("Dashboard Information", style={
            'color': '#2d3748',
            'marginBottom': '16px',
            'fontSize': '20px',
            'fontWeight': '600',
            'borderBottom': '2px solid #5a67d8',
            'paddingBottom': '8px',
            'display': 'inline-block'
        }),
        html.P(info, style={
            'fontSize': '15px',
            'color': '#4a5568',
            'lineHeight': '1.6',
            'marginTop': '16px'
        }),
        html.P(f"Hover over points (blue dots) to see migration inflows and outflows for each location.",
               style={
                   'marginTop': '12px',
                   'fontSize': '14px',
                   'color': '#718096',
                   'fontStyle': 'italic'
               }),
        html.Div([
            html.Div([
                html.P([
                    html.Strong("Data Source: ", style={'color': '#2d3748'}),
                    html.Span("Migration patterns are based on reported responses from Consumer Pyramids Household Survey (CPHS) members. "
                    "The data covers waves from January 2023 through December 2024. "
                    "During each survey wave, respondents were asked about emigration or immigration status, "
                    "from which origin and destination states and districts have been identified.",
                    style={'color': '#4a5568'})
                ], style={'fontSize': '14px', 'lineHeight': '1.7', 'marginBottom': '12px'}),
                html.P([
                    html.Strong("Geographic Boundaries: ", style={'color': '#2d3748'}),
                    html.Span("Shapefiles sourced from Asher, S., Lunt, T., Matsuura, R., & Novosad, P. (2021). "
                    "Development research at high geographic resolution: an analysis of night-lights, firms, and poverty in India using the SHRUG open data platform. ",
                    style={'color': '#4a5568'}),
                    html.Em("The World Bank Economic Review, 35", style={'color': '#4a5568'}),
                    html.Span("(4). Oxford University Press.", style={'color': '#4a5568'})
                ], style={'fontSize': '14px', 'lineHeight': '1.7'})
            ], style={
                'background': '#f7fafc',
                'padding': '20px',
                'borderRadius': '8px',
                'marginTop': '20px',
                'borderLeft': '4px solid #5a67d8'
            }),
            html.P("© Created by Bishmay Barik",
                   style={
                       'fontSize': '13px',
                       'color': '#a0aec0',
                       'marginTop': '20px',
                       'textAlign': 'center',
                       'fontWeight': '300'
                   })
        ])
    ])

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Starting Migration Dashboard...")
    print("📍 Open http://localhost:8050 in your browser")
    print("="*60 + "\n")
    app.run_server(debug=True, port=8050)
