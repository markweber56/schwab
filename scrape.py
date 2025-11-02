import base64
import os
import requests
import time
import sys

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta

from db import Price, Security, Session
from redis_client import redis_client

TOKEN_URL = 'https://api.schwabapi.com/v1/oauth/token'
MARKET_DATA_URL = 'https://api.schwabapi.com/marketdata/v1/'

DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

PREVIOUS_PRICE_TIMES = {}

app_key = os.environ.get("SCHWAB_APPLICATION_KEY")
secret = os.environ.get("SCHWAB_APPLICATION_SECRET")

headers = {'Authorization': f'Basic {base64.b64encode(bytes(f"{app_key}:{secret}", "utf-8")).decode("utf-8")}', 'Content-Type': 'application/x-www-form-urlencoded'}


def milliseconds_to_cst(millis: int):
    t_utc = datetime.utcfromtimestamp(millis / 1000.0)
    t_cst = t_utc - timedelta(hours=5)
    return t_cst.strftime(DATE_FORMAT)


def milliseconds_to_utc(millis: int) -> datetime.utcfromtimestamp:
    return datetime.utcfromtimestamp(millis / 1000.0)


def create_log_message(msg: str, time_milliseconds: int):
    t_formatted = milliseconds_to_cst(time_milliseconds)
    return f"{t_formatted} - {msg}"


def get_refresh_token(refresh_token: str):
    data = {'grant_type': 'refresh_token', 'refresh_token': refresh_token}
    print(f'\n{datetime.utcnow()} ---------------------------------------------- Attempting to retrieve refresh token-----------------------------\n')

    response = requests.post('https://api.schwabapi.com/v1/oauth/token', headers=headers, data=data)
    status = response.status_code
    if status == 200:
        data = response.json()
        print(f"successfully retrieved token: {data['access_token']}")
        return data['access_token'], data['refresh_token']
    else:
        print(f"{status} - Failed to retrieve access token")
    return '', ''


def chunk_tickers(all_tickers: list[str], chunk_size: int = 10) -> list[list[str]]:
    '''
    Break list of tickers into list of list

    parameters
    ----------
        all_tickers: list[str]
            - list of tickers
        chunk_size: int
            - length of lists to breaks input length into
        
    returns
    -------
        List of lists of tickers

    '''
    all_tickers_length = len(all_tickers)
    chunks = []
    idx = 0
    while (idx + 1) * chunk_size < all_tickers_length:
        chunk = all_tickers[chunk_size * idx: chunk_size * (idx + 1)]
        chunks.append(chunk)
        idx += 1
    chunk = all_tickers[chunk_size * idx:]
    chunks.append(chunk)

    return chunks


def main():
    db_session = Session()
    # all securities in the S&P500 index
    securities = db_session.query(Security).all()
    last_prices = db_session.query(
        Price.ticker,
        func.max(Price.utc_time).label('previous_time')
        ).group_by(Price.ticker)

    # initialize previous price times
    for observation in last_prices:
        PREVIOUS_PRICE_TIMES[observation.ticker.replace('.', '/')] = observation.previous_time

    # tickers from stock.securities table
    all_tickers = [s.ticker.replace('.', '/') for s in securities]

    # limit to args length in GET request is 500, so split tickers into list of lists
    chunked_tickers = chunk_tickers(all_tickers, 25)

    refresh_token = redis_client.get('refresh_token').decode('utf-8')
    authorization_token = redis_client.get('access_token').decode('utf-8')

    refresh_time = datetime.utcnow() + timedelta(minutes=3)

    stop = False
    while not stop:
        now = datetime.utcnow()

        if (refresh_time - now) < timedelta(minutes=2):
            authorization_token, refresh_token = get_refresh_token(refresh_token)
            redis_client.set('access_token', authorization_token)
            refresh_time = now + timedelta(minutes=25)

        prices_to_commit = []
        # loop over chunks
        for chunk in chunked_tickers:

            args = f"symbols={','.join(chunk)}"

            response = requests.get(f'{MARKET_DATA_URL}/quotes?{args}', headers={'Authorization': f'Bearer {authorization_token}'})

            status_code = response.status_code
            chunk_prices = []

            if status_code == 200:
                data = response.json()
                for ticker in chunk:

                    # extract data for ticker from response data
                    ticker_data = data[ticker]

                    # extract time and price values
                    t_ms = ticker_data['quote']['quoteTime']
                    last_price = ticker_data['quote']['lastPrice']

                    t_utc = milliseconds_to_utc(t_ms)

                    if ticker in PREVIOUS_PRICE_TIMES:
                        if PREVIOUS_PRICE_TIMES[ticker] == t_utc:
                            print(f"Data retrieved for {ticker} matches the last record, removing {ticker} from query list")
                            PREVIOUS_PRICE_TIMES.pop(ticker)
                        else:
                            PREVIOUS_PRICE_TIMES[ticker] = t_utc
                            chunk_prices.append(Price(ticker=ticker.replace("/", '.'), utc_time=t_utc, price=last_price))
                            print(create_log_message(f"{ticker}: ${last_price}", t_ms))
                    else:
                        PREVIOUS_PRICE_TIMES[ticker] = t_utc
                        chunk_prices.append(Price(ticker=ticker.replace("/", '.'), utc_time=t_utc, price=last_price))
                        print(create_log_message(f"{ticker}: ${last_price}", t_ms))

            else:
                print(f"{status_code} - Failed to retrieve data")

            prices_to_commit.append(chunk_prices)
            
        try:
            db_session.add_all(sum(prices_to_commit, []))
            db_session.commit()
            print()
        except IntegrityError as x:
            print(x._message)
            sys.exit(1)

        all_tickers = list(PREVIOUS_PRICE_TIMES.keys())
        print(f'all tickers length: {len(all_tickers)}')
        if len(all_tickers) == 0:
            print("------------------------- NO MORE DATA TO FETCH, SHUTTING DOWN-------------------------------")
            sys.exit(0)

        chunked_tickers = chunk_tickers(all_tickers, 25)
        time.sleep(30)


if __name__ == '__main__':
    main()
