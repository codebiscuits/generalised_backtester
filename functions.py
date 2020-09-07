from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patch
from matplotlib.lines import Line2D
import math
import statistics
import time
from finta import TA
from finta.utils import resample
import multiprocessing

### define functions

def create_pairs_list(quote, source='ohlc'):
    if source == 'ohlc':
        stored_files_path = Path(f'V:/ohlc_data/')
        files_list = list(stored_files_path.glob(f'*{quote}-1m-data.csv'))
        pairs = [str(pair)[13:-12] for pair in files_list]
    else:
        folders_list = list(source.iterdir())
        pairs = [str(pair.stem) for pair in folders_list]


    return pairs

### get_dates calculates the index numbers for slicing the ohlc data to feed into the walk-forward testing function
def get_dates(counter, long, short, set):
    if set == 'train':
        from_date = counter * short
        to_date = from_date + long + 1
    elif set == 'test':
        from_date = counter * short + long
        to_date = from_date + short + 1
    return from_date, to_date

### load ohlc data, returns two lists; price (ohlcv, close or avg) and volume
def load_data(pair, mode='ohlcv'):
    filepath = Path(f'V:/ohlc_data/{pair}-1m-data.csv')
    data = pd.read_csv(filepath, index_col=0)

    data.index = pd.to_datetime(data.index)

    data['avg_price'] = (data['open'] + data['high'] + data['low'] + data['close']) / 4
    close_price = list(data['close'])
    avg_price = list(data['avg_price'])  # In live trading, this data can only be known at the close of each period. Potential source of look-ahead bias

    vol = list(data['volume'])

    if mode == 'ohlcv':
        ohlcv_data = data[['open', 'high', 'low', 'close', 'volume']]
        return ohlcv_data, vol
    if mode == 'close':
        return close_price, vol
    if mode == 'avg':
        return avg_price, vol

### takes in 1min price data and returns 5min, 15min, 30min, 1h, 4h, 12h, 1d, 3d, 1w price(ohlcv, close, mean or median) data
def resample_ohlc(price, vol, scale, mode='ohlcv'):
    timescales = {'5min': 5, '15min': 15, '30min': 30, '1h': 60, '4h': 240, '12h': 720, '1d': 1440, '3d': 4320, '1w': 10080}
    t = timescales.get(scale)

    if mode == 'ohlcv':
        new_price = resample(price, scale)
        new_vol = list(new_price.volume)

    if mode == 'close':
        new_price = []
        new_vol = []
        for i in range(int(len(price) / t)):
            pos = i * t
            p = price[pos + t - 1]
            new_price.append(p)
            v = sum(vol[pos:pos + t])
            new_vol.append(v)
    if mode == 'mean':
        new_price = []
        new_vol = []
        for i in range(int(len(price) / t)):
            pos = i * t
            p = statistics.mean(price[pos:pos + t])
            new_price.append(p)
            v = sum(vol[pos:pos + t])
            new_vol.append(v)
    if mode == 'median':
        new_price = []
        new_vol = []
        for i in range(int(len(price) / t)):
            pos = i * t
            p = statistics.median(price[pos:pos + t])
            new_price.append(p)
            v = sum(vol[pos:pos + t])
            new_vol.append(v)

    return new_price, new_vol

### Hull moving average
def hma_calc(price, length):
    return TA.HMA(price, length)

### currently returns a list of tuples containing signals: (index, b/s, price)
def hma_strat(price, length):
    hma = list(hma_calc(price, length))
    signals = []
    for i in range(len(price)):
        if hma[i] > hma[i-2] and hma[i-1] > hma[i-3]:
            signal = (i, 'b', price)
            signals.append(signal)
        if hma[i] < hma[i-2] and hma[i-1] < hma[i-3]:
            signal = (i, 's', price)
            signals.append(signal)

    return signals

# TODO i need to make a new hma_strat_forward to implement the variable length param,
#  and then finish updating forward_run and forward_run_all to fit them to this code

