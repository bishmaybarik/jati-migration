"""
Conversion script to convert CSV and GeoJSON files to Parquet/GeoParquet format
This script prepares all data files needed for the migration dashboard

Run this script from the root directory of the repo:
python b/convert_to_parquet.py
"""

import pandas as pd
import geopandas as gpd
import os
from pathlib import Path

# Define source and destination paths
SOURCE_BASE = "/Users/bishmaybarik/Library/CloudStorage/Dropbox/cafral_work/shreya-projects/cphs-migrate"
DEST_DIR = "raw"

# Create raw directory if it doesn't exist
os.makedirs(DEST_DIR, exist_ok=True)

print("Starting data conversion...")
print("=" * 60)

# 1. Convert CSV files to Parquet
print("\n1. Converting CSV files to Parquet...")

csv_files = {
    'district_mapping.csv': 'district_mapping.parquet',
    'state_centroids.csv': 'state_centroids.parquet',
    'district_centroids.csv': 'district_centroids.parquet'
}

for csv_file, parquet_file in csv_files.items():
    source_path = f"{SOURCE_BASE}/e/{csv_file}"
    dest_path = f"{DEST_DIR}/{parquet_file}"

    print(f"   Converting {csv_file}...")
    df = pd.read_csv(source_path)
    df.to_parquet(dest_path, index=False)
    print(f"   ✓ Saved to {dest_path}")

# 2. Convert GeoJSON files to GeoParquet (with simplification)
print("\n2. Converting GeoJSON files to GeoParquet (with simplification)...")

geojson_files = {
    'state_boundaries.geojson': ('state_boundaries.parquet', 0.05),
    'district_boundaries.geojson': ('district_boundaries.parquet', 0.02)
}

for geojson_file, (parquet_file, tolerance) in geojson_files.items():
    source_path = f"{SOURCE_BASE}/e/{geojson_file}"
    dest_path = f"{DEST_DIR}/{parquet_file}"

    print(f"   Loading {geojson_file}...")
    gdf = gpd.read_file(source_path)

    print(f"   Simplifying geometry (tolerance={tolerance})...")
    gdf['geometry'] = gdf.geometry.simplify(tolerance=tolerance, preserve_topology=True)

    print(f"   Saving to {parquet_file}...")
    gdf.to_parquet(dest_path)
    print(f"   ✓ Saved to {dest_path}")

# 3. Copy migration.parquet
print("\n3. Copying migration data...")
source_migration = f"{SOURCE_BASE}/clean/migration.parquet"
dest_migration = f"{DEST_DIR}/migration_2024.parquet"

print(f"   Copying migration.parquet...")
df_migration = pd.read_parquet(source_migration)
df_migration.to_parquet(dest_migration, index=False)
print(f"   ✓ Saved to {dest_migration}")

print("\n" + "=" * 60)
print("✓ All conversions completed successfully!")
print(f"✓ All files saved to {DEST_DIR}/ directory")
print("=" * 60)
