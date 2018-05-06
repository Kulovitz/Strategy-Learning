"""MC2-P1: Market simulator."""

from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import datetime as dt
import os
from util import get_data, plot_data

def compute_portvals(orders, symbol, start_val = 100000, start = dt.datetime(2010, 1, 1), end = dt.datetime(2010, 12, 31)):
    orders['Symbol'] = 'JPM'
    orders['Action'] = 'BUY'
    for j, row in orders.iterrows():
        if orders.loc[j, 'Shares'] < 0:
            orders.loc[j,'Action'] = 'SELL'
    orders = orders[orders.Shares != 0]
    orders['Shares'] = orders['Shares'].abs()
    orders.index.name = 'Date'
    print orders
    date2 = pd.date_range(start, end)
    prices = get_data(symbol, date2)
    prices = prices[symbol]
    prices = prices.assign(Cash = start_val)
    trades = prices.copy()
    trades[0:] = 0.0
    holdings = pd.DataFrame
    values = pd.DataFrame
    j = 0
    for i, date in orders.iterrows():
        symbol = orders['Symbol'][i]
        order = orders['Action'][i]
        shares = orders['Shares'][i]
        adjclose = prices.ix[i][symbol]
        # Added in correction phase to calculate transaction costs
        trades.loc[i, 'Cash'] -= 9.95
        market_cut = float("{:.3f}".format(.005*(adjclose*shares)))
        trades.loc[i, 'Cash'] -= market_cut
        #
        if order == "SELL":
            trades.ix[i][symbol] = trades.ix[i][symbol] - shares
            trades.ix[i]['Cash'] = trades.ix[i]['Cash'] + adjclose * shares
            j = j + 1
        if order == "BUY":
            trades.ix[i][symbol] = trades.ix[i][symbol] + shares
            trades.ix[i]['Cash'] = trades.ix[i]['Cash'] - adjclose * shares
            j = j + 1

#    print trades

    holdings = trades.copy()
    holdings[1:] = 0.0
    holdings['Cash'][0] = start_val

    holdings['Cash'][0] = holdings['Cash'][0] + trades['Cash'][0]
    for i in range(1, len(holdings)):
        holdings.iloc[i,:] = holdings.iloc[i-1,:] + trades.iloc[i,:]
   # print "==============HOLDINGS============"
   # print holdings
    prices['Cash'][0:] = 1.0
    values = holdings.copy()
    values = prices*holdings
   # print "============VALUES============"
   # print values
    port_val = values.sum(axis=1).to_frame()
    port_val = port_val.rename(columns = {0: 'portval'})
   # print "======= PORT VAL ======="
   # print port_val
    cr, adr, sddr, sr = compute_portfolio_stats(port_val, 0.0, 252.0)
    return port_val

def compute_daily_returns(df):
    daily_returns = df.copy()
    daily_returns[1:] = (df[1:]/df[:-1].values) - 1
    daily_returns[0] = 0
    return daily_returns

def compute_portfolio_stats(prices, rfr, sf):
    cr = prices.loc[prices.last_valid_index()] - prices.loc[prices.first_valid_index()]/(prices.loc[prices.first_valid_index()])
    adr = compute_daily_returns(prices).mean()
    daily_returns = compute_daily_returns(prices)
    sddr = daily_returns[1:].std()
    sr = np.sqrt(sf) * adr/sddr;
    return cr, adr, sddr, sr


def test_code():
    # this is a helper function you can use to test your code
    # note that during autograding his function will not be called.
    # Define input parameters

    of = "./orders/ordersQ.csv"
    sv = 100000
    sd = dt.datetime(2009, 1, 1)
    ed = dt.datetime(2009, 12, 31)
    # Process orders
    portvals = compute_portvals(orders_file = of, start_val = sv, start = sd, end = ed)
    if isinstance(portvals, pd.DataFrame):
        portvals = portvals[portvals.columns[0]] # just get the first column
    else:
        "warning, code did not return a DataFrame"

    # Get portfolio stats
    # Here we just fake the data. you should use your code from previous assignments.

    normalized_port_val = portvals/portvals[0]
   # print portvals
   # print normalized_port_val
    dates = pd.date_range(sd, ed)
    spy = get_data(['SPY'], dates)
   # print "=====SPY======"
   # print spy
    spy = spy.rename(columns = {0: 'SPY'})
    spy = spy['SPY']
    cr, adr, sddr, sr = compute_portfolio_stats(normalized_port_val, 0.0, 252)
    cum_ret_SPY, avg_daily_ret_SPY, std_daily_ret_SPY, sharpe_ratio_SPY = compute_portfolio_stats(spy,0.0,252)

    # Compare portfolio against $SPX
    print "Date Range: {} to {}".format(sd, ed)
    print
    print "Sharpe Ratio of Fund: {}".format(sr)
    print "Sharpe Ratio of SPY : {}".format(sharpe_ratio_SPY)
    print
    print "Cumulative Return of Fund: {}".format(cr)
    print "Cumulative Return of SPY : {}".format(cum_ret_SPY)
    print
    print "Standard Deviation of Fund: {}".format(sddr)
    print "Standard Deviation of SPY : {}".format(std_daily_ret_SPY)
    print
    print "Average Daily Return of Fund: {}".format(adr)
    print "Average Daily Return of SPY : {}".format(avg_daily_ret_SPY)
    print
    print "Final Portfolio Value: {}".format(portvals[-1])

if __name__ == "__main__":
    test_code()
