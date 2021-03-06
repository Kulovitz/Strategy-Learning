import datetime as dt
import QLearner as ql
import pandas as pd
import util as ut
import ordersmarketsim as ms
import matplotlib.pyplot as plt

class StrategyLearner(object):
    # constructor
    def __init__(self, verbose = False, impact = 0.00):
        self.verbose = verbose
        self.impact = impact
        self.learner = ql.QLearner(num_states = 1000, num_actions = 4, alpha = .02, gamma = 0.9, rar = .5, radr = .99, dyna = 0, verbose = False)
    # this method should create a QLearner, and train it for trading
    def addEvidence(self, symbol = "JPM", \
        sd=dt.datetime(2008,1,1), \
        ed=dt.datetime(2009,1,1), \
        sv = 100000):
        window = 20

        # add your code to do learning here
        # Look
        N = 20
        K = 2 * N
        sd_original = sd
        sd = sd - dt.timedelta(K)


        # example usage of the old backward compatible util function
        cash = sv
        syms=[symbol]
        dates = pd.date_range(sd, ed)
        prices_all = ut.get_data(syms, dates)  # automatically adds SPY
        prices = prices_all[syms]  # only portfolio symbols
        prices_SPY = prices_all['SPY']  # only SPY, for comparison later

        if self.verbose: print prices


        #Indicators
        normalized_prices = self.normalize_prices(prices)
        prices_sma = self.SMA(normalized_prices, window)
        momentum = self.Momentum(normalized_prices, window)
        daily_rets = self.daily_returns(normalized_prices)
        bollinger_bands = self.bollingerBands(normalized_prices, window)
        bbp = pd.DataFrame(0, index = normalized_prices.index, columns = ['bbp'])
        bbp['bbp'] = (normalized_prices[symbol] - bollinger_bands['lower_band'])/(bollinger_bands['upper_band'] - bollinger_bands['lower_band'])
        indicators = pd.concat([prices_sma, momentum, bbp['bbp']], axis=1)

        indicators = indicators.loc[sd_original:]
        normalized_prices = normalized_prices.loc[sd_original:]
        #print indicators
        indicators = self.discretize(indicators)

        starting_state = indicators.iloc[0]['State']
        self.learner.querysetstate(int(float(starting_state)))

        book = self.simulate(indicators, normalized_prices, daily_rets, symbol, learning = True)
        #print book


    # this method should use the existing policy and test it against new data
    def testPolicy(self, symbol = "JPM", \
        sd=dt.datetime(2010,1,1), \
        ed=dt.datetime(2011,1,1), \
        sv = 100000):
        window = 20
        N = 20
        K = 2 * N
        sd_original = sd
        sd = sd - dt.timedelta(K)


        # example usage of the old backward compatible util function
        cash = sv
        syms=[symbol]
        dates = pd.date_range(sd, ed)
        prices_all = ut.get_data(syms, dates)  # automatically adds SPY
        prices = prices_all[syms]  # only portfolio symbols
        prices_SPY = prices_all['SPY']  # only SPY, for comparison later



        #Indicators
        normalized_prices = self.normalize_prices(prices)
        prices_sma = self.SMA(normalized_prices, window)
        momentum = self.Momentum(normalized_prices, window)
        daily_rets = self.daily_returns(normalized_prices)
        bollinger_bands = self.bollingerBands(normalized_prices, window)
        bbp = pd.DataFrame(0, index = normalized_prices.index, columns = ['bbp'])
        bbp['bbp'] = (normalized_prices[symbol] - bollinger_bands['lower_band'])/(bollinger_bands['upper_band'] - bollinger_bands['lower_band'])
        indicators = pd.concat([prices_sma, momentum, bbp['bbp']], axis=1)

        indicators = indicators.loc[sd_original:]
        normalized_prices = normalized_prices.loc[sd_original:]
        #print indicators
        indicators = self.discretize(indicators)

        starting_state = indicators.iloc[0]['State']
        self.learner.querysetstate(int(float(starting_state)))

        book = self.simulate(indicators, normalized_prices, daily_rets, symbol, learning = False)
