from flask import Flask, render_template, request, jsonify, redirect
import requests
from datetime import datetime
import math
from functools import lru_cache
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import json

app = Flask(__name__)

# Constants
WORLD_BANK_DATA_INDEX = 1
EARTH_RADIUS_KM = 6371
API_TIMEOUT = 10  # seconds
MAX_RETRIES = 3

# Global cache
COUNTRY_DATA = {}
WORLD_BANK_DATA = []
COUNTRIES_STATIC_DATA = {}

# Configure requests with retries
retry_strategy = Retry(
    total=MAX_RETRIES,
    backoff_factor=1,
    status_forcelist=[500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("https://", adapter)
http.mount("http://", adapter)

def load_static_country_data():
    global COUNTRIES_STATIC_DATA
    try:
        with open('static/data/country_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Index by ISO2 code for faster lookups
            COUNTRIES_STATIC_DATA = {
                country['cca2'].lower(): country 
                for country in data
            }
    except Exception as e:
        print(f"Error loading static country data: {e}")

@lru_cache(maxsize=128)
def get_currency_info(iso2_code):
    country_data = COUNTRIES_STATIC_DATA.get(iso2_code)
    if country_data and 'currencies' in country_data:
        currency_data = country_data['currencies']
        currency_code = list(currency_data.keys())[0]
        return {
            'code': currency_code,
            'name': currency_data[currency_code]['name'],
            'symbol': currency_data[currency_code]['symbol']
        }
    return {'code': 'Unknown', 'name': 'Unknown', 'symbol': 'Unknown'}

def get_country_and_ppp_data():
    year = datetime.now().year
    data_urls = {
        'ppp': f"https://api.worldbank.org/v2/en/country/all/indicator/PA.NUS.PPP?format=json&per_page=20000&source=2&date={year - 5}:{year}",
        'gdp': f"https://api.worldbank.org/v2/en/country/all/indicator/NY.GDP.PCAP.CD?format=json&per_page=20000&source=2&date={year - 5}:{year}"
    }
    
    country_data = {}
    try:
        for indicator_type, url in data_urls.items():
            response = http.get(url, timeout=API_TIMEOUT)
            data = response.json()[WORLD_BANK_DATA_INDEX]
            
            for item in data:
                if item['value'] is not None:
                    country = item['country']['value']
                    if country not in country_data:
                        country_data[country] = {'ppp': {}, 'gdp': {}}
                    
                    country_data[country][indicator_type][item['date']] = item['value']
        
        return country_data
    except Exception as e:
        print(f"Failed to retrieve country data: {e}")
        return {}

# Create an index for faster country lookups
country_lookup = {}
def load_world_bank_data():
    global WORLD_BANK_DATA, country_lookup
    try:
        response = http.get(
            "https://api.worldbank.org/v2/country?format=json&per_page=20000",
            timeout=API_TIMEOUT
        )
        if response.status_code == 200:
            WORLD_BANK_DATA = response.json()[1]
            country_lookup = {country['name']: country for country in WORLD_BANK_DATA}
    except Exception as e:
        print(f"Failed to fetch World Bank data: {e}")

def get_country_info(country_name):
    country_data = country_lookup.get(country_name)
    if country_data:
        iso2_code = country_data['iso2Code'].lower()
        currency_info = get_currency_info(iso2_code)
        return {
            'incomeLevel': country_data['incomeLevel']['value'],
            'capitalCity': country_data['capitalCity'],
            'latitude': float(country_data['latitude']),
            'longitude': float(country_data['longitude']),
            'iso2Code': iso2_code,
            'currency': currency_info
        }
    return {
        'incomeLevel': 'Unknown', 
        'capitalCity': 'Unknown', 
        'latitude': 0, 
        'longitude': 0,
        'iso2Code': 'unknown',
        'currency': {'code': 'Unknown', 'name': 'Unknown', 'symbol': 'Unknown'}
    }

def calculate_distance(country1, country2):
    info1 = get_country_info(country1)
    info2 = get_country_info(country2)
    
    lat1, lon1 = map(math.radians, [info1['latitude'], info1['longitude']])
    lat2, lon2 = map(math.radians, [info2['latitude'], info2['longitude']])

    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return round(EARTH_RADIUS_KM * c, 2)

# Initialize data at startup
COUNTRY_DATA = get_country_and_ppp_data()
load_world_bank_data()
load_static_country_data()

@app.route('/')
def index():
    return render_template('index.html', countries=sorted(COUNTRY_DATA.keys()))

@app.route('/convert/')
def convert_page():
    countries = sorted(COUNTRY_DATA.keys())
    
    source = request.args.get('source', 'indonesia').replace('-', ' ').title()
    destination = request.args.get('destination', 'united-states').replace('-', ' ').title()
    value = request.args.get('value', '')
    granularity = request.args.get('granularity', 'monthly')
    
    # Validate countries
    if source not in COUNTRY_DATA or destination not in COUNTRY_DATA:
        return redirect('/')
        
    return render_template('index.html', 
                         countries=countries,
                         selected_source=source,
                         selected_target=destination,
                         initial_value=value,
                         initial_granularity=granularity)

@app.context_processor
def utility_processor():
    def slugify(text):
        # Simple slugify function - replace spaces with dashes and lowercase
        return text.lower().replace(' ', '-')
    return dict(slugify=slugify)

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        source_country = request.form['sourceCountry']
        target_country = request.form['targetCountry']
        source_amount = float(request.form['sourceAmount'].replace(',', ''))
        salary_frequency = request.form['salaryFrequency']

        yearly_source_amount = source_amount * (12 if salary_frequency == 'monthly' else 1)

        source_ppp = max(COUNTRY_DATA[source_country]['ppp'].values())
        target_ppp = max(COUNTRY_DATA[target_country]['ppp'].values())

        yearly_target_amount = yearly_source_amount / source_ppp * target_ppp
        monthly_target_amount = yearly_target_amount / 12

        source_info = get_country_info(source_country)
        target_info = get_country_info(target_country)

        return jsonify({
            'sourceAmount': f"{source_amount:.2f}",
            'sourceFrequency': salary_frequency,
            'targetAmountMonthly': f"{target_info['currency']['code']} {monthly_target_amount:,.2f}",
            'targetAmountYearly': f"{target_info['currency']['code']} {yearly_target_amount:,.2f}",
            'sourceCountry': source_country,
            'targetCountry': target_country,
            'sourceIncomeLevel': source_info['incomeLevel'],
            'targetIncomeLevel': target_info['incomeLevel'],
            'targetCapital': target_info['capitalCity'],
            'distance': f"{calculate_distance(source_country, target_country):.2f}",
            'sourceIso2Code': source_info['iso2Code'],
            'targetIso2Code': target_info['iso2Code'],
            'sourceGDP': f"{max(COUNTRY_DATA[source_country]['gdp'].values()):.2f}",
            'targetGDP': f"{max(COUNTRY_DATA[target_country]['gdp'].values()):.2f}"
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)