### backtest a single set of params
def single_backtest(price, length):
    printout = False
    vol = list(price.loc[:, 'volume'])
    # print(price.columns)

    startcash = 1000
    cash = startcash
    asset = 0
    fees = 0.00075
    comm = 1 - fees
    close_list = list(price['close'])
    equity_curve = []
    trade_list = []
    position = None

    start_signals = time.perf_counter()
    signals = hma_strat(price, length)
    if printout:
        print(f'Signals: {len(signals)}')
    end_signals = time.perf_counter()
    seconds = round(end_signals - start_signals)
    # print(f'Generating signals for length {length} took: {seconds // 60} minutes, {seconds % 60} seconds')

    # counter = 0
    for i in range(len(signals)):
        # old_counter = counter
        # counter = round(100 * i / len(signals))
        # if counter %10 == 0 and old_counter != counter:
        #     print(f'{counter}% completed')
        ohlc_limit = signals[i + 1][0] if i < (len(signals) - 1) else signals[-1][0]  # no slippage allowed past the next signal
        sell_condition = signals[i][1] == 's' and position == 'long'
        buy_condition = signals[i][1] == 'b' and position == 'short'
        initial_sell_cond = signals[i][1] == 's' and position == None
        initial_buy_cond = signals[i][1] == 'b' and position == None
        if printout:
            print('-' * 80)
            print(f'i: {i}')
            print(f'price index: {signals[i][0]}')
        ### initial sell condition won't be useful until ive implemented shorting logic
        # if initial_sell_cond: # if the last 'num' bricks were red and preceded by none
        #     ohlc_index = signals[i][0] + 1
        #     print(f'ohlc_index before: {ohlc_index}') ####
        #     trade_vol = 0
        #     cash = comm * asset * close_list[i]
        #     while trade_vol < cash and ohlc_index < (len(close_list)-1 and ohlc_limit):
        #         trade_vol += vol[ohlc_index]
        #         trade_vol /= 2 # volume figures are for buys and sells combined, i can only draw on half the liquidity
        #         ohlc_index += 1
        #     print(f'ohlc_index after: {ohlc_index}, trade_vol: {trade_vol}, cash: {cash}')
        #     cash = comm * asset * price[ohlc_index]
        #     equity_curve.append(cash)
        #     if printout:
        #         print(f'sold {asset:.2f} units at {price[ohlc_index]}, commision: {(fees * cash):.3f}')
        #     trade_list.append((i, 's', price[ohlc_index]))  # record a sell signal
        #     position = 'short'
        if initial_buy_cond and signals[i][0] + 2 < len(close_list):  # if the last 'num' bricks were green and preceded by none
            ohlc_index = signals[i][0] + 1
            how_many = 0  # for recording how many ohlc periods it takes to fill the order
            if printout:
                print(f'ohlc_index before: {ohlc_index}')
            trade_vol = 0
            asset = cash * comm / close_list[i] # initial calculation for position size
            cash_value = comm * asset * close_list[i]  # position is in base currency but volume is given in quote
            while trade_vol < cash_value and ohlc_index < len(close_list) - 1 and ohlc_index < ohlc_limit:
                try:
                    trade_vol += vol[ohlc_index]
                except IndexError:
                    print(f'len(vol): {len(vol)}, ohlc_index: {ohlc_index}')
                trade_vol /= 2  # volume figures are for buys and sells combined, i can only draw on half the liquidity
                ohlc_index += 1
                how_many += 1
            if printout:
                print(f'ohlc_index after: {ohlc_index}, trade_vol: {trade_vol}, cash: {cash}')
            asset = cash * comm / close_list[ohlc_index] # true trade price accounting for liquidity
            if printout:
                print(f'bought {asset:.2f} units at {close_list[ohlc_index]}, commision: {(fees * cash):.3f}')
            trade_list.append((i, 'b', close_list[ohlc_index], ohlc_index, how_many))  # record a buy signal
            position = 'long'
        if sell_condition and signals[i][0] + 2 < len(close_list):  # if the last 'num' bricks were red and preceded by a green
            if signals[i][0] + 1 < len(close_list):
                ohlc_index = signals[i][0] + 1  # this line causes out of index error on its own
                how_many = 0
            else:
                break
            if printout:
                print(f'ohlc_index before: {ohlc_index}') ####
            trade_vol = 0
            cash = comm * asset * close_list[i]
            mins = 1
            while trade_vol < cash and ohlc_index < len(close_list) - 1 and ohlc_index < ohlc_limit:
                mins += 1
                trade_vol += vol[ohlc_index] / 2  # volume figures are for buys and sells combined, i can only draw on half the liquidity
                ohlc_index += 1
                how_many += 1
            if printout:
                print(f'ohlc_index after: {ohlc_index}, trade_vol: {trade_vol}, cash: {cash}')
            cash = comm * asset * close_list[ohlc_index]
            equity_curve.append(cash)
            if printout:
                print(f'sold {asset:.2f} units at {close_list[ohlc_index]}, commision: {(fees * cash):.3f}')
            trade_list.append((i, 's', close_list[ohlc_index], ohlc_index, how_many))  # record a sell signal
            position = 'short'
        if buy_condition and signals[i][0] + 2 < len(close_list):  # if the last 'num' bricks were green and preceded by a red
            if signals[i][0] + 1 < len(close_list):
                ohlc_index = signals[i][0] + 1  # this line causes out of index error on its own
                how_many = 0
            else:
                break
            if printout:
                print(f'ohlc_index before: {ohlc_index}') ####
            trade_vol = 0
            asset = cash * comm / close_list[i]
            cash_value = comm * asset * close_list[i]  # position is in base currency but volume is given in quote
            mins = 1
            while trade_vol < cash_value and ohlc_index < len(close_list) - 1 and ohlc_index < ohlc_limit:
                mins += 1
                trade_vol += vol[ohlc_index] / 2  # volume figures are for buys and sells combined, i can only draw on half the liquidity
                ohlc_index += 1
                how_many += 1
            if printout:
                print(f'ohlc_index after: {ohlc_index}, trade_vol: {trade_vol}, cash: {cash}')
            asset = cash * comm / close_list[ohlc_index]
            if printout:
                print(f'bought {asset:.2f} units at {close_list[ohlc_index]}, commision: {(fees * cash):.3f}')
            trade_list.append((i, 'b', close_list[ohlc_index], ohlc_index, how_many))  # record a buy signal
            position = 'long'
        if printout:
            if equity_curve:
                print(equity_curve[-1])
    if printout:
        print(f'Number of trades: {len(trade_list)}')

    return {'length': length, 'equity curve': equity_curve, 'trades': trade_list}

### backtests a range of settings
def optimise_backtest(price, length_range, printout=False):
    lengths_list = []
    trades_array = []
    eq_curves = []
    for length in range(*length_range):
        if printout:
            print(f'testing length: {length}')
        backtest = single_backtest(price, length)
        lengths_list.append(length)
        trades_array.append(backtest['trades'])
        eq_curves.append(backtest['equity curve'])

    return {'lengths': lengths_list, 'trades': trades_array, 'eq curves': eq_curves}

def optimise_bt_multi(price, length_range, printout=False):
    lengths_list = []
    trades_array = []
    eq_curves = []

    lengths = list(range(*length_range))
    price_list = [price] * len(lengths)
    arguments = zip(price_list, lengths)

    if printout:
        print(f'Optimising length range: {length_range}')
    with multiprocessing.Pool() as pool:
        backtest = pool.starmap(single_backtest, arguments)
    for i in backtest:
        lengths_list.append(i.get('length'))
        trades_array.append(i.get('trades'))
        eq_curves.append(i.get('equity curve'))


    return {'lengths': lengths_list, 'trades': trades_array, 'eq curves': eq_curves}

def calc_stats_one(signals, days):
    equity_curve = signals.get('equity curve')
    if len(equity_curve) > 5 and statistics.stdev(equity_curve) > 0 and days > 0:
        startcash = 1000
        cash = equity_curve[-1]
        profit = (100 * (cash - startcash) / startcash)

        # TODO this pnl_series calc is probably going to be a problem, work out what to do about divide by 0 errors
        pnl_series = [(equity_curve[i] - equity_curve[i - 1]) / equity_curve[i - 1] for i in
                      range(1, len(equity_curve))]
        if len(pnl_series) > 1:  # to avoid StatisticsError: variance requires at least two data points
            sqn = math.sqrt(len(equity_curve)) * statistics.mean(pnl_series) / statistics.stdev(pnl_series)
        else:
            sqn = -1

        wins = 0
        losses = 0
        for i in range(1, len(pnl_series)):
            if pnl_series[i] > 0:
                wins += 1
            else:
                losses += 1
        winrate = round(100 * wins / (wins + losses))

        trades_per_day = len(equity_curve) / days
        prof_per_day = profit / days #TODO this really should be using some kind of logarithm or something

        print(f'{len(equity_curve)} round-trip trades, Profit: {profit:.6}%')
        print(f'SQN: {sqn:.3}, win rate: {winrate}%, avg trades/day: {trades_per_day:.3}, avg profit/day: {prof_per_day:.3}%')
        return {'sqn': sqn, 'win rate': winrate, 'avg trades/day': trades_per_day, 'avg profit/day': prof_per_day}
    else:
        print('Not enough data to produce a result')

def calc_stats_many(signals, days, pair, timescale, strat, params, train_str=None, set_num=None):
    length_list = signals.get('lengths')
    new_length_list = []
    trad_list = []
    prof_list = []
    sqn_list = []
    winrate_list = []
    avg_win_list = []
    avg_loss_list = []
    tpd_list = []
    ppd_list = []

    for x in range(len(length_list)):
        equity_curve = signals.get('eq curves')[x]
        if len(equity_curve) > 5 and statistics.stdev(equity_curve) > 0 and days > 0:
            startcash = 1000
            cash = equity_curve[-1]
            profit = (100 * (cash - startcash) / startcash)

            #TODO this pnl_series calc is probably going to be a problem, work out what to do about divide by 0 errors
            pnl_series = [(equity_curve[i] - equity_curve[i - 1]) / equity_curve[i - 1] for i in range(1, len(equity_curve))]
            if len(pnl_series) > 1:  # to avoid StatisticsError: variance requires at least two data points
                sqn = math.sqrt(len(equity_curve)) * statistics.mean(pnl_series) / statistics.stdev(pnl_series)
            else:
                sqn = -1

            wins = 0
            losses = 0
            win_list = []
            loss_list = []
            for i in range(1, len(pnl_series)):
                if pnl_series[i] > 0:
                    wins += 1
                    win_list.append(pnl_series[i])
                else:
                    losses += 1
                    loss_list.append(pnl_series[i])
            winrate = round(100 * wins / (wins + losses))
            if len(win_list) > 0:
                avg_win = statistics.mean(win_list)
            else:
                avg_win = 0
            if len(loss_list) > 0:
                avg_loss = statistics.mean(loss_list)
            else:
                avg_loss = 0

            trades_per_day = len(equity_curve) / days
            prof_per_day = profit / days #TODO this should use a logarithm

            new_length_list.append(length_list[x])
            trad_list.append(len(equity_curve))
            prof_list.append(profit)
            sqn_list.append(sqn)
            winrate_list.append(winrate)
            avg_win_list.append(avg_win)
            avg_loss_list.append(avg_loss)
            tpd_list.append(trades_per_day)
            ppd_list.append(prof_per_day)

    results = {'length': new_length_list, 'num trades': trad_list, 'profit': prof_list, 'sqn': sqn_list,
               'win rate': winrate_list, 'avg wins': avg_win_list, 'avg losses': avg_loss_list,
               'trades per day': tpd_list, 'pnl per day': ppd_list}
    results_df = pd.DataFrame(results)

    if set_num:
        res_path = Path(f'V:/results/{strat}/walk-forward/{pair}/{timescale}/{train_str}/{params}')

        res_name = Path(f'{set_num}.csv')
    else:
        res_path = Path(f'V:/results/{strat}/backtest/{pair}/{timescale}')
        res_name = Path(f'{params}.csv')

    res_path.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(res_path / res_name)

    return results_df