#        print book

        return book

    def daily_returns(self, prices):
        daily_returns = prices.copy()
        daily_returns[1:] = (prices[1:] / prices[:-1].values)-1
        return daily_returns

    def normalize_prices(self, prices):
        prices.fillna(method='ffill', inplace = True)
        prices.fillna(method='bfill', inplace = True)
        return prices / prices.ix[0,:]

    def SMA(self, normalized_prices, window):
        sma = pd.DataFrame(0, index = normalized_prices.index, columns = ['SMA'])
        sma['SMA'] = normalized_prices.rolling(window=window).mean()
        return sma

    def bollingerBands(self, normalized_prices, window):
        rolling_std = pd.rolling_std(normalized_prices, window=window)
        rolling_avg = pd.rolling_mean(normalized_prices, window=window)
        upper_band = rolling_avg + ( 2 * rolling_std)
        lower_band = rolling_avg - ( 2 * rolling_std)
        bollinger_bands = pd.DataFrame(0, index = normalized_prices.index, columns = ['lower_band','upper_band'])
        bollinger_bands['lower_band'] = lower_band
        bollinger_bands['upper_band'] = upper_band
        return bollinger_bands


    def Momentum(self, normalized_prices, window):
        momentum = pd.DataFrame(0, index = normalized_prices.index, columns = ['momentum'])
        momentum['momentum'] = normalized_prices.diff(window)/normalized_prices.shift(window)
        return momentum

    def discretize(self, indicators):
        momentum_bins = [-1, -0.8, -0.6, -0.4, -0.2, 0, 0.2, 0.4, 0.6, 0.8, 1]
        bbp_bins = [-2, -1.6, -1.2, -0.8, -0.4, 0, 0.4, 0.8, 1.2, 1.6, 2]
        sma_bins = [0, 0.2, 0.4, 0.6, 0.8, 1, 1.2, 1.4, 1.6, 1.8, 2]
        labels = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        indicators['sma_state'] = pd.cut(indicators['SMA'], sma_bins, labels=labels)
        indicators['momentum_state'] = pd.cut(indicators['momentum'], momentum_bins, labels=labels)
        indicators['bbp_state'] = pd.cut(indicators['bbp'], bbp_bins, labels=labels)
        indicators = indicators.drop('SMA', axis=1)
        indicators = indicators.drop('momentum', axis=1)
        indicators = indicators.drop('bbp', axis=1)
        indicators['State'] = indicators['sma_state'].astype(str) + indicators['momentum_state'].astype(str) + indicators['bbp_state'].astype(str)

        indicators = indicators.drop('bbp_state', axis=1)
        indicators = indicators.drop('sma_state', axis=1)
        indicators = indicators.drop('momentum_state', axis=1)
        return indicators

    def simulate(self, indicators, normalized_prices, daily_returns, symbol, learning):
        orders = pd.DataFrame(0, index = normalized_prices.index, columns=['Shares'])
        actions = pd.DataFrame('BUY', index = normalized_prices.index, columns=['Action'])
        symbols = pd.DataFrame(symbol, index = normalized_prices.index, columns=['Symbol'])

        book = pd.concat([symbols, actions, orders], axis=1)
        book.columns = ['Symbol', 'Action', 'Shares']
        copy = book.copy()

        iterations = 0
        while iterations < 500:
            total_holdings = 0
            iterations += 1
            reward = 0

            if (iterations > 20) and (book.equals(copy)):
                break
            copy = book.copy()
            for i, row in normalized_prices.iterrows():
                reward = total_holdings * daily_returns.loc[i] * (1 - self.impact)
                if (learning == True):
                    a = self.learner.query(int(float(indicators.loc[i]['State'])), reward)
                elif (learning == False):
                    a = self.learner.querysetstate(int(float(indicators.loc[i]['State'])))

                if (a == 0) and (total_holdings <= 0):
                    actions.loc[i]['Action'] = 'BUY'
                    orders.loc[i]['Shares'] = 1000
                    total_holdings += 1000
                elif (a == 1) and (total_holdings < 0):
                    actions.loc[i]['Action'] = 'BUY'
                    orders.loc[i]['Shares'] = 2000
                    total_holdings += 2000
                elif (a == 2) and (total_holdings >= 0):
                    actions.loc[i]['Action'] = 'SELL'
                    orders.loc[i]['Shares'] = -1000
                    total_holdings = total_holdings - 1000
                elif (a == 3) and (total_holdings > 0):
                    actions.loc[i]['Action'] = 'SELL'
                    orders.loc[i]['Shares'] = -2000
                    total_holdings = total_holdings - 2000

            book = pd.concat([symbols, actions, orders], axis=1)
            book.columns = ['Symbol', 'Action', 'Shares']
            book = book.drop('Symbol', axis=1)
            book = book.drop('Action', axis=1)
