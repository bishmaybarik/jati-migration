# India Migration Patterns Dashboard

An interactive web-based visualization platform for analyzing internal migration patterns in India at state and district levels, with demographic stratification by caste, religion, and migration motivations.

## Overview

This dashboard provides a geospatial analysis framework for understanding migration flows within India, leveraging household survey data to visualize origin-destination patterns across multiple temporal and demographic dimensions.

## Dataset

### Primary Data Source

**Consumer Pyramids Household Survey (CPHS)** - Centre for Monitoring Indian Economy (CMIE)
- **Temporal Coverage**: 2024 (Jan-Sep available in data)
- **Survey Design**: Longitudinal household panel survey with wave-based data collection
- **Migration Variables**: Self-reported emigration and immigration status with origin and destination information
- **Sample Size**: Nationally representative sample covering rural and urban households

### Derived Variables

The dashboard constructs migration flows by:
1. **Unique Individual Identification**: Creating composite identifiers (`hh_id + mem_id`) to track distinct migrants
2. **Origin-Destination Mapping**: Defining directional flows based on reported migration status
   - Emigration: Current residence → Destination state/district
   - Immigration: Source state/district → Current residence
3. **Geographic Harmonization**: Mapping survey district codes to standardized administrative boundaries using fuzzy matching algorithms

### Geographic Boundaries

Administrative boundaries sourced from:
> Asher, S., Lunt, T., Matsuura, R., & Novosad, P. (2021). *Development research at high geographic resolution: an analysis of night-lights, firms, and poverty in India using the SHRUG open data platform*. The World Bank Economic Review, 35(4). Oxford University Press.

**Spatial Processing**:
- Topology simplification using Douglas-Peucker algorithm
  - State boundaries: tolerance = 0.05 degrees
  - District boundaries: tolerance = 0.02 degrees
- Centroid calculation for origin-destination line rendering

## Methodology

### Data Processing Pipeline

1. **Data Loading & Merging**
   - Parquet-based data storage for efficient columnar access
   - Left-join merge with district mapping crosswalk
   - Filter to migration records (`mem_status ∈ {'Emigrated', 'Immigrated'}`)

2. **Aggregation Strategy**
   - Group by origin-destination pairs at selected geographic level
   - Count unique individuals using `nunique()` on composite identifiers
   - Compute separate aggregations for each demographic filter combination

3. **Spatial Visualization**
   - **Flow Lines**: Origin-destination pairs rendered as great circle arcs
   - **Line Width Encoding**: Logarithmic scale based on migrant counts
     - `width = max(0.5, (log(count + 1) / log(max_count + 1)) × 8)`
   - **Directional Indicators**: Triangle markers positioned at 80% of arc length
   - **Interactive Points**: Centroid-based markers with aggregated inflow/outflow statistics

### Filtering Hierarchy

The dashboard implements cascading filters:
1. **Migration Direction** (Emigration/Immigration)
2. **Geographic Level** (State/District)
3. **Demographic Breakdown** (Overall/Caste Category/Religion)
4. **Specific Category Value** (conditional on breakdown selection)
5. **Caste (Jati)** (conditional on caste category selection)
6. **Migration Reason** (independent filter)

## Technical Stack

### Core Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| **Dash** | ≥2.14.0 | Web application framework and reactive UI |
| **Pandas** | ≥2.0.0 | Data manipulation and aggregation |
| **GeoPandas** | ≥0.13.0 | Geospatial data operations and GeoJSON handling |
| **Plotly** | ≥5.14.0 | Interactive choropleth maps and scatter-geo visualizations |
| **NumPy** | ≥1.24.0 | Numerical computations and array operations |
| **PyArrow** | ≥12.0.0 | Parquet file format I/O |
| **Gunicorn** | ≥21.2.0 | WSGI HTTP server for deployment |

### Algorithms & Techniques

#### Geometric Operations
- **Topology Simplification**: Douglas-Peucker algorithm via GeoPandas `simplify()`
- **Centroid Calculation**: Weighted geographic center computation for polygon geometries
- **Great Circle Interpolation**: Linear interpolation in geographic coordinates for flow lines

#### Data Aggregation
- **GroupBy Operations**: Hierarchical grouping with `observed=True` for categorical optimization
- **Unique Count Estimation**: Hash-based distinct value counting
- **Callback-based Reactivity**: Dash callbacks for efficient state management

