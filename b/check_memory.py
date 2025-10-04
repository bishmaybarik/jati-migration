#!/usr/bin/env python3
"""
Estimate memory usage for the migration dashboard
"""

import pandas as pd
import geopandas as gpd
import sys

def format_bytes(bytes):
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.2f} TB"

print("Checking memory requirements for migration dashboard...")
print("=" * 70)

total_memory = 0

# Check local files
print("\n1. LOCAL FILES (in raw/ folder):")
print("-" * 70)

try:
    district_mapping = pd.read_parquet('raw/district_mapping.parquet')
    mem1 = district_mapping.memory_usage(deep=True).sum()
    print(f"   district_mapping.parquet: {format_bytes(mem1)}")
    total_memory += mem1

    state_centroids = pd.read_parquet('raw/state_centroids.parquet')
    mem2 = state_centroids.memory_usage(deep=True).sum()
    print(f"   state_centroids.parquet: {format_bytes(mem2)}")
    total_memory += mem2

    district_centroids = pd.read_parquet('raw/district_centroids.parquet')
    mem3 = district_centroids.memory_usage(deep=True).sum()
    print(f"   district_centroids.parquet: {format_bytes(mem3)}")
    total_memory += mem3

    state_gdf = gpd.read_parquet('raw/state_boundaries.parquet')
    mem4 = state_gdf.memory_usage(deep=True).sum()
    print(f"   state_boundaries.parquet: {format_bytes(mem4)}")
    total_memory += mem4

    district_gdf = gpd.read_parquet('raw/district_boundaries.parquet')
    mem5 = district_gdf.memory_usage(deep=True).sum()
    print(f"   district_boundaries.parquet: {format_bytes(mem5)}")
    total_memory += mem5

except Exception as e:
    print(f"   Error loading local files: {e}")

# Check AWS S3 file
print("\n2. AWS S3 FILE:")
print("-" * 70)

try:
    print("   Loading migration.parquet from S3 (this may take a moment)...")
    migration_df = pd.read_parquet('https://jati-data.s3.ap-south-1.amazonaws.com/migration.parquet')
    mem6 = migration_df.memory_usage(deep=True).sum()
    print(f"   migration.parquet: {format_bytes(mem6)}")
    print(f"   Rows: {len(migration_df):,}, Columns: {len(migration_df.columns)}")
    total_memory += mem6
except Exception as e:
    print(f"   Error loading S3 file: {e}")
    print("   Note: Couldn't load from S3. Estimated size: ~100-200 MB")

# Summary
print("\n" + "=" * 70)
print("MEMORY USAGE SUMMARY:")
print("=" * 70)
print(f"Total Data in Memory: {format_bytes(total_memory)}")
print(f"\nEstimated Total Runtime Memory (with Python + libraries):")
print(f"  - Base Python + Libraries: ~200-300 MB")
print(f"  - Your Data: {format_bytes(total_memory)}")
print(f"  - TOTAL ESTIMATED: ~{format_bytes(total_memory + 250*1024*1024)}")
print("\n" + "=" * 70)
print("RENDER LIMITS:")
print("=" * 70)
print("  Free Tier: 512 MB RAM")
print("  Starter ($7/mo): 512 MB RAM")
print("  Standard ($25/mo): 2 GB RAM")
print("  Pro ($85/mo): 4 GB RAM")