#            book['Shares'].last_valid_index() = book['Shares'].sum()

            return book

    def printResults(self, port_vals, sd, ed):
        dates = pd.date_range(sd,ed)
        port_vals = port_vals['portval']
        normalized_port_vals = port_vals/port_vals[0]
        spy = ut.get_data(['SPY'], dates)
        spy = spy.rename(columns = {0: 'SPY'})
        spy = spy['SPY']
        spy = spy/spy[0]
        cr, adr, sddr, sr = ms.compute_portfolio_stats(normalized_port_vals, 0.0, 252)
        cum_ret_SPY, avg_daily_ret_SPY, std_daily_ret_SPY, sharpe_ratio_SPY = ms.compute_portfolio_stats(spy,0.0,252)
        final_val = port_vals[-1]

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
        print "Final Portfolio Value: ${}".format(final_val)

    def getBenchmark(self, book):
        benchmark_orders = pd.DataFrame(0, index=book.index, columns = ['Shares'])
        benchmark_orders['Shares'][1] = 1000
        benchmark_orders['Shares'][-1:] = -1000
        print benchmark_orders
        return benchmark_orders

if __name__=="__main__":
    early_sd = dt.datetime(2005,1,1)
    sd = dt.datetime(2010,1,1)
    ed = dt.datetime(2011,1,1)
    symbol = 'JPM'
    sl = StrategyLearner(impact=0.0)
    sl.addEvidence(sd = sd, ed = ed)
    book = sl.testPolicy()
    benchmark_orders = sl.getBenchmark(book)
    port_vals = ms.compute_portvals(book, [symbol], 100000, sd, ed)
    benchmark_vals = ms.compute_portvals(benchmark_orders, [symbol], 100000, sd, ed)

    o1 = port_vals['portval']
    o2 = benchmark_vals['portval']
    concat = pd.concat([o1, o2], axis=1)
    concat.columns = ['Portfolio','Benchmark']
    concat.plot(title="Portfolio Value vs Benchmark Value", use_index=True, color = ['Green','Orange'], grid=True)
    #####IMPACT TEST#####
    slImpact = StrategyLearner(impact = .05)
    slImpact.addEvidence(sd = sd, ed = ed)
    bookImpact = slImpact.testPolicy()
    bookImpact_portvals = ms.compute_portvals(bookImpact, [symbol], 100000, sd, ed)
    i1 = bookImpact_portvals['portval']
    impactConcat = pd.concat([o1, i1], axis=1)
    impactConcat.columns = ['No Impact', 'Impact']
    impactConcat.plot(title="No Impact vs Impact", use_index=True, color = ['Green','Orange',], grid=True)
    ##### Leaning Time ####

    long_term_sl = StrategyLearner(impact = 0.0)
    long_term_sl.addEvidence(sd = early_sd, ed = ed)
    long_term_book = long_term_sl.testPolicy()
    long_term_book_portvals = ms.compute_portvals(long_term_book, [symbol], 100000, sd , ed)
    lt1 = long_term_book_portvals['portval']
    ltconcat = pd.concat([o1, lt1], axis=1)
    ltconcat.columns = ['1yr Learning Time', '6yr Learning Time']
    ltconcat.plot(title="Short Term Learning vs Long Term Learning", use_index=True, color=['Green','Orange'], grid=True)

    print "####### STRATEGY LEARNER PORTFOLIO #######"
    sl.printResults(port_vals, sd, ed)
    print "####### BENCHMARK #######"
    sl.printResults(benchmark_vals, sd, ed)
    print "#######  .05 MARKET IMPACT ########"
    sl.printResults(bookImpact_portvals, sd, ed)
    print "#######  LONG TERM LEARNING PORTFOLIO #######"
    sl.printResults(long_term_book_portvals, sd, ed)

    #benchmark_vals.plot(title="Benchmark Portfolio Value", use_index=True, color='Green')
    plt.show()
