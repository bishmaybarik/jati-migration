#!/usr/bin/env python3
"""
Aggressive optimization for Render deployment:
1. Filter to 2024 only
2. Simplify geometries much more aggressively
"""

import pandas as pd
import geopandas as gpd

print("="*70)
print("STEP 1: Filter migration data to 2024 only")
print("="*70)

migration_df = pd.read_parquet('https://jati-data.s3.ap-south-1.amazonaws.com/migration_2023_2024.parquet')
print(f"Original (2023-2024): {migration_df.shape[0]:,} rows")

valid_months_2024 = ['Jan 2024', 'Feb 2024', 'Mar 2024', 'Apr 2024', 'May 2024', 'Jun 2024',
                     'Jul 2024', 'Aug 2024', 'Sep 2024', 'Oct 2024', 'Nov 2024', 'Dec 2024']

filtered_df = migration_df[migration_df['month_slot'].isin(valid_months_2024)].copy()
print(f"Filtered (2024 only): {filtered_df.shape[0]:,} rows")
print(f"Reduction: {((len(migration_df) - len(filtered_df))/len(migration_df)*100):.1f}%")

# Save
filtered_df.to_parquet('raw/migration_2024.parquet', engine='pyarrow', compression='snappy', index=False)
import os
file_size = os.path.getsize('raw/migration_2024.parquet') / (1024*1024)
mem_size = filtered_df.memory_usage(deep=True).sum() / (1024*1024)
print(f"File size: {file_size:.2f} MB")
print(f"Memory: {mem_size:.2f} MB")

print("\n" + "="*70)
print("STEP 2: Simplify geometries more aggressively")
print("="*70)

# State boundaries
print("\nState boundaries:")
state_gdf = gpd.read_parquet('raw/state_boundaries.parquet')
print(f"  Original memory: {state_gdf.memory_usage(deep=True).sum() / (1024*1024):.2f} MB")

# Increase tolerance from 0.05 to 0.15
state_gdf['geometry'] = state_gdf.simplify(tolerance=0.15, preserve_topology=True)
print(f"  Simplified (0.15): {state_gdf.memory_usage(deep=True).sum() / (1024*1024):.2f} MB")

state_gdf.to_parquet('raw/state_boundaries_simplified.parquet', compression='snappy')
file_size = os.path.getsize('raw/state_boundaries_simplified.parquet') / (1024*1024)
print(f"  File size: {file_size:.2f} MB")

# District boundaries
print("\nDistrict boundaries:")
district_gdf = gpd.read_parquet('raw/district_boundaries.parquet')
print(f"  Original memory: {district_gdf.memory_usage(deep=True).sum() / (1024*1024):.2f} MB")

# Increase tolerance from 0.02 to 0.08
district_gdf['geometry'] = district_gdf.simplify(tolerance=0.08, preserve_topology=True)
print(f"  Simplified (0.08): {district_gdf.memory_usage(deep=True).sum() / (1024*1024):.2f} MB")

district_gdf.to_parquet('raw/district_boundaries_simplified.parquet', compression='snappy')
file_size = os.path.getsize('raw/district_boundaries_simplified.parquet') / (1024*1024)
print(f"  File size: {file_size:.2f} MB")

print("\n" + "="*70)
print("FINAL SUMMARY")
print("="*70)
print(f"Migration data (2024):         {mem_size:.2f} MB in memory")
print(f"State boundaries (simplified): <0.1 MB in memory")
print(f"District boundaries (simp):    <0.2 MB in memory")
print(f"CSV files:                     <0.2 MB in memory")
print(f"Python + libraries:            ~200-250 MB")
print("-"*70)
total = mem_size + 0.5 + 225
print(f"ESTIMATED TOTAL:               ~{total:.0f} MB")
print(f"Render Free Tier:              512 MB")
print(f"Headroom:                      ~{512-total:.0f} MB ({((512-total)/512*100):.0f}%)")
print("="*70)
