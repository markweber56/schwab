import base64
import os
import sys
import time
from datetime import datetime, timedelta

import pytz
import requests
from redis_client import redis_client
from sqlalchemy import func

from db import Price, Security, Session

TOKEN_URL = 'https://api.schwabapi.com/v1/oauth/token'
MARKET_DATA_URL = 'https://api.schwabapi.com/marketdata/v1/'

DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
EASTERN_TIME_ZONE = pytz.timezone('America/New_York')
CENTRAL_TIME_ZONE = pytz.timezone('America/Chicago')

PREVIOUS_PRICE_TIMES = {}

app_key = os.environ.get("SCHWAB_APPLICATION_KEY")
secret = os.environ.get("SCHWAB_APPLICATION_SECRET")

headers = {'Authorization': f'Basic {base64.b64encode(bytes(f"{app_key}:{secret}", "utf-8")).decode("utf-8")}', 'Content-Type': 'application/x-www-form-urlencoded'}


def is_before_close():
    current_time = datetime.now(EASTERN_TIME_ZONE)

    end_time = current_time.replace(hour=15, minute=30)

    return current_time < end_time


def format_time(t: datetime, date_format: str, time_zone) -> str:
    return t.astimezone(time_zone).strftime(date_format)


def milliseconds_to_utc(millis: int) -> datetime.utcfromtimestamp:
    return datetime.utcfromtimestamp(millis / 1000.0)


def create_log_message(msg: str, time_zone):
    t_formatted = format_time(datetime.now(pytz.UTC), '%Y-%m-%d %H:%M:%S', time_zone)
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
        # print(f'{observation.ticker.replace(".", "/")} - {observation.previous_time}')
        PREVIOUS_PRICE_TIMES[observation.ticker.replace('.', '/')] = observation.previous_time

    # tickers from stock.securities table
    all_tickers = [s.ticker.replace('.', '/') for s in securities]

    # limit to args length in GET request is 500, so split tickers into list of lists
    chunked_tickers = chunk_tickers(all_tickers, 25)

    refresh_token = redis_client.get('refresh_token').decode('utf-8')
    authorization_token, refresh_token = get_refresh_token(refresh_token)
    redis_client.set('access_token', authorization_token)
    redis_client.set('refresh_token', refresh_token)
    refresh_time = datetime.utcnow() + timedelta(minutes=25)

    while True:
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

            if status_code == 200:
                data = response.json()
                for ticker in chunk:

                    # extract data for ticker from response data
                    ticker_data = data[ticker]

                    # extract time and price values
                    t_ms = ticker_data['quote']['quoteTime']
                    last_price = ticker_data['quote']['lastPrice']

                    t_utc = milliseconds_to_utc(t_ms)

                    is_regular_trading_hours = is_before_close()

                    # if ticker in PREVIOUS_PRICE_TIMES:
                    previous_time = PREVIOUS_PRICE_TIMES[ticker]
                    PREVIOUS_PRICE_TIMES[ticker] = t_utc

                    print(create_log_message(f"{ticker}: ${last_price}", CENTRAL_TIME_ZONE))

                    # check for repeat values
                    if previous_time >= t_utc:
                        if not is_regular_trading_hours:
                            print(f"Data retrieved for {ticker} matches the last record, removing {ticker} from query list")
                            PREVIOUS_PRICE_TIMES.pop(ticker)
                    # add record to records to commit
                    else:
                        prices_to_commit.append(Price(ticker=ticker.replace("/", '.'), utc_time=t_utc, price=last_price))

            else:
                print(f"{status_code} - Failed to retrieve data")

        try:
            db_session.add_all(prices_to_commit)
            db_session.commit()
            print()
        except Exception as x:
            print(x.__str__)

        all_tickers = list(PREVIOUS_PRICE_TIMES.keys())
        print(f'all tickers length: {len(all_tickers)}')
        if len(all_tickers) == 0:
            print("------------------------- NO MORE DATA TO FETCH, SHUTTING DOWN-------------------------------")
            sys.exit(0)

        chunked_tickers = chunk_tickers(all_tickers, 25)
        time.sleep(30)


if __name__ == '__main__':
    main()
