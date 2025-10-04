#!/usr/bin/env python3
"""
Filter migration data to Jan 2022 - Dec 2024
"""

import pandas as pd
from datetime import datetime

print("Loading migration data from AWS S3...")
migration_df = pd.read_parquet('https://jati-data.s3.ap-south-1.amazonaws.com/migration.parquet')

print(f"\nOriginal data shape: {migration_df.shape}")
print(f"Columns: {list(migration_df.columns)}")

# Check for date columns
print("\nLooking for date-related columns...")
date_columns = [col for col in migration_df.columns if 'date' in col.lower() or 'wave' in col.lower() or 'month' in col.lower() or 'year' in col.lower()]
print(f"Date-related columns: {date_columns}")

# Display first few rows
print("\nFirst few rows:")
print(migration_df.head())

# Check data types
print("\nColumn data types:")
print(migration_df.dtypes)

# Check unique values in potential date columns
for col in date_columns:
    print(f"\n{col} unique values (first 20):")
    print(sorted(migration_df[col].dropna().unique())[:20])

print("\n" + "="*70)
print("Now filtering data to Jan 2022 - Dec 2024...")
print("="*70)

# Use month_slot column for filtering
date_col = 'month_slot'
print(f"\nUsing column '{date_col}' for filtering...")

# Convert month_slot to datetime (first convert categorical to string)
migration_df['date_parsed'] = pd.to_datetime(migration_df[date_col].astype(str), format='%b %Y')

# Filter to Jan 2022 - Dec 2024
start_date = pd.to_datetime('2022-01-01')
end_date = pd.to_datetime('2024-12-31')

filtered_df = migration_df[(migration_df['date_parsed'] >= start_date) & (migration_df['date_parsed'] <= end_date)].copy()

# Drop the temporary date_parsed column
filtered_df = filtered_df.drop(columns=['date_parsed'])

print(f"\nFiltered data shape: {filtered_df.shape}")
print(f"Reduction: {len(migration_df) - len(filtered_df):,} rows removed ({((len(migration_df) - len(filtered_df))/len(migration_df)*100):.1f}%)")

# Save to parquet
output_path = 'raw/migration_2022_2024.parquet'
print(f"\nSaving to {output_path}...")
filtered_df.to_parquet(output_path, engine='pyarrow', compression='snappy')

# Check file sizes
import os
file_size = os.path.getsize(output_path) / (1024 * 1024)
print(f"✓ Saved successfully! File size: {file_size:.2f} MB")

# Check memory usage
mem_usage = filtered_df.memory_usage(deep=True).sum() / (1024 * 1024)
print(f"✓ Memory usage: {mem_usage:.2f} MB")

print("\n" + "="*70)
print("Date range in filtered data:")
print(f"  Earliest month_slot: {sorted(filtered_df[date_col].unique())[0]}")
print(f"  Latest month_slot: {sorted(filtered_df[date_col].unique())[-1]}")
print(f"  Total unique months: {filtered_df[date_col].nunique()}")
print("="*70)
