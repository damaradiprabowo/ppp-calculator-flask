from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime
import math

app = Flask(__name__)

WORLD_BANK_DATA_INDEX = 1
COUNTRY_DATA = {}
WORLD_BANK_DATA = []

def get_country_and_ppp_data():
    year = datetime.now().year
    ppp_url = f"https://api.worldbank.org/v2/en/country/all/indicator/PA.NUS.PPP?format=json&per_page=20000&source=2&date={year - 5}:{year}"
    gdp_url = f"https://api.worldbank.org/v2/en/country/all/indicator/NY.GDP.PCAP.CD?format=json&per_page=20000&source=2&date={year - 5}:{year}"
    
    try:
        ppp_response = requests.get(ppp_url)
        gdp_response = requests.get(gdp_url)
        ppp_data = ppp_response.json()[WORLD_BANK_DATA_INDEX]
        gdp_data = gdp_response.json()[WORLD_BANK_DATA_INDEX]
        
        country_data = {}
        for item in ppp_data + gdp_data:
            if item['value'] is not None:
                country = item['country']['value']
                date = item['date']
                value = item['value']
                indicator = item['indicator']['id']
                
                if country not in country_data:
                    country_data[country] = {'ppp': {}, 'gdp': {}}
                
                if indicator == 'PA.NUS.PPP':
                    country_data[country]['ppp'][date] = value
                elif indicator == 'NY.GDP.PCAP.CD':
                    country_data[country]['gdp'][date] = value
        
        return country_data
    except:
        print("Failed to retrieve country data")
        return {}

def load_world_bank_data():
    global WORLD_BANK_DATA
    url = "https://api.worldbank.org/v2/country?format=json&per_page=20000"
    response = requests.get(url)
    if response.status_code == 200:
        WORLD_BANK_DATA = response.json()[1]  # The actual country data is in the second element of the response
    else:
        print(f"Failed to fetch World Bank data: {response.status_code}")

def get_currency_info(iso2_code):
    url = f"https://restcountries.com/v3.1/alpha/{iso2_code}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()[0]
            currency_data = data['currencies']
            currency_code = list(currency_data.keys())[0]
            return {
                'code': currency_code,
                'name': currency_data[currency_code]['name'],
                'symbol': currency_data[currency_code]['symbol']
            }
    except Exception as e:
        print(f"Error fetching currency data: {e}")
    return {'code': 'Unknown', 'name': 'Unknown', 'symbol': 'Unknown'}

def get_country_info(country_name):
    country_data = next((country for country in WORLD_BANK_DATA if country['name'] == country_name), None)
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
    else:
        print(f"Country data not found for {country_name}")
        return {
            'incomeLevel': 'Unknown', 
            'capitalCity': 'Unknown', 
            'latitude': 0, 
            'longitude': 0,
            'iso2Code': 'unknown',
            'currency': {'code': 'Unknown', 'name': 'Unknown', 'symbol': 'Unknown'}
        }

def calculate_distance(country1, country2):
    # Earth's radius in kilometers
    R = 6371

    # Get coordinates for both countries
    info1 = get_country_info(country1)
    info2 = get_country_info(country2)
    lat1, lon1 = info1['latitude'], info1['longitude']
    lat2, lon2 = info2['latitude'], info2['longitude']

    # Convert latitude and longitude to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    distance = R * c

    return round(distance, 2)

COUNTRY_DATA = get_country_and_ppp_data()
load_world_bank_data()

@app.route('/')
def index():
    return render_template('index.html', countries=sorted(COUNTRY_DATA.keys()))

@app.route('/calculate', methods=['POST'])
def calculate():
    source_country = request.form['sourceCountry']
    target_country = request.form['targetCountry']
    source_amount = float(request.form['sourceAmount'].replace(',', ''))
    salary_frequency = request.form['salaryFrequency']

    # Convert source amount to yearly if it's monthly
    yearly_source_amount = source_amount * 12 if salary_frequency == 'monthly' else source_amount

    source_ppp = max(COUNTRY_DATA[source_country]['ppp'].values())
    target_ppp = max(COUNTRY_DATA[target_country]['ppp'].values())

    yearly_target_amount = yearly_source_amount / source_ppp * target_ppp
    monthly_target_amount = yearly_target_amount / 12

    # Format amounts in US currency format
    yearly_target_amount = "${:,.2f}".format(yearly_target_amount)
    monthly_target_amount = "${:,.2f}".format(monthly_target_amount)

    source_info = get_country_info(source_country)
    target_info = get_country_info(target_country)

    target_currency_code = target_info['currency']['code']

    distance = calculate_distance(source_country, target_country)

    source_gdp = max(COUNTRY_DATA[source_country]['gdp'].values())
    target_gdp = max(COUNTRY_DATA[target_country]['gdp'].values())

    return jsonify({
        'sourceAmount': f"{source_amount:.2f}",
        'sourceFrequency': salary_frequency,
        'targetAmountMonthly': f"{target_currency_code} {monthly_target_amount}",
        'targetAmountYearly': f"{target_currency_code} {yearly_target_amount}",
        'sourceCountry': source_country,
        'targetCountry': target_country,
        'sourceIncomeLevel': source_info['incomeLevel'],
        'targetIncomeLevel': target_info['incomeLevel'],
        'targetCapital': target_info['capitalCity'],
        'distance': f"{distance:.2f}",
        'sourceIso2Code': source_info['iso2Code'],
        'targetIso2Code': target_info['iso2Code'],
        'sourceGDP': f"{source_gdp:.2f}",
        'targetGDP': f"{target_gdp:.2f}"
    })

if __name__ == '__main__':
    app.run(debug=True)