### draws ohlc chart with buys and sells plotted
def draw_ohlc(data, price, pair):
    trades = data.get('trades')
    eq = data.get('equity curve')
    price = list(price['close'])

    f, (a0, a1) = plt.subplots(2, 1, gridspec_kw={'height_ratios': [3, 1]})


    a0.plot(price)

    buy_indices = []
    buy_prices = []
    sell_indices = []
    sell_prices = []
    how_many_indices = []
    how_many_list = []
    for i in trades:
        if i[1] == 'b':
            buy_prices.append(i[2])
            buy_indices.append(i[3])
        else:
            sell_prices.append(i[2])
            sell_indices.append(i[3])
        how_many_indices.append(i[3])
        how_many_list.append(i[4])

    a0.plot(buy_indices, buy_prices, 'yo')
    a0.plot(sell_indices, sell_prices, 'ro')

    # a1.plot(how_many_indices, how_many_list)
    a1.plot(sell_indices, eq)

    f.tight_layout()
    plt.show()

def single_test(pair, length, timescale='1min', printout=False):
    print(f'Starting single_test on {time.ctime()[:3]} {time.ctime()[9]} at {time.ctime()[11:-8]}')
    start = time.perf_counter()

    price, vol = load_data(pair)
    days = len(vol) / 1440
    if timescale != '1min':
        price, vol = resample_ohlc(price, vol, timescale)
    backtest = single_backtest(price, length)
    if printout:
        print(backtest)
    calc_stats_one(backtest, days)
    draw_ohlc(backtest, price, pair)
    # plot_eq(backtest.get('equity curve'), pair, 'sqn')

    end = time.perf_counter()
    seconds = round(end - start)
    print(f'Time taken: {seconds // 60} minutes, {seconds % 60} seconds')

def test_all(strat, printout=False):
    '''
    Cycles through all pairs and all timescales, each time producing a dictionary of results for a range of param settings
    Saves these dictionaries as dataframes in csv files for further analysis
    Prints best result (according to sqn score) for each pair in each timescale
    '''

    print(f'Starting tests on {time.ctime()[:3]} {time.ctime()[9]} at {time.ctime()[11:-8]}')
    start = time.perf_counter()

    pairs = create_pairs_list('USDT')
    pairs = ['TOMOUSDT']
    timescales = {
        '1min': (300, 1001, 50), '5min': (50, 1001, 10), '15min': (10, 1001, 5), '30min': (10, 1001, 5),
        '1h': (5, 501, 2), '4h': (5, 501, 1), '12h': (5, 501, 1),
        '1d': (3, 301, 1), '3d': (3, 301, 1), '1w': (3, 101, 1)
        }

    for pair in pairs:
        print(f'Testing {pair}')
        price, vol = load_data(pair)
        days = len(vol) / 1440
        for scale in timescales.keys():
            print(f'Testing {scale}')
            if scale != '1min':
                r_price, r_vol = resample_ohlc(price, vol, scale)
            else:
                r_price, r_vol = price, vol
            if len(r_vol) > 0:
                low, hi, step = timescales.get(scale)
                params = f'lengths{low}-{hi}-{step}'
                backtest = optimise_bt_multi(r_price, timescales.get(scale), True)
                results = calc_stats_many(backtest, days, pair, scale, strat, params)
                if printout:
                    print(f'Tests recorded: {len(results.index)}')
                if len(results.index) > 0 and results["sqn"].max() > 2:
                    if printout:
                        print(f'Best SQN: {results["sqn"].max()}')
                    best = results['sqn'].argmax()
                    if printout:
                        print(f'Best settings: {results.iloc[best]}')
            if printout:
                print('-' * 40)
        mid = time.perf_counter()
        seconds = round(mid - start)
        print(f'{pair} took: {seconds // 60} minutes, {seconds % 60} seconds')

    end = time.perf_counter()
    seconds = round(end - start)
    print(f'Time taken: {seconds // 60} minutes, {seconds % 60} seconds')

