from argparse import ArgumentParser
import matplotlib.pyplot as plt
from datetime import datetime, timezone

from db import Price, Session

DATE_FORMAT = '%Y-%m-%d'


def plot_ticker(ticker: str, start_date: str, end_date: str):

    sd = datetime.strptime(start_date, DATE_FORMAT)
    ed = datetime.strptime(end_date, DATE_FORMAT)

    db_session = Session()

    prices = db_session.query(Price).filter(
        (Price.utc_time >= sd) &
        (Price.utc_time <= ed) &
        (Price.ticker == ticker)).all()

    datetimes = [p.utc_time for p in prices]
    values = [p.price for p in prices]

    plt.figure(figsize=(12, 6))
    plt.plot(datetimes, values, '-', alpha=0.5)
    plt.scatter(datetimes, values, s=5)
    plt.grid(True)
    plt.show()


if __name__ == '__main__':
    arg_parser = ArgumentParser()
    arg_parser.add_argument('--ticker', type=str, required=True)
    arg_parser.add_argument('--start-date', type=str, required=True)
    arg_parser.add_argument('--end-date', type=str, required=True)

    args = arg_parser.parse_args()

    plot_ticker(args.ticker, args.start_date, args.end_date)
