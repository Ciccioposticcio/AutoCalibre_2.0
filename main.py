
# py -3 -m venv .venv (Solo se .venv non è stata creata)
# Set-Executionpolicy Unrestricted -Scope Process
# .venv\Scripts\activate
# python.exe -m pip install --upgrade pip
# pip install flask-sqlalchemy: integrazione fra flask e sqlalchemy (questo installa anche flask e sqlalchemy)
# pip install alembic: Modulo usato per la gestione della migrazione del database
# pip install requests: Modulo per le chiamate alle API 
#-------------------------------------------------------------------------------------------------------
# LIBRERIE NON INSTALLATE 
# pip install babel: Modulo usato per facilitare la formattazione di date e currency. E trova impiego anche per la internazionalizzazione delle applicazioni. Questo modulo è integrabile con Flask tramite Babel-Flask
# pip install python-dateutil: Modulo usato per facilitare la gestione delle date
#-------------------------------------------------------------------------------------------------------
# Alpha Vantage API key: 905QT51HKUH8KETT 
#a908025f2d39706780c95b4e2ba199622860f43e
#-------------------------------------------------------------------------------------------------------
#import main #importa le funzioni e variabili dell'applicazione main.py

from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy


# Inizializza l'applicazione Flask
app = Flask(__name__)

#Configuro il database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///autocalibre.sqlite'  # il database è posizionato dentro <nomeprogetto>\instance\<nomedb>.sqlite
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy()
db.init_app(app)

#Definisco variabili di configurazione visibili a livello globale
app.config["API_KEY"] = ""

# Route per la home page
@app.route('/')
def home():
    app.config["API_KEY"] = get_API_KEY()
    roic = 'x'
    tiingo_get_DAILY("AAPL")
    #tiingo_get_FUNDAMENTALS("AAPL")
    exit(1)
    return render_template('index.html', roic = roic)


def calcola_AlphaAdvantage_Ebit(symbol, income_data ):
    x= 0
    # Utilizza i dati del report annuale più recente
    latest_annual_report = income_data['annualReports'][0]  # Rapporto annuale più recente

    # Estrai COGS e Income Before Tax
    cogs = float(latest_annual_report.get("costOfRevenue", 0))
    income_before_tax = float(latest_annual_report.get("incomeBeforeTax", 0))

    # Approssima EBIT come Income Before Tax + COGS
    ebit = income_before_tax + cogs

    # Stampa il risultato
    print(f"EBIT approssimativo per {symbol}: ${ebit:.2f}")
    return(ebit)

def calcola_AlphaAdvantage_TaxRate(data):
    # Utilizza i dati del report annuale più recente
    latest_annual_report = data['annualReports'][0]  # Rapporto annuale più recente

    # Estrai Net Income e Income Before Tax
    net_income = float(latest_annual_report.get("netIncome", 0))
    income_before_tax = float(latest_annual_report.get("incomeBeforeTax", 0))

    # Calcola il Tax Rate
    if income_before_tax != 0:  # Evita la divisione per zero
        tax_rate = 1 - (net_income / income_before_tax)
        tax_rate_percentage = tax_rate * 100
        print(f"Tax Rate: {tax_rate_percentage:.2f}%")
    else:
        print("Income Before Tax è zero, impossibile calcolare l'aliquota fiscale.")
    
    return tax_rate
    
def calcola_AlphaAdvantage_ROIC(symbol,ebit,taxRate, balance_sheet_data):

    # Ottieni il capitale investito (Net Working Capital + Fixed Assets) dal bilancio
    latest_annual_report = balance_sheet_data['annualReports'][0]  # Rapporto annuale più recente
    net_working_capital = float(latest_annual_report.get("totalCurrentAssets", 0)) - float(latest_annual_report.get("totalCurrentLiabilities", 0))
    fixed_assets = float(latest_annual_report.get("totalNonCurrentAssets", 0))
    total_invested_capital = net_working_capital + fixed_assets

    # Aliquota fiscale (può variare, qui usiamo il 21% come media USA)
    

    # Calcolo del ROIC
    roic = (ebit * (1 - taxRate)) / total_invested_capital * 100
    print(f"ROIC per {symbol}: {roic:.2f}%")
    return roic

def get_AlphaAdvantage_OVERVIEW(symbol):
    import requests
    api_key = app.config["API_KEY"]
    endpoint = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={api_key}'
    response = requests.get(endpoint)
    data = response.json()
    return data

