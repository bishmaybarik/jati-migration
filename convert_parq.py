#!/usr/bin/env python3
"""
Convert CSV and GeoJSON files to Parquet/GeoParquet format for efficient storage and loading
"""

import pandas as pd
import geopandas as gpd
from pathlib import Path

# Directory containing raw files
RAW_DIR = Path(__file__).parent / "raw"

def convert_csvs_to_parquet():
    """Convert CSV files to Parquet format"""
    csv_files = [
        "district_mapping.csv",
        "state_centroids.csv",
        "district_centroids.csv"
    ]

    for csv_file in csv_files:
        csv_path = RAW_DIR / csv_file
        parquet_file = csv_file.replace('.csv', '.parquet')
        parquet_path = RAW_DIR / parquet_file

        if csv_path.exists():
            df = pd.read_csv(csv_path)
            df.to_parquet(parquet_path, engine='pyarrow', compression='snappy')
            file_size_csv = csv_path.stat().st_size / 1024  # KB
            file_size_parquet = parquet_path.stat().st_size / 1024  # KB
            print(f"✓ Converted {csv_file} to {parquet_file}")
            print(f"  Size: {file_size_csv:.2f} KB → {file_size_parquet:.2f} KB (saved {file_size_csv - file_size_parquet:.2f} KB)")
        else:
            print(f"✗ Warning: {csv_file} not found")

def convert_geojsons_to_geoparquet():
    """Convert GeoJSON files to GeoParquet format"""
    geojson_files = [
        "state_boundaries.geojson",
        "district_boundaries.geojson"
    ]

    for geojson_file in geojson_files:
        geojson_path = RAW_DIR / geojson_file
        parquet_file = geojson_file.replace('.geojson', '.parquet')
        parquet_path = RAW_DIR / parquet_file

        if geojson_path.exists():
            gdf = gpd.read_file(geojson_path)
            gdf.to_parquet(parquet_path, compression='snappy')
            file_size_geojson = geojson_path.stat().st_size / (1024 * 1024)  # MB
            file_size_parquet = parquet_path.stat().st_size / (1024 * 1024)  # MB
            print(f"✓ Converted {geojson_file} to {parquet_file}")
            print(f"  Size: {file_size_geojson:.2f} MB → {file_size_parquet:.2f} MB (saved {file_size_geojson - file_size_parquet:.2f} MB)")
        else:
            print(f"✗ Warning: {geojson_file} not found")

def main():
    print("Converting CSV files to Parquet...")
    print("=" * 60)
    convert_csvs_to_parquet()

    print("\nConverting GeoJSON files to GeoParquet...")
    print("=" * 60)
    convert_geojsons_to_geoparquet()

    print("\n" + "=" * 60)
    print("Conversion complete! All files saved in raw/ directory")
    print("=" * 60)

if __name__ == "__main__":
    main()
