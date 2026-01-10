from argparse import ArgumentParser
import matplotlib.pyplot as plt
from datetime import datetime, timezone

from db import Velocity, Session

DATE_FORMAT = '%Y-%m-%d'


def plot_ticker(ticker: str, start_date: str, end_date: str):

    sd = datetime.strptime(start_date, DATE_FORMAT)
    ed = datetime.strptime(end_date, DATE_FORMAT)

    db_session = Session()

    data = db_session.query(Velocity).filter(
        (Velocity.utc_time >= sd) &
        (Velocity.utc_time <= ed) &
        (Velocity.ticker == ticker)).all()

    datetimes = [p.utc_time for p in data]
    price = [p.price for p in data]
    velocities10 = [p.v10 for p in data]
    velocities30 = [p.v30 for p in data]

    # print(datetimes)

    fig, ax1 = plt.subplots(figsize=(12, 6))

    color = 'tab:blue'
    ax1.set_xlabel('DateTime')
    ax1.set_ylabel('Price', color=color)
    ax1.plot(datetimes, price, '-', alpha=0.5, color=color)
    ax1.scatter(datetimes, price, s=5)
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('Velocity', color=color)
    ax2.tick_params(axis='y', color=color)
    ax2.plot(datetimes, velocities10, color=color)
    ax2.tick_params(axis='y', labelcolor=color)

    ax3 = ax1.twinx()
    color = 'tab:green'
    ax3.plot(datetimes, velocities30, color=color)

    plt.grid(True)
    plt.show()


if __name__ == '__main__':
    arg_parser = ArgumentParser()
    arg_parser.add_argument('--ticker', type=str, required=True)
    arg_parser.add_argument('--start-date', type=str, required=True)
    arg_parser.add_argument('--end-date', type=str, required=True)

    args = arg_parser.parse_args()

    plot_ticker(args.ticker, args.start_date, args.end_date)