def get_AlphaAdvantage_INCOME_STATEMENT(symbol):
    import requests
    api_key = app.config["API_KEY"]
    # Ottieni il conto economico (Income Statement)
    income_statement_url = f'https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol={symbol}&apikey={api_key}'
    income_statement_response = requests.get(income_statement_url)
    income_data = income_statement_response.json()
    return income_data

def get_AlphaAdvantage_BALANCE_SHEET(symbol):
    import requests
    api_key = app.config["API_KEY"]
    balance_sheet_url = f'https://www.alphavantage.co/query?function=BALANCE_SHEET&symbol={symbol}&apikey={api_key}'
    balance_sheet_response = requests.get(balance_sheet_url)
    balance_sheet_data = balance_sheet_response.json()
    return balance_sheet_data


@app.route("/cercaTicker", methods=["POST"])
def cercaTicker():
    #import os
    #print("Esecuzione di main.py tramite os.system...")
    #os.system('python main.py ' + ticker)  # Esegue main.py come comando
    
    ticker = request.form.get("name_input_cercaTicker") #contiene il ticker
    data = get_AlphaAdvantage_OVERVIEW(ticker)
    # Stampa i dati fondamentali
    print("Fundamentals for", ticker)
    print("P/E Ratio:", data.get("PERatio"))
    print("Revenue:", data.get("RevenueTTM"))
    print("Free Cash Flow:", data.get("FreeCashFlowTTM"))
    print("Sector:", data.get("Sector"))
    
    # Puoi accedere a molti altri campi come `MarketCapitalization`, `DividendYield`, ecc.
    
    # Calcola l'Ebit
    income_data = get_AlphaAdvantage_INCOME_STATEMENT(ticker)
    ebit = calcola_AlphaAdvantage_Ebit(ticker,income_data)
    
    taxRate = calcola_AlphaAdvantage_TaxRate(income_data)
    
    #Calcola il ROIC
    balance_sheet_data = get_AlphaAdvantage_BALANCE_SHEET(ticker)
    roic = calcola_AlphaAdvantage_ROIC(ticker,ebit,taxRate, balance_sheet_data)
    print (f"ROIC: {roic} - Ebit: {ebit} - Tax rate: {taxRate}")
    return render_template('index.html', roic = roic)

def get_API_KEY():
    file = "api_key"
    fa = open(file, 'r')
    Lines = fa.readlines()
    for x in Lines:
        x = x.split("\n")[0] #prende tutto quello che precede il carattere '\n' presente alla fine della riga
        x = x.replace(" ","") #tolgo eventuali spazi dalla stringa
    return x

def tiingo_get_FUNDAMENTALS(ticker):
    import requests
    api_key = app.config["API_KEY"]
    url = f"https://api.tiingo.com/tiingo/fundamentals/{ticker}/statements"
    headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Token {api_key}'
    }
    
    # Esegui la richiesta
    response = requests.get(url, headers=headers)

    # Verifica la risposta
    if response.status_code == 200:
        data = response.json()
        print(data)
    else:
        print("Errore:", response.status_code, response.text)

def tiingo_get_DAILY(ticker):
    import requests

    api_key = app.config["API_KEY"]
    

    # URL dell'endpoint per ottenere i price target e le valutazioni degli analisti
    url = f"https://api.tiingo.com/tiingo/daily/{ticker}/prices" 
    

    # header di autorizzazione per Tiingo
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Token {api_key}'
    }

    # Effettua la richiesta
    response = requests.get(url, headers=headers)

    # Controlla se la richiesta è andata a buon fine
    if response.status_code == 200:
        data = response.json()
        
        # Stampa i dati per il price target e le valutazioni degli analisti
        for entry in data:
            print(f"Date: {entry['date']}")
            print(f"Mean Price Target: {entry['meanPriceTarget']}")
            print(f"Median Price Target: {entry['medianPriceTarget']}")
            print(f"Low Price Target: {entry['lowPriceTarget']}")
            print(f"High Price Target: {entry['highPriceTarget']}")
            print(f"Number of Ratings: {entry['numRatings']}\n")
    else:
        print("Errore nella richiesta:", response.status_code, response.text)


def esegui_spider():
    from scrapy.crawler import CrawlerProcess
    from spiderman import MioSpider

    process = CrawlerProcess(settings={
        "FEEDS": {
            "risultati.json": {"format": "json"},
        },
    })
    process.crawl(MioSpider)
    process.start()  # Avvia lo spider e blocca fino alla fine della sua esecuzione
    
    
# Altre rotte possono essere aggiunte qui
# @app.route('/about')
# def about():
#     return render_template('about.html')

# Punto di ingresso
if __name__ == '__main__':
    app.run(debug=True)  #Note that we set debug=True so we don't have to reload our server each time we make a change in our code.