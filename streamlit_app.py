"""
India Migration Patterns Dashboard - Streamlit Version
Identical functionality to the Dash version
"""

import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.graph_objects as go
import json
import numpy as np

# Page config
st.set_page_config(
    page_title="India Migration Patterns Dashboard",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main {
        background: linear-gradient(to bottom, #f7fafc 0%, #edf2f7 100%);
    }
    .stSelectbox {
        margin-bottom: 1rem;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.2rem;
    }
    .info-box {
        background: #f7fafc;
        padding: 20px;
        border-radius: 8px;
        border-left: 4px solid #5a67d8;
        margin-top: 20px;
    }
    h1 {
        color: white;
        background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%);
        padding: 32px 24px;
        margin: -5rem -5rem 2rem -5rem;
        border-radius: 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .subtitle {
        color: rgba(255, 255, 255, 0.9);
        font-size: 16px;
        font-weight: 300;
        margin-top: -10px;
    }
</style>
""", unsafe_allow_html=True)

# Cache data loading
@st.cache_data
def load_data():
    """Load all data from AWS S3"""
    print("Loading data from AWS S3...")

    migration_df = pd.read_parquet('https://jati-data.s3.ap-south-1.amazonaws.com/migration.parquet')
    district_mapping = pd.read_csv('https://jati-data.s3.ap-south-1.amazonaws.com/district_mapping.csv')
    state_centroids = pd.read_csv('https://jati-data.s3.ap-south-1.amazonaws.com/state_centroids.csv')
    district_centroids = pd.read_csv('https://jati-data.s3.ap-south-1.amazonaws.com/district_centroids.csv')

    # Load boundaries
    state_gdf = gpd.read_file('https://jati-data.s3.ap-south-1.amazonaws.com/state_boundaries.geojson')
    district_gdf = gpd.read_file('https://jati-data.s3.ap-south-1.amazonaws.com/district_boundaries.geojson')

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

    # Convert to string to avoid categorical issues
    migration_df['caste_category'] = migration_df['caste_category'].astype(str)
    migration_df['caste'] = migration_df['caste'].astype(str)
    migration_df['religion'] = migration_df['religion'].astype(str)
    migration_df['emigration_immigration_reason'] = migration_df['emigration_immigration_reason'].astype(str)

    return migration_df, state_gdf, district_gdf, state_centroids_dict, district_centroids_dict

# Load data
try:
    migration_df, state_gdf, district_gdf, state_centroids_dict, district_centroids_dict = load_data()
    data_loaded = True
except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    data_loaded = False

# Header
st.markdown("""
    <h1>🗺️ India Migration Patterns Dashboard
    <div class="subtitle">Interactive visualization of migration flows across states and districts</div>
    </h1>
""", unsafe_allow_html=True)

if data_loaded:
    # Sidebar filters
    st.sidebar.header("🎛️ Filters")

    # Migration Type
    migration_status = st.sidebar.selectbox(
        "Migration Type",
        options=['Emigrated', 'Immigrated'],
        format_func=lambda x: 'Emigration' if x == 'Emigrated' else 'Immigration'
    )

    # Analysis Level
    level_type = st.sidebar.selectbox(
        "Analysis Level",
        options=['state', 'district'],
        format_func=lambda x: 'State Level' if x == 'state' else 'District Level'
    )

    # Breakdown Type
    breakdown_type = st.sidebar.selectbox(
        "Breakdown By",
        options=['overall', 'caste_category', 'religion'],
        format_func=lambda x: {'overall': 'Overall', 'caste_category': 'Caste Category', 'religion': 'Religion'}[x]
    )

    # Get filtered data for breakdown options
    df_for_filters = migration_df[migration_df['mem_status'] == migration_status].copy()

    # Breakdown Value (conditional)
    breakdown_value = None
    if breakdown_type != 'overall':
        if breakdown_type == 'caste_category':
            available_values = sorted([x for x in df_for_filters['caste_category'].unique() if x and x != 'nan'])
        elif breakdown_type == 'religion':
            available_values = sorted([x for x in df_for_filters['religion'].unique() if x and x != 'nan'])
        else:
            available_values = []

        breakdown_value = st.sidebar.selectbox(
            "Select Value",
            options=[None] + available_values,
            format_func=lambda x: 'All' if x is None else x
        )

    # Caste Filter (only show when caste category is selected)
    caste_filter = None
    if breakdown_type == 'caste_category':
        df_for_caste = df_for_filters.copy()
        if breakdown_value:
            df_for_caste = df_for_caste[df_for_caste['caste_category'] == breakdown_value]

        available_castes = sorted([x for x in df_for_caste['caste'].unique() if x and x != 'nan'])
        caste_filter = st.sidebar.selectbox(
            "Specific Caste (Jati)",
            options=[None] + available_castes,
            format_func=lambda x: 'All Castes' if x is None else x
        )

    # Migration Reason Filter
    df_for_reason = df_for_filters.copy()
    if breakdown_type != 'overall' and breakdown_value:
        if breakdown_type == 'caste_category':
            df_for_reason = df_for_reason[df_for_reason['caste_category'] == breakdown_value]
        elif breakdown_type == 'religion':
            df_for_reason = df_for_reason[df_for_reason['religion'] == breakdown_value]

    if caste_filter:
        df_for_reason = df_for_reason[df_for_reason['caste'] == caste_filter]

    available_reasons = sorted([x for x in df_for_reason['emigration_immigration_reason'].unique() if x and x != 'nan'])
    migration_reason = st.sidebar.selectbox(
        "Migration Reason",
        options=[None] + available_reasons,
        format_func=lambda x: 'All Reasons' if x is None else x
    )

    # Process data based on filters
    df = migration_df[migration_df['mem_status'] == migration_status].copy()

    # Define origin and destination
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

    # Apply filters
    if breakdown_type != 'overall' and breakdown_value:
        if breakdown_type == 'caste_category':
            df = df[df['caste_category'] == breakdown_value]
        elif breakdown_type == 'religion':
            df = df[df['religion'] == breakdown_value]

    if caste_filter:
        df = df[df['caste'] == caste_filter]

    if migration_reason:
        df = df[df['emigration_immigration_reason'] == migration_reason]

    # Aggregate data
    if level_type == 'state':
        agg_df = df.groupby(['origin', 'destination'], observed=True)['unique_id'].nunique().reset_index()
        agg_df.columns = ['origin', 'destination', 'count']
        centroids_dict = state_centroids_dict
        geojson = json.loads(state_gdf.to_json())
    else:
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

    # Add migration flow lines
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
                if origin_coords == dest_coords:
                    continue

                width = max(0.5, (np.log1p(row['count']) / np.log1p(max_count)) * 8)

                fig.add_trace(go.Scattergeo(
                    lon=[origin_coords[1], dest_coords[1]],
                    lat=[origin_coords[0], dest_coords[0]],
                    mode='lines',
                    line=dict(width=width, color='#FF6B6B'),
                    hoverinfo='skip',
                    showlegend=False,
                    opacity=0.5
                ))

                arrow_lat = origin_coords[0] + 0.8 * (dest_coords[0] - origin_coords[0])
                arrow_lon = origin_coords[1] + 0.8 * (dest_coords[1] - origin_coords[1])
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

    # Add interactive points
    if len(agg_df) > 0:
        if level_type == 'state':
            dest_summary = agg_df.groupby('destination').apply(
                lambda x: pd.Series({
                    'total_migrants': x['count'].sum(),
                    'origins': '<br>'.join([f"From {row['origin']}: {row['count']:,}" for _, row in x.iterrows()]),
                    'destination': x.name,
                    'lat': centroids_dict.get(x.name, [0, 0])[0],
                    'lon': centroids_dict.get(x.name, [0, 0])[1]
                }), include_groups=False
            ).reset_index(drop=True)

            origin_summary = agg_df.groupby('origin').apply(
                lambda x: pd.Series({
                    'total_migrants': x['count'].sum(),
                    'destinations': '<br>'.join([f"To {row['destination']}: {row['count']:,}" for _, row in x.iterrows()]),
                    'origin': x.name,
                    'lat': centroids_dict.get(x.name, [0, 0])[0],
                    'lon': centroids_dict.get(x.name, [0, 0])[1]
                }), include_groups=False
            ).reset_index(drop=True)

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

    # Display map
    st.plotly_chart(fig, use_container_width=True)

    # Info section
    st.markdown("---")
    st.markdown("### 📊 Dashboard Information")

    total_migrants = agg_df['count'].sum()
    num_flows = len(agg_df)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Migrants", f"{total_migrants:,}")
    with col2:
        st.metric("Migration Flows", f"{num_flows:,}")
    with col3:
        st.metric("Analysis Level", level_type.title())

    # Filters applied
    filters_applied = []
    if breakdown_type != 'overall' and breakdown_value:
        filters_applied.append(f"{breakdown_type.replace('_', ' ').title()}: {breakdown_value}")
    if caste_filter:
        filters_applied.append(f"Caste: {caste_filter}")
    if migration_reason:
        filters_applied.append(f"Reason: {migration_reason}")

    if filters_applied:
        st.info(f"**Active Filters:** {', '.join(filters_applied)}")

    st.markdown("*Hover over blue dots on the map to see migration inflows and outflows for each location.*")

    # Data sources
    st.markdown("""
    <div class="info-box">
        <p><strong>Data Source:</strong> Migration patterns are based on reported responses from Consumer Pyramids Household Survey (CPHS) members.
        The data covers waves from September-December 2020 through September-December 2024.
        During each survey wave, respondents were asked about emigration or immigration status,
        from which origin and destination states and districts have been identified.</p>

        <p><strong>Geographic Boundaries:</strong> Shapefiles sourced from Asher, S., Lunt, T., Matsuura, R., & Novosad, P. (2021).
        Development research at high geographic resolution: an analysis of night-lights, firms, and poverty in India using the SHRUG open data platform.
        <em>The World Bank Economic Review, 35</em>(4). Oxford University Press.</p>

        <p style="text-align: center; color: #a0aec0; margin-top: 20px;">© Created by Bishmay Barik</p>
    </div>
    """, unsafe_allow_html=True)
