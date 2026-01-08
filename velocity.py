# from argparse import ArgumentParser
# import matplotlib.pyplot as plt
from datetime import datetime, timezone
from sqlalchemy import func

from db import Price, Session, Velocity

DATE_FORMAT = '%Y-%m-%d'
DAY_0 = datetime(2000, 1, 1)


def datetime_to_int(datetime_val):
    return (datetime_val - DAY_0).total_seconds()


def velocity(time_data, price_data, starting_price):
    n = len(time_data)

    time_data_normalized = [t - time_data[0] for t in time_data]
    sum_time = sum(time_data_normalized)
    sum_price = sum(price_data)

    sum_time_price = sum(ti * pi for ti, pi in zip(time_data_normalized, price_data))
    sum_time_squred = sum(ti * ti for ti in time_data_normalized)

    numerator = n * sum_time_price - sum_time * sum_price
    denominator = n * sum_time_squred - sum_time * sum_time

    return ((numerator / denominator) / starting_price) * 1000000
    


def main():

    db_session = Session()

    ticker = 'AMZN'

    ticker_query = db_session.query(
        Price.ticker
    ).distinct()

    tickers = [t[0] for t in ticker_query]

    for ticker in tickers:
        print(f'Generating velocity data for {ticker}')

        distinct_dates = db_session.query(
            func.date(Price.utc_time)
        ).filter(
            Price.ticker == ticker
        ).filter(
            func.date(Price.utc_time) > datetime(2025, 10, 31)
        ).distinct().order_by(
            func.date(Price.utc_time)
        ).all()

        dates = [date[0] for date in distinct_dates]

        for date in dates:
            velocity_data = []

            price_data = db_session.query(Price).filter(
                Price.ticker == ticker,
                func.date(Price.utc_time) == date
            ).order_by(Price.utc_time).all()

            # print(len(price_data))

            # zero_price = price_data[0]
            # print(type(zero_price))
            # print(zero_price.price)
            # print(type(zero_price.utc_time))
            # print(datetime_to_int(zero_price.utc_time))
            t = [datetime_to_int(pd.utc_time) for pd in price_data]
            p = [pd.price for pd in price_data]
            p0 = p[0]

            NUM_POINTS = 10

            for i in range(len(t)):
                v3 = 0
                v5 = 0
                v10 = 0
                if i > 2:
                    v3 = velocity(t[i-3:i], p[i-3:i], p0)
                if i > 4:
                    v5 = velocity(t[i-5:i], p[i-5:i], p0)
                if i > NUM_POINTS - 1:
                    v10 = velocity(t[i-NUM_POINTS:i], p[i-NUM_POINTS:i], p0)
                # print(f'{v3}, {v5}, {v10}')

                velocity_data.append(
                    Velocity(
                      ticker=ticker,
                      utc_time=price_data[i].utc_time,
                      price=price_data[i].price,
                      v3=v3,
                      v5=v5,
                      v10=v10
                    )
                )

            db_session.add_all(velocity_data)
            db_session.commit()

    db_session.close()

if __name__ == '__main__':
    main()
