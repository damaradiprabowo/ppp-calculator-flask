# PPP Value Converted
This project is a web application that calculates equivalent monetary values between countries based on Purchasing Power Parity (PPP). It helps users understand how different amounts (salaries, costs, income, spending) translate across countries, considering factors like GDP per capita and income levels.

## Features
- Calculate equivalent monetary values between countries
- Display additional country information (capital city, income level, GDP per capita)
- Responsive design for various screen sizes
- Loading animation during calculations
- Informational popups for credits and definitions

## Tech Stack
- **Backend:** Python with Flask
- **Frontend:** HTML, CSS, JavaScript
- **APIs:** World Bank API, Rest Countries API

## Setup and Installation
1. Clone the repository:
   ```bash
   git clone git@github.com:damaradiprabowo/ppp-calculator-flask.git
   ``` 
2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the Flask application:
   ```bash
   python app.py
   ```
4. Open a web browser and navigate to [http://localhost:5000](http://localhost:5000)

## Project Structure
```
PPPCalculator/
│
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── templates/
│   └── index.html             # HTML template for the main page
└── static/
    ├── css/
    │   └── styles.css         # CSS styles for the application
    └── js/
        └── script.js          # JavaScript for frontend functionality
```

## Credits
Credits to the following resources:
- inspiration: https://www.chrislross.com/PPPConverter/
- World Bank API: https://www.worldbank.org/
- Rest Country API: https://restcountries.com/