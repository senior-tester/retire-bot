import requests
import datetime
import secret

# Your FRED API key (get one from https://fred.stlouisfed.org/)
FRED_API_KEY = secret.FRED_API_KEY

# FRED series ID for U.S. Consumer Price Index (CPI-U, All Urban Consumers)
SERIES_ID = 'CPIAUCSL'


# Function to get CPI data from FRED API
def get_cpi_data(series_id, start_date, end_date):
    url = f"https://api.stlouisfed.org/fred/series/observations"
    params = {
        'series_id': series_id,
        'api_key': FRED_API_KEY,
        'file_type': 'json',
        'observation_start': start_date,
        'observation_end': end_date
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data['observations']


# Function to calculate total inflation rate (YoY)
def calculate_total_inflation(cpi_data):
    # Get the first and last CPI values (over a 1-year period)
    start_cpi = float(cpi_data[0]['value'])
    end_cpi = float(cpi_data[-1]['value'])

    # Calculate total inflation over the year
    total_inflation = ((end_cpi - start_cpi) / start_cpi) * 100
    return total_inflation


# Main function to calculate the total inflation rate over the past year
def get_total_inflation_rate(days):
    # Define the date range
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=days)

    # Fetch CPI data for the past year
    cpi_data = get_cpi_data(SERIES_ID, start_date.isoformat(), end_date.isoformat())

    # Calculate total inflation over the past year
    if len(cpi_data) >= 2:
        total_inflation_rate = calculate_total_inflation(cpi_data)
        return total_inflation_rate
    else:
        return None
