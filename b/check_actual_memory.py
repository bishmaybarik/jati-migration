#!/usr/bin/env python3
"""
Check actual memory usage of all data files
"""

import pandas as pd
import geopandas as gpd

def format_mb(bytes):
    return f"{bytes / (1024*1024):.2f} MB"

print("Checking ACTUAL memory usage when loaded...")
print("="*70)

total_mem = 0

# Check geographic files
print("\nGEOGRAPHIC FILES:")
print("-"*70)

state_gdf = gpd.read_parquet('raw/state_boundaries.parquet')
mem1 = state_gdf.memory_usage(deep=True).sum()
print(f"state_boundaries.parquet:      {format_mb(mem1)}")
total_mem += mem1

# Apply simplification as in app.py
state_gdf['geometry'] = state_gdf.simplify(tolerance=0.05, preserve_topology=True)
mem1_simplified = state_gdf.memory_usage(deep=True).sum()
print(f"  After simplification (0.05):  {format_mb(mem1_simplified)}")

district_gdf = gpd.read_parquet('raw/district_boundaries.parquet')
mem2 = district_gdf.memory_usage(deep=True).sum()
print(f"\ndistrict_boundaries.parquet:   {format_mb(mem2)}")
total_mem += mem2

# Apply simplification as in app.py
district_gdf['geometry'] = district_gdf.simplify(tolerance=0.02, preserve_topology=True)
mem2_simplified = district_gdf.memory_usage(deep=True).sum()
print(f"  After simplification (0.02):  {format_mb(mem2_simplified)}")

print("\n" + "-"*70)
print(f"Total geographic memory (after simplification): {format_mb(mem1_simplified + mem2_simplified)}")

# CSV files
print("\nCSV FILES:")
print("-"*70)
district_mapping = pd.read_parquet('raw/district_mapping.parquet')
mem3 = district_mapping.memory_usage(deep=True).sum()
print(f"district_mapping.parquet:      {format_mb(mem3)}")
total_mem += mem3

state_centroids = pd.read_parquet('raw/state_centroids.parquet')
mem4 = state_centroids.memory_usage(deep=True).sum()
print(f"state_centroids.parquet:       {format_mb(mem4)}")
total_mem += mem4

district_centroids = pd.read_parquet('raw/district_centroids.parquet')
mem5 = district_centroids.memory_usage(deep=True).sum()
print(f"district_centroids.parquet:    {format_mb(mem5)}")
total_mem += mem5

# Migration data
print("\nMIGRATION DATA:")
print("-"*70)
if 'raw/migration_2023_2024.parquet' in str(pd.io.common.file_exists('raw/migration_2023_2024.parquet')):
    migration_df = pd.read_parquet('raw/migration_2023_2024.parquet')
    mem6 = migration_df.memory_usage(deep=True).sum()
    print(f"migration_2023_2024.parquet:   {format_mb(mem6)}")
else:
    mem6 = 0
    print("migration_2023_2024.parquet:   Not found locally (on AWS)")

print("\n" + "="*70)
print("TOTAL MEMORY ESTIMATE:")
print("="*70)
print(f"Geographic files (simplified): {format_mb(mem1_simplified + mem2_simplified)}")
print(f"CSV files:                     {format_mb(mem3 + mem4 + mem5)}")
print(f"Migration data (2023-2024):    {format_mb(mem6 if mem6 > 0 else 22.90 * 1024 * 1024)}")
print(f"Python + Libraries:            ~250 MB")
print("-"*70)
total_estimate = (mem1_simplified + mem2_simplified + mem3 + mem4 + mem5 +
                  (mem6 if mem6 > 0 else 22.90 * 1024 * 1024) + 250 * 1024 * 1024)
print(f"TOTAL ESTIMATED:               {format_mb(total_estimate)}")
print(f"Render Free Tier Limit:        512 MB")
print(f"Headroom:                      {format_mb(512 * 1024 * 1024 - total_estimate)}")
print("="*70)