#### Visualization Encoding
- **Logarithmic Scaling**: Line width encoding using `np.log1p()` for right-skewed distributions
- **Angular Transformation**: Arctangent-based arrow orientation
  - `angle = arctan2(Δlon, Δlat) × 180/π`
- **Hover Text Aggregation**: Dynamic HTML generation for multi-line tooltips

### Performance Optimizations

1. **Data Loading**: Efficient parquet loading with hybrid storage (AWS S3 + local files)
2. **Geometry Simplification**: Pre-simplified boundaries reduce rendering overhead
3. **Categorical Data Types**: Memory-efficient storage for string columns
4. **Columnar Storage**: Parquet format enables selective column loading

## Installation

### Prerequisites
- Python 3.11 or higher
- pip package manager

### Setup

```bash
# Clone repository
git clone https://github.com/bishmaybarik/jati-migration.git
cd jati-migration

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Local Development

```bash
python app.py
```

Access the dashboard at `http://localhost:8050`

### Deployment

The application is configured for deployment on Render.

**Configuration**:
- Entry point: `app.py`
- WSGI server: Gunicorn
- Deployment config: `render.yaml`

### Data Storage

Data is stored using a hybrid approach:
- **AWS S3**: Migration dataset (2024 only)
  - File: `migration_2024.parquet` (1.45 MB)
  - Bucket: `jati-data`
  - Region: `ap-south-1`
  - Memory footprint: ~10 MB when loaded
- **Local Storage**: Geographic reference files in `raw/` directory (all parquet format, pre-simplified)
  - `district_mapping.parquet` (15 KB)
  - `state_centroids.parquet` (3.4 KB)
  - `district_centroids.parquet` (18 KB)
  - `state_boundaries.parquet` (321 KB, simplified)
  - `district_boundaries.parquet` (196 KB, simplified)

## File Structure

```
jati-migration/
├── app.py                           # Main Dash application (REQUIRED for Render)
├── requirements.txt                 # Python dependencies (REQUIRED for Render)
├── render.yaml                      # Render deployment config (REQUIRED for Render)
├── README.md                        # Documentation
├── .gitignore                       # Git exclusion patterns
├── raw/                             # Local geographic data files (REQUIRED for Render)
│   ├── district_mapping.parquet
│   ├── state_centroids.parquet
│   ├── district_centroids.parquet
│   ├── state_boundaries.parquet
│   └── district_boundaries.parquet
└── b/                               # Build scripts (not needed for deployment)
    ├── check_memory.py              # Memory usage estimation
    ├── convert_parq.py              # CSV/GeoJSON to Parquet converter
    ├── filter_migration_data.py     # Initial filtering script
    └── filter_migration_optimized.py # Optimized filtering script
```

## Features

### Interactive Controls

- **Migration Type Selection**: Toggle between emigration and immigration flows
- **Multi-scale Analysis**: Switch between state-level and district-level granularity
- **Demographic Stratification**: Filter by caste category, religion, or specific jati
- **Reason-based Filtering**: Isolate migration flows by reported motivation
- **Dynamic Hover Information**: Detailed inflow/outflow statistics on map interaction

### Visualization Components

1. **Geographic Base Map**: Administrative boundaries with configurable simplification
2. **Flow Network**: Directed edges with thickness encoding migration volume
3. **Centroid Markers**: Interactive points displaying aggregated statistics
4. **Dashboard Metrics**: Summary statistics (total migrants, flow count, active filters)
5. **Information Panel**: Data provenance and methodology documentation

## Data Limitations

- **Self-reported Data**: Migration status based on household responses
- **Temporal Coverage**: Limited to 2024 only (earlier data excluded for memory efficiency on free deployment tier)
- **Temporal Granularity**: Wave-based observation (monthly snapshots)
- **Geographic Simplification**: Boundary geometries simplified for memory efficiency (may affect visual precision at high zoom)
- **Geographic Specificity**: District-level precision subject to respondent knowledge
- **Survey Coverage**: Representative sample, not census
- **Attrition Bias**: Panel survey subject to household dropout

## Citation

If you use this dashboard or methodology in your research, please cite:

```bibtex
@software{barik2024migration,
  author = {Barik, Bishmay},
  title = {India Migration Patterns Dashboard},
  year = {2024},
  url = {https://github.com/bishmaybarik/jati-migration}
}
```

## License

This project is available for educational and research purposes.

## Author

**Bishmay Barik**

---

© 2024 Bishmay Barik. All rights reserved.