def walk_forward(strat, printout=False):
    print(f'Starting tests on {time.ctime()[:3]} {time.ctime()[9]} at {time.ctime()[11:-8]}')
    start = time.perf_counter()

    timescales = {
        '1d': (3, 301, 1, 1, 90, 1), '3d': (3, 301, 1, 0.333333, 50, 1), '1w': (3, 101, 1, 0.142857, 50, 1),
        '1h': (5, 501, 2, 24, 2000, 50), '4h': (5, 501, 1, 6, 500, 12), '12h': (5, 501, 1, 2, 180, 4),
        '15min': (10, 1001, 5, 96, 6000, 150), '30min': (10, 1001, 5, 48, 3000, 75),
        '1min': (300, 1001, 50, 1440, 80000, 2000), '5min': (50, 1001, 10, 288, 18000, 450)
    }

    pairs_list = create_pairs_list('USDT')
    # pairs_list = ['ETHBTC', 'ETHUSDT', 'BNBUSDT', 'BTCUSDT', 'BNBBTC']
    pairs_list = ['BNBBTC']
    for pair in pairs_list:
        if printout:
            print(f'Testing {pair} on {time.ctime()[:3]} {time.ctime()[9]} at {time.ctime()[11:-8]}')
        for scale in timescales.keys():
            low, hi, step, div, train_length, test_length = timescales.get(scale)
            params = f'lengths{low}-{hi}-{step}'
            train_string = f'{train_length}-{test_length}'
            ### following lines determine if some tests have already been completed and can be skipped
            res_path = Path(f'V:/results/{strat}/walk-forward/{pair}/{scale}/{train_string}/{params}')
            files_done = list(res_path.glob('*.csv'))
            tests_done = [int(file.stem) for file in files_done]
            i = 0
            for x, test in enumerate(sorted(tests_done)):
                if x+1 != test:
                    i = x
                    break
                else:
                    i += 1
            # print(f'i starting at {i}')
            ### main loop
            training = True
            while training:
                price, vol = load_data(pair)
                print(f'Testing {pair} {scale} on {time.ctime()[:3]} {time.ctime()[9]} at {time.ctime()[11:-8]}')
                if scale != '1min':
                    price, vol = resample_ohlc(price, vol, scale)
                if len(vol) > 0:
                    from_index, to_index = get_dates(i, train_length, test_length, 'train')
                    if (train_length + test_length) > len(price):
                        print(f'Not enough data for {pair} test')
                        training = False
                        print('*' * 40)
                    elif (to_index + test_length) > len(price):
                        print(f'Not enough data for another training period, {pair} finished')
                        training = False
                        print('*' * 40)
                    elif i+1 in tests_done:
                        print(f'Test {i} already completed, moving to next test')
                        i += 1
                    else:
                        num_sets = int((len(price) - train_length) / test_length)
                        print(f'training {i} of {num_sets}\n')
                        price = price.iloc[from_index:to_index, :]
                        days = (len(price.index) / div)
                        backtest_range = timescales.get(scale)[:3]
                        backtest = optimise_bt_multi(price, backtest_range)
                        results = calc_stats_many(backtest, days, pair, scale, strat, params, train_string, i)
                        if printout:
                            print(f'Tests recorded: {len(results.index)}')
                        if len(results.index) > 0:
                            if printout:
                                print(f'Best SQN: {results["sqn"].max()}')
                            best = results['sqn'].argmax()
                            if printout:
                                print(f'Best settings: {results.iloc[best]}')
                        if printout:
                            print('-' * 40)
                        i += 1

    end = time.perf_counter()
    seconds = round(end - start)
    print(f'Time taken: {seconds // 60} minutes, {seconds % 60} seconds')

def load_results(strat, pair, timescale, train_str, params):
    folder = Path(f'V:/results/{strat}/walk-forward/{pair}/{timescale}/{train_str}/{params}')
    files_list = list(folder.glob('*.csv'))
    set_num_list = [int(file.stem) for file in files_list]
    names_list = [file.name for file in files_list]
    df_list = [pd.read_csv(folder / name, index_col=0) for name in names_list]
    df_dict = dict(zip(set_num_list, df_list))

    # print(df_dict.get(1).columns)
    # print(df_dict.keys())
    return df_dict

