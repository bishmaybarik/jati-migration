# India Migration Patterns Dashboard

An interactive web dashboard visualizing migration patterns across India at state and district levels. Built with Plotly Dash and deployed using AWS S3 for data storage.

## Features

- **Interactive Map Visualization**: View migration flows with directional arrows showing movement patterns
- **Multiple Analysis Levels**: Switch between state-level and district-level analysis
- **Demographic Filters**: Filter by caste category, religion, specific caste (jati), and migration reasons
- **Real-time Updates**: Dynamic filtering with instant visualization updates
- **Comprehensive Data**: Based on Consumer Pyramids Household Survey (CPHS) data from 2020-2024

## Data Source

Migration patterns are based on reported responses from Consumer Pyramids Household Survey (CPHS) members, covering waves from September-December 2020 through September-December 2024.

Geographic boundaries are sourced from Asher, S., Lunt, T., Matsuura, R., & Novosad, P. (2021). Development research at high geographic resolution: an analysis of night-lights, firms, and poverty in India using the SHRUG open data platform. *The World Bank Economic Review, 35*(4).

## Installation

### Prerequisites

- Python 3.11 or higher
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone https://github.com/bishmaybarik/jati-migration.git
cd jati-migration
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running Locally

To run the dashboard on your local machine:

```bash
python app.py
```

Then open your browser and navigate to `http://localhost:8050`

## Deployment Options

### Option 1: Render (Recommended - Free & Easy)

[Render](https://render.com) offers free hosting for web applications with automatic deployments from GitHub.

**Steps:**
1. Push your code to GitHub
2. Sign up at [render.com](https://render.com)
3. Create a new "Web Service"
4. Connect your GitHub repository
5. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:server`
   - **Environment**: Python 3

### Option 2: Railway

[Railway](https://railway.app) provides a simple deployment platform with generous free tier.

**Steps:**
1. Sign up at [railway.app](https://railway.app)
2. Create new project from GitHub repo
3. Railway auto-detects Python and uses the Procfile
4. Deploy!

### Option 3: Heroku

[Heroku](https://www.heroku.com) is a classic platform with easy deployment.

**Steps:**
1. Install Heroku CLI
2. Login: `heroku login`
3. Create app: `heroku create your-app-name`
4. Deploy: `git push heroku main`

### Option 4: PythonAnywhere

[PythonAnywhere](https://www.pythonanywhere.com) offers easy Python app hosting.

**Steps:**
1. Sign up for free account
2. Create new web app (Flask/Django, but works with Dash)
3. Upload files or clone from GitHub
4. Configure WSGI file to point to `app:server`

### Option 5: Streamlit Cloud

While this is a Dash app, you could convert it to Streamlit for free hosting at [streamlit.io/cloud](https://streamlit.io/cloud).

## Environment Variables

If you need to configure any environment variables (e.g., for authentication or custom settings), create a `.env` file:

```
PORT=8050
```

## File Structure

```
jati-migration/
├── app.py                 # Main application file
├── requirements.txt       # Python dependencies
├── Procfile              # Process file for deployment
├── runtime.txt           # Python version specification
├── .gitignore           # Git ignore rules
└── README.md            # This file
```

## Technology Stack

- **Frontend**: Plotly Dash
- **Backend**: Flask (via Dash)
- **Data Processing**: Pandas, GeoPandas
- **Visualization**: Plotly
- **Data Storage**: AWS S3
- **Deployment**: Gunicorn

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available for educational and research purposes.

## Contact

Created by Bishmay Barik

---

© 2024 Bishmay Barik. All rights reserved.
