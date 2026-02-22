import os
import sys
import django
import csv
import yfinance as yf
from django.db import connection
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE","simps_project.settings")
django.setup()

Batch_size = 60

def fetch_symbols():
    with connection.cursor() as cursor:
        cursor.execute(''' SELECT equity_id, symbol
            FROM Global_Equities
        ''')
        return cursor.fetchall()

def read_symbols(csv_path):
    symbols = []
    with open(csv_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                symbols.append(row['symbol'])
    return symbols
        
def batch(iterable,n):
    for i in range(0,len(iterable),n):
        yield iterable[i:i+n]
    
def populate_prices(initial_symbols):
    today = datetime.today().date()
    for symbol_batch in batch(initial_symbols,Batch_size):
        data = yf.download(
            tickers = symbol_batch,
            period = '1d',
            interval = '1d',
            group_by = 'ticker',
            progress = False,
        )
        
        with connection.cursor() as cursor:
            for symbol in symbol_batch:
                try:
                    if len(symbol_batch)>1:
                        price = data[symbol]['Close'].iloc[-1]
                    else:
                        price = data['Close'].iloc[-1]
                    
                    if price is None:
                        continue

                    price = round(float(price),2)
                    info = yf.Ticker(symbol).info
                    print(symbol, info.get('regularMarketPrice'))
                    name = info.get('shortName') or 'Stock'
                    typ = info.get('sector') or ''
                    sector = info.get('sector') or ''

                    cursor.execute(""" INSERT INTO Global_Equities(symbol,equity_name,type,sector,current_price)
                                    VALUES (%s,%s,%s,%s,%s)                
                                """,[symbol,name,typ,sector,price])
                    

                    cursor.execute("SELECT equity_id, symbol FROM Global_Equities WHERE symbol = %s",[symbol] )
                    
            
                    equity_id = cursor.fetchone()[0]

                    cursor.execute(''' INSERT INTO Equity_Price_History (equity_id,price)
                                VALUES (%s,%s)
                                    ''',[equity_id,price])
                except Exception as e:
                    print(f"failed this{e}")
        connection.commit()
            


def update_prices():
    today = datetime.today().date()
    equities = fetch_symbols()
    
    if not equities:
        print("No Equities Found, populating")
        csv_path = os.path.join(os.path.dirname(__file__), 'symbols.csv')
        initial_symbols=read_symbols(csv_path)
        populate_prices(initial_symbols)
        return
    
    equity_map = {symbol: eid for eid, symbol in equities}    
    symbols = [symbol for _, symbol in equities]

    for symbol_batch in batch(symbols,Batch_size):
        data = yf.download(
            tickers = symbol_batch,
            period = '1d',
            interval = '1d',
            group_by = 'ticker',
            progress = False,
        )

        with connection.cursor() as cursor:
            for symbol in symbol_batch:
                try:
                    if len(symbol_batch)>1:
                        price = data[symbol]['Close'].iloc[-1]
                    else:
                        price = data['Close'].iloc[-1]
                    
                    if price is None:
                        continue 

                    price = round(float(price),2)
                    equity_id = equity_map[symbol]

                    cursor.execute(''' UPDATE Global_Equities
                        SET current_price = %s, last_updated = NOW()
                        WHERE equity_id = %s
                    ''', [price, equity_id])

                    cursor.execute(''' INSERT INTO Equity_Price_History (equity_id, price)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                    ''', [equity_id, price])

                except Exception as e:
                    print(e)
        connection.commit()


def main():
    update_prices()
    print("Done")

if __name__=="__main__":
    main()