def get_best(metric, df_dict):
    results = {}
    for i in range(1, len(df_dict.keys())): # range starts at 1 because training sets are all numbered from 1
        df = df_dict.get(i)
        df = df.loc[df['num trades'] > 10]
        best = df.sort_values(metric, ascending=False, ignore_index=True).head(1)
        # TODO if this method doesnt produce good results, it may be because i am just choosing the highest score from
        #  each metric in each period, when i could instead choose the middle of the widest and highest local maximum
        if len(best.index) > 0:
            print(f'\n\n{i} best {metric}:\nlength: {best.iloc[0, 0]}')
            results[i] = best.iloc[0, 0]
        else:
            print(f'\n\n{i} empty df')
            results[i] = None
    return results

def plot_eq(eq_curve, pair, metric):
    plt.plot(eq_curve)

    plt.xlabel('Trades')
    plt.ylabel('Equity')
    plt.yscale('log')
    plt.title(f'{pair} optimised by {metric}')
    plt.show()

def forward_run(strat, pair, timescale, train_length, test_length, params, metric, single_run=True, printout=False):

    # call load_data to get price and vol data
    price, vol = load_data(pair)
    price = price[train_length:]  # forward test starts from the beginning of the first test period
    vol = vol[train_length:]
    days = len(price) / 1440
    train_string = f'{train_length // 1000}k-{test_length // 1000}k'
    if printout:
        print(train_string)

    # call load_results to get walk-forward test results
    df_dict = load_results(strat, pair, timescale, train_string, params)
    if printout:
        print(f'df_dict: {df_dict}')

    # call get_best to get settings for each period for a particular metric
    best = get_best(metric, df_dict)
    # print(best.values())

    # call backtest_forward to generate the signals
    backtest = backtest_forward(best, price, train_length, test_length)
    if printout:
        print(f'backtest: {backtest}')

    # call calculate to generate final statistics
    fwd_results = calculate_one(backtest, days)

    # call draw_ohlc to plot trades on ohlc chart
    # call draw_bricks to draw renko chart
    if single_run:
        draw_ohlc(backtest, price, pair)
        # draw_bars(bricks, 500)
        # chart the equity curves of the different optimisation metrics
        # plot_eq(backtest.get('equity curve'), pair, metric)
        #TODO get draw_ohlc and plot_eq as subplots of the same chart

    return fwd_results

def forward_run_all(train_length, test_length):
    print(f'Starting tests at {time.ctime()[11:-8]}')
    start = time.perf_counter()

    train_string = f'{train_length//1000}k-{test_length//1000}k'
    source = Path(f'V:/results/renko_static_ohlc/walk-forward/{train_string}/{params}')
    pairs_list = create_pairs_list('USDT', source)
    metrics = ['sqn', 'win rate', 'pnl per day', 'avg run', 'score']
    results = {}
    for metric in metrics:
        print(f'running {metric} tests')
        results[metric] = {}
        for pair in pairs_list:
            # print(f'running {pair} tests')
            final_results = forward_run(pair, train_length, test_length, metric, single_run=False)
            results[metric][pair] = final_results
            # print(f'results dictionary: {results}')

    sqn_df = pd.DataFrame(results['sqn'])
    winrate_df = pd.DataFrame(results['win rate'])
    pnl_df = pd.DataFrame(results['pnl per day'])
    avg_run_df = pd.DataFrame(results['avg run'])
    score_df = pd.DataFrame(results['score'])

    res_path = Path(f'V:/results/renko_static_ohlc/forward-run/{train_string}/{params}')
    res_path.mkdir(parents=True, exist_ok=True)

    sqn_df.to_csv(res_path / 'sqn.csv')
    winrate_df.to_csv(res_path / 'winrate.csv')
    pnl_df.to_csv(res_path / 'pnl_per_day.csv')
    avg_run_df.to_csv(res_path / 'avg_run.csv')
    score_df.to_csv(res_path / 'score.csv')

    end = time.perf_counter()
    seconds = round(end - start)
    print(f'Time taken: {seconds // 60} minutes, {seconds % 60} seconds')

if __name__ == '__main__':
    # low, hi, step = (300, 1001, 50)'
    # params = f'lengths{low}-{hi}-{step}'

    # single_test('CRVUSDT', 10, '1w', True)

    # test_all('hma_strat', True)

    walk_forward('hma_strat', True)

    # results = load_results('hma_strat', 'ETHBTC', '1d', '90-1', 'lengths3-301-1')
    # get_best('sqn', results)