from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import math
import statistics
import time
import multiprocessing
from utilities import exp_range
from config import ind_cache



backtest_ranges = {
        # '1w': (3, 101, 1),
        # '3d': (3, 301, 1),
        # '1d': (3, 301, 1),
        '12h': (5, 501, 1),
        '4h': (5, 501, 1),
        '1h': (5, 501, 2),
        '30min': (10, 1001, 5),
        '15min': (10, 1001, 5),
        # '5min': (50, 1001, 10)
        # '1min': (300, 1001, 50),
        }

walk_fwd_ranges_old = {
        # '1w': (3, 101, 1, 0.142857, 50, 1),
        # '3d': (3, 301, 1, 0.333333, 50, 1),
        # '1d': (3, 301, 1, 1, 90, 1),
        '12h': (5, 25, 1, 2, 360, 4),
        '4h': (5, 201, 2, 6, 1000, 12),
        '1h': (5, 201, 2, 24, 2000, 50),
        '30min': (10, 301, 3, 48, 3000, 75),
        '15min': (10, 601, 5, 96, 6000, 150),
        # '5min': (50, 1001, 10, 288, 18000, 450),
        # '1min': (300, 1001, 50, 1440, 80000, 2000)
        }

ranges0 = {
        # '1w': ({'hma': (3, 101, 1), 'dvb': (3, 101, 1)}, 0.142857, 50, 1),
        # '3d': ({'hma': (3, 301, 1), 'dvb': (3, 301, 1)}, 0.333333, 50, 1),
        # '1d': ({'hma': (3, 301, 1), 'dvb': (3, 301, 1)}, 1, 90, 1),
        '12h': ({'hma': (5, 25, 1), 'dvb': (5, 25, 1)}, 2, 360, 4),
        '4h': ({'hma': (5, 201, 2), 'dvb': (5, 201, 2)}, 6, 1000, 12),
        '1h': ({'hma': (11, 301, 3), 'dvb': (11, 301, 3)}, 24, 2000, 50),
        '30min': ({'hma': (11, 301, 3), 'dvb': (11, 301, 3)}, 48, 3000, 75),
        '15min': ({'hma': (11, 601, 6), 'dvb': (11, 601, 6)}, 96, 6000, 150),
        # '5min': ({'hma': (50, 1001, 10), 'dvb': (50, 1001, 10)}, 288, 18000, 450),
        # '1min': ({'hma': (300, 1001, 50), 'dvb': (300, 1001, 50)}, 1440, 80000, 2000)
        }

ranges = {
        # '1w': ({'hma': (2, 21, 1), 'dvb': (2, 21, 1)}, 0.142857, 50, 1),
        # '3d': ({'hma': (3, 21, 1), 'dvb': (3, 21, 1)}, 0.333333, 50, 1),
        # '1d': ({'hma': (3, 21, 1), 'dvb': (3, 21, 1)}, 1, 90, 1),
        # '12h': ({'hma': (3, 21, 1), 'dvb': (5, 25, 10)}, 2, 360, 4),
        '4h': ({'hma': (11, 401, 4), 'dvb': (11, 201, 20)}, 6, 1000, 12),
        '1h': ({'hma': (11, 501, 5), 'dvb': (11, 301, 30)}, 24, 2000, 50),
        '30min': ({'hma': (11, 501, 5), 'dvb': (11, 401, 40)}, 48, 3000, 75),
        '15min': ({'hma': (11, 601, 6), 'dvb': (11, 601, 60)}, 96, 6000, 150),
        # '5min': ({'hma': (50, 1001, 10), 'dvb': (50, 1001, 100)}, 288, 18000, 450),
        # '1min': ({'hma': (300, 1001, 50), 'dvb': (300, 1001, 100)}, 1440, 80000, 2000)
        }




### define functions

### backtest a single set of params
def single_backtest_old(price, length, mode='norm', best=None, printout=False):
    printout = False
    vol = list(price.loc[:, 'volume'])
    # print(price.columns)

    startcash = 1000
    cash = startcash
    asset = 0
    fees = 0.00075
    comm = 1 - fees
    equity_curve = []
    trade_list = []
    position = None

    start_signals = time.perf_counter()
    if mode == 'norm':
        signals = hma_strat(price, length)
        new_price = price
    else:
        signals, new_price, hma_stitch = hma_strat_forward(best, price)
    if printout:
        print(f'Signals: {len(signals)}')
    close_list = list(new_price['close'])
    end_signals = time.perf_counter()
    seconds = round(end_signals - start_signals)
    # print(f'Generating signals for length {length} took: {seconds // 60} minutes, {seconds % 60} seconds')

    # counter = 0
    for i in range(len(signals)):
        if printout:
            print(f'Backtest {i} of {len(signals)} completed')
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
        #     cash = comm * asset * close_list[ohlc_index]
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
            asset = cash * comm / close_list[ohlc_index] # initial calculation for position size
            cash_value = comm * asset * close_list[ohlc_index]  # position is in base currency but volume is given in quote
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
            cash = comm * asset * close_list[ohlc_index]
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
            asset = cash * comm / close_list[ohlc_index]
            cash_value = comm * asset * close_list[ohlc_index]  # position is in base currency but volume is given in quote
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

    if mode == 'norm':
        return {'length': length, 'equity curve': equity_curve, 'trades': trade_list}
    else:
        return {'length': length, 'equity curve': equity_curve, 'trades': trade_list}, new_price, hma_stitch

### backtest a single set of params
def single_backtest(price, strategy, *args, mode='norm', best=None, printout=False):
    printout = False
    vol = list(price.loc[:, 'volume'])
    # print(price.columns)

    startcash = 1000
    cash = startcash
    asset = 0
    fees = 0.00075
    comm = 1 - fees
    equity_curve = []
    trade_list = []
    position = None

    start_signals = time.perf_counter()
    if mode == 'norm':
        signals = strategy(price, args)
        new_price = price
    else:
        #TODO fwd needs updating to *args functionality
        signals, new_price, hma_stitch = hma_strat_forward(best, price)
    if printout:
        print(f'Signals: {len(signals)}')
    close_list = list(new_price['close'])
    end_signals = time.perf_counter()
    seconds = round(end_signals - start_signals)
    # print(f'Generating signals for length {length} took: {seconds // 60} minutes, {seconds % 60} seconds')

    # counter = 0
    for i in range(len(signals)):
        if printout:
            print(f'Backtest {i} of {len(signals)} completed')
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
        #     cash = comm * asset * close_list[ohlc_index]
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
            asset = cash * comm / close_list[ohlc_index] # initial calculation for position size
            cash_value = comm * asset * close_list[ohlc_index]  # position is in base currency but volume is given in quote
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
            cash = comm * asset * close_list[ohlc_index]
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
            asset = cash * comm / close_list[ohlc_index]
            cash_value = comm * asset * close_list[ohlc_index]  # position is in base currency but volume is given in quote
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

    # in the old version, 'params' was 'length' and output a single value, now it's a tuple
    if mode == 'norm':
        return {'params': args, 'equity curve': equity_curve, 'trades': trade_list}
    else:
        return {'params': args, 'equity curve': equity_curve, 'trades': trade_list}, new_price, hma_stitch

### backtests a range of settings
def optimise_backtest_old(price, length_range, printout=False):
    lengths_list = []
    trades_array = []
    eq_curves = []
    for length in range(*length_range):
        if printout:
            print(f'testing length: {length}')
        backtest = single_backtest_old(price, length)
        lengths_list.append(length)
        trades_array.append(backtest['trades'])
        eq_curves.append(backtest['equity curve'])

    return {'lengths': lengths_list, 'trades': trades_array, 'eq curves': eq_curves}

def optimise_backtest(price, strategy, *args, printout=False):
    params_list = []
    trades_array = []
    eq_curves = []

    # global ind_cache # this line and the next just clear ind_cache ready for the next set of tests
    # ind_cache = {'p1': {}, 'p2': {}, 'p3': {}}
    test_count = 0

    if len(args) > 3:
        raise ValueError("Can't optimise more than 3 params")
    elif len(args) == 3:
        total_tests = len(exp_range(*args[0])) * len(exp_range(*args[1])) * len(exp_range(*args[2]))
        opt_start = time.perf_counter()
        new_mod = False
        for param0 in exp_range(*args[0]):
            for param1 in exp_range(*args[1]):
                for param2 in exp_range(*args[2]):
                    if printout:
                        print(f'Testing params {param0}, {param1}, {param2} on {time.ctime()[:3]} {time.ctime()[9]} at {time.ctime()[11:-8]}')
                    backtest = single_backtest(price, strategy, param0, param1, param2)
                    params_list.append((param0, param1, param2))
                    trades_array.append(backtest['trades'])
                    eq_curves.append(backtest['equity curve'])
                    opt_split = time.perf_counter()
                    split_time = round(opt_split-opt_start)
                    test_count += 1
                    pct_tests = round(100*test_count/total_tests)
                    mod_pct = 10
                    if pct_tests % mod_pct == 1:
                        new_mod = True
                    if pct_tests % mod_pct == 0 and new_mod:
                        print(f'{pct_tests}% completed on {time.ctime()[:3]} {time.ctime()[9]} at {time.ctime()[11:-8]}. '
                              f'Time taken: {int(split_time/60)}m {split_time%60}s')
                        new_mod = False
                        opt_start = time.perf_counter()
    elif len(args) == 2:
        total_tests = len(exp_range(*args[0])) * len(exp_range(*args[1]))
        opt_start = time.perf_counter()
        new_mod = False
        for param0 in exp_range(*args[0]):
            for param1 in exp_range(*args[1]):
                if printout:
                    print(f'Testing params {param0}, {param1} on {time.ctime()[:3]} {time.ctime()[9]} at {time.ctime()[11:-8]}')
                backtest = single_backtest(price, strategy, param0, param1)
                params_list.append((param0, param1))
                trades_array.append(backtest['trades'])
                eq_curves.append(backtest['equity curve'])
                opt_split = time.perf_counter()
                split_time = round(opt_split-opt_start)
                test_count += 1
                pct_tests = round(100*test_count/total_tests)
                mod_pct = 10
                if pct_tests % mod_pct == 1:
                    new_mod = True
                if pct_tests % mod_pct == 0 and new_mod:
                    print(f'{pct_tests}% completed on {time.ctime()[:3]} {time.ctime()[9]} at {time.ctime()[11:-8]}. '
                          f'Time taken: {int(split_time/60)}m {split_time%60}s')
                    new_mod = False
                    opt_start = time.perf_counter()
    else:
        total_tests = len(exp_range(*args[0]))
        opt_start = time.perf_counter()
        new_mod = False
        for param0 in exp_range(*args[0]):
            if printout:
                print(f'Testing params {param0} on {time.ctime()[:3]} {time.ctime()[9]} at {time.ctime()[11:-8]}')
            backtest = single_backtest(price, strategy, param0)
            params_list.append(param0)
            trades_array.append(backtest['trades'])
            eq_curves.append(backtest['equity curve'])
            opt_split = time.perf_counter()
            split_time = round(opt_split-opt_start)
            test_count += 1
            pct_tests = round(100*test_count/total_tests)
            mod_pct = 10
            if pct_tests % mod_pct == 1:
                new_mod = True
            if pct_tests % mod_pct == 0 and new_mod:
                print(f'{pct_tests}% completed on {time.ctime()[:3]} {time.ctime()[9]} at {time.ctime()[11:-8]}. '
                      f'Time taken: {int(split_time/60)}m {split_time%60}s')
                new_mod = False
                opt_start = time.perf_counter()

    return {'params': params_list, 'trades': trades_array, 'eq curves': eq_curves}

def optimise_bt_multi_old(price, length_range, printout=False):
    lengths_list = []
    trades_array = []
    eq_curves = []

    lengths = list(range(*length_range))
    price_list = [price] * len(lengths)
    arguments = zip(price_list, lengths)

    if printout:
        print(f'Optimising length range: {length_range}')
    with multiprocessing.Pool() as pool:
        backtest = pool.starmap(single_backtest_old, arguments) # returns list of dictionaries
    for i in backtest:
        lengths_list.append(i.get('length'))
        trades_array.append(i.get('trades'))
        eq_curves.append(i.get('equity curve'))


    return {'lengths': lengths_list, 'trades': trades_array, 'eq curves': eq_curves}

def optimise_bt_multi(price, strategy, *args, printout=False):
    # TODO this is mostly rewritten but i haven't quite got it working yet
    params_list = []
    trades_array = []
    eq_curves = []

    if len(args) == 1:
        param0 = exp_range(*args[0])
        price_list = [price] * len(param0)
        strat_list = [strategy] * len(param0)
        arguments = zip(price_list, strat_list, param0)

        if printout:
            print(f'Optimising param range: {args[0]}')
        with multiprocessing.Pool() as pool:
            backtest = pool.starmap(single_backtest, arguments)  # returns list of dictionaries
        for i in backtest:
            params_list.append(i.get('params'))
            trades_array.append(i.get('trades'))
            eq_curves.append(i.get('equity curve'))

    elif len(args) == 2:
        param0 = exp_range(*args[0])
        param1 = exp_range(*args[1])
        p0_list = []
        p1_list = []
        for p0 in param0:
            for p1 in param1:
                p0_list.append(p0)
                p1_list.append(p1)
        price_list = [price] * len(p0_list)
        strat_list = [strategy] * len(p0_list)
        arguments = zip(price_list, strat_list, p0_list, p1_list)

        if printout:
            print(f'Optimising param range: {args[0]}, {args[1]}')
        with multiprocessing.Pool() as pool:
            backtest = pool.starmap(single_backtest, arguments)  # returns list of dictionaries
        for i in backtest:
            params_list.append(i.get('params'))
            trades_array.append(i.get('trades'))
            eq_curves.append(i.get('equity curve'))

    elif len(args) == 3:
        param0 = exp_range(*args[0])
        param1 = exp_range(*args[1])
        param2 = exp_range(*args[2])
        p0_list = []
        p1_list = []
        p2_list = []
        for p0 in param0:
            for p1 in param1:
                for p2 in param2:
                    p0_list.append(p0)
                    p1_list.append(p1)
                    p2_list.append(p2)
        price_list = [price] * len(param0)
        strat_list = [strategy] * len(param0)
        arguments = zip(price_list, strat_list, param0, param1, param2)

        if printout:
            print(f'Optimising param range: {args[0]}, {args[1]}, {args[2]}')
        with multiprocessing.Pool() as pool:
            backtest = pool.starmap(single_backtest, arguments)  # returns list of dictionaries
        for i in backtest:
            params_list.append(i.get('params'))
            trades_array.append(i.get('trades'))
            eq_curves.append(i.get('equity curve'))

    else:
        raise ValueError("Can't optimise more than 3 params")

    return {'params': params_list, 'trades': trades_array, 'eq curves': eq_curves}

def calc_stats_one(signals, days, hodl):
    equity_curve = signals.get('equity curve')
    if len(equity_curve) > 5 and statistics.stdev(equity_curve) > 0 and days > 0:
        startcash = 1000
        cash = equity_curve[-1]
        profit = (100 * (cash - startcash) / startcash)
        profit_bth = profit / hodl

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

        print(f'{len(equity_curve)} round-trip trades, Profit (better than hodl): {profit_bth:.3}%')
        print(f'SQN: {sqn:.3}, win rate: {winrate}%, avg trades/day: {trades_per_day:.3}, avg profit/day: {prof_per_day:.3}%')
        return {'sqn': round(sqn, 3), 'win rate': winrate, 'avg trades/day': round(trades_per_day, 3), 'avg profit/day': round(prof_per_day, 3)}
    else:
        print('Not enough data to produce a result')

def calc_stats_many_old(signals, days, pair, timescale, strat, params, train_str=None, set_num=None):
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

def calc_stats_many(signals, days, pair, timescale, strat, params, hodl_profit, train_str=None, set_num=None):
    param_list = signals.get('params')
    new_param_list = []
    trad_list = []
    prof_list = []
    sqn_list = []
    winrate_list = []
    avg_rr_list = []
    # avg_loss_list = []
    tpd_list = []
    ppd_list = []

    for x in range(len(param_list)):
        equity_curve = signals.get('eq curves')[x]
        if len(equity_curve) > 5 and statistics.stdev(equity_curve) > 0 and days > 0:
            startcash = 1000
            cash = equity_curve[-1]
            profit = (100 * (cash - startcash) / startcash)
            profit_bth = profit / hodl_profit # profit better than hodl

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
            winrate = 100 * wins / (wins + losses)
            if len(win_list) > 0:
                avg_win = statistics.mean(win_list)
            else:
                avg_win = 0
            if len(loss_list) > 0:
                avg_loss = statistics.mean(loss_list)
            else:
                avg_loss = 0
            if abs(avg_loss) > 0:
                avg_rr = avg_win / avg_loss
            else:
                avg_rr = 0

            trades_per_day = len(equity_curve) / days
            prof_per_day = profit / days #TODO this should use a logarithm

            new_param_list.append(param_list[x])
            trad_list.append(len(equity_curve))
            prof_list.append(round(profit_bth, 3))
            sqn_list.append(round(sqn, 3))
            winrate_list.append(round(winrate))
            avg_rr_list.append(round(avg_rr, 3))
            # avg_loss_list.append(round(avg_loss, 3))
            tpd_list.append(round(trades_per_day, 3))
            ppd_list.append(round(prof_per_day, 3))

    results = {'params': new_param_list, 'num trades': trad_list, 'profit bth': prof_list, 'sqn': sqn_list,
               'win rate': winrate_list, 'avg rr': avg_rr_list,# 'avg loss': avg_loss_list,
               'trades per day': tpd_list, 'pnl per day': ppd_list}
    results_df = pd.DataFrame(results)

    if set_num:
        res_path = Path(f'V:/results/{strat}/walk-forward/{pair}/{timescale}/{train_str}/{params}')

        res_name = Path(f'{set_num}.csv')
    else:
        res_path = Path(f'V:/results/{strat}/backtest_multi/{pair}/{timescale}')
        res_name = Path(f'{params}.csv')

    res_path.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(res_path / res_name)

    return results_df

### draws ohlc chart with buys and sells plotted
def draw_ohlc(data, price, hma_stitch):
    trades = data.get('trades')
    eq = data.get('equity curve')
    price = list(price['close'])

    f, (a0, a1) = plt.subplots(2, 1, sharex=True, gridspec_kw={'height_ratios': [3, 1]})


    a0.plot(price)
    a0.plot(hma_stitch)

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

def hodl_profit(data):
    '''Calculates the percentage profit from holding the asset from the beginning to the end of the data being tested,
    for the purpose of comparing to strategy results from the same data'''
    first_open = data.iloc[0, 0]
    last_close = data.iloc[-1, 3]
    return round(100 * (last_close - first_open) / first_open, 3)

def walk_forward(strat, printout=False):
    print(f'Starting tests on {time.ctime()[:3]} {time.ctime()[9]} at {time.ctime()[11:-8]}')
    start = time.perf_counter()

    timescales = walk_fwd_ranges_old

    # pairs_list = create_pairs_list('BTC')
    # pairs_list = pairs_list[::-1]
    pairs_list = ['BNBBTC', 'ETHBTC', 'ETHUSDT', 'BNBUSDT', 'BTCUSDT', 'TOMOBTC', 'VETBTC', 'ICXBTC', 'ADABTC', 'NEOBTC', 'LTCBTC', 'LINKBTC']

    for pair in pairs_list:
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
            if not printout: # theres an alternative in the while loop if printout is true
                print(f'Testing {pair} {scale} on {time.ctime()[:3]} {time.ctime()[9]} at {time.ctime()[11:-8]}')
            # result = None
            # while result is None:
            #     try:
            #         main_price, main_vol = load_data(pair)
            #         result = main_vol
            #     except pd.error.ParserError:
            #         print('*-' * 30, ' ParserError ', '-*' * 30)
            #         pass
            main_price, main_vol = load_data(pair) # the try except block above just produces an endless loop of errors
            if scale != '1min':
                main_price, main_vol = resample_ohlc(main_price, main_vol, scale)
            training = True
            while training:
                if printout:
                    print(f'Testing {pair} {scale} on {time.ctime()[:3]} {time.ctime()[9]} at {time.ctime()[11:-8]}')
                if len(main_vol) > 0:
                    from_index, to_index = get_dates(i, train_length, test_length, 'train')
                    if (train_length + test_length) > len(main_price):
                        print(f'Not enough data for {pair} test')
                        training = False
                        print('*' * 40)
                    elif (to_index + test_length) > len(main_price):
                        print(f'set number: {i}, from_index: {from_index}, to_index: {to_index}, len(price): {len(main_price)}')
                        print(f'Not enough data for another training period, {pair} finished')
                        training = False
                        print('*' * 40)
                    elif i+1 in tests_done:
                        print(f'Test {i} already completed, moving to next test')
                        i += 1
                    else:
                        num_sets = int((len(main_price) - train_length) / test_length)
                        if printout:
                            print(f'training {i} of {num_sets}')
                        else:
                            print(f'{pair} {scale} training {i} of {num_sets} at time {time.ctime()[11:-8]}, len(price): {len(main_price)}')

                        price = main_price.iloc[from_index:to_index, :]
                        days = (len(price.index) / div)
                        backtest_range = timescales.get(scale)[:3]
                        backtest = optimise_bt_multi_old(price, backtest_range)
                        results = calc_stats_many_old(backtest, days, pair, scale, strat, params, train_string, i)
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
    # print(folder)
    files_list = list(folder.glob('*.csv'))
    # print(f'files_list: {files_list}')
    set_num_list = [int(file.stem) for file in files_list]
    names_list = [file.name for file in files_list]
    df_list = [pd.read_csv(folder / name, index_col=0) for name in names_list]
    df_dict = dict(zip(set_num_list, df_list))

    # print(df_dict.get(1).columns)
    # print(df_dict.keys())
    return df_dict

### returns dict with keys: training set num, values: hma length
def get_best(metric, df_dict, long, short):
    results = {}
    last_valid = -1 # any train period that doesn't produce a valid result can use the most recent one
    count_result = 0 # how many training periods produced a valid result
    count_none = 0 # how many didn't. these counts are affected by the 'num trades' filter a few lines down
    list_for_plot = []
    for i in range(1, len(df_dict.keys())): # range starts at 1 because training sets are all numbered from 1
        df = df_dict.get(i)
        df = df.loc[df['num trades'] > 30]
        best = df.sort_values(metric, ascending=False, ignore_index=True).head(1)
        from_date, to_date = get_dates(i, long, short, 'test')
        if len(best.index) > 0:
            count_result += 1
            # print(f'{i} best {metric}: length: {best.iloc[0, 0]}')
            results[i] = {'length': best.iloc[0, 0], 'from': from_date, 'to': to_date}
            last_valid = best.iloc[0, 0]
            list_for_plot.append(best.iloc[0, 0])
        else:
            count_none += 1
            # print(f'{i} empty df')
            results[i] = {'length': last_valid, 'from': from_date, 'to': to_date}
    print(f'count_result: {count_result}, count_none: {count_none}')

    plt.plot(list_for_plot)
    plt.xlabel('period')
    plt.ylabel('length')
    plt.show()

    return results # returns dict with keys: training set num, values: {hma length, date from, date to}

### returns dict with keys: training set num, values: hma length
def get_best_wide(metric, df_dict, long, short):
    results = {}
    last_valid = -1 # any train period that doesn't produce a single valid result can use the most recent one
    count_result = 0 # how many training periods produced a valid result
    count_none = 0 # how many didn't. these counts are affected by the 'num trades' filter a few lines down
    list_for_plot = [] # to plot evolution of length over the whole lifetime of the pair
    wide_tot_list = []
    for j in range(1, len(df_dict.keys())): # range starts at 1 because training sets are all numbered from 1
        df = df_dict.get(j)
        df = df.loc[df['num trades'] > 10]
        for i in range(len(df.index)):
            res_cols = {'sqn': 3, 'win rate': 4, 'pnl per day': 8}
            col = res_cols.get(metric) # turns metric string into a number so i can use iloc
            wide_total = sum(df.iloc[i-3:i+4, col])
            wide_tot_list.append((df.iloc[i, 0], wide_total))
        # print(f'wide_tot_list before sort: {wide_tot_list}')
        wide_tot_list = sorted(wide_tot_list, key=lambda x:x[1])
        # print(f'wide_tot_list after: {wide_tot_list}')
        best = wide_tot_list[0]
        from_date, to_date = get_dates(j, long, short, 'test')
        if len(best) > 0:
            count_result += 1
            # print(f'{i} best {metric}: length: {best.iloc[0, 0]}')
            results[j] = {'length': best[0], 'from': from_date, 'to': to_date}
            last_valid = best[0]
            list_for_plot.append(best[0])
        else:
            count_none += 1
            # print(f'{i} empty df')
            results[j] = {'length': last_valid, 'from': from_date, 'to': to_date}
    print(f'count_result: {count_result}, count_none: {count_none}')

    # plt.plot(list_for_plot)
    # plt.xlabel('period')
    # plt.ylabel('length')
    # plt.show()

    return results # returns dict with keys: training set num, values: {hma length, date from, date to}

# if get_best outputs a length of -1, that means dont start trading yet, because no valid signal has been produced yet

### takes the results from get_best and stitches together a hma series from different hma lengths
def aggregate_results(best, price):
    # this function replaces hma_calc as it outputs a series of hma values which can be used to generate signals

    prev = 0
    from_list = []
    for setnum in best:
        l = best[setnum].get('length')
        f = best[setnum].get('from')
        t = best[setnum].get('to')
        # print(f'setnum: {setnum}, length: {l}, from: {f}, to: {t}')
        if l != prev:
            from_list.append((l, f))
        prev = l
    # for i in from_list:
        # print(f'length {i[0]} starts at {i[1]}')

    length_set = set([best[i].get('length') for i in best])
    # print(f'length_set: {length_set}')
    # print(f'len(price): {len(price)}')
    hma_dict = {}
    for k in length_set:
        start = time.perf_counter()
        hma_k = hma_calc_old(price, k)
        end = time.perf_counter()
        total = end - start
        hma_dict[k] = hma_k

        # print(f'hma {k} calculated in {int(total / 60)}m {round(total % 60)}s')
    # print(f'len(series_dict): {len(hma_dict)}')
    stitch = []

    for setnum in best:
        l = best[setnum].get('length')
        f = best[setnum].get('from')
        t = best[setnum].get('to')
        s = hma_dict.get(l)[f:t]
        # print(f'l: {l}, f: {f}, t: {t}, s: {s}')
        stitch.extend(s)

    first_set = min(best.keys())
    last_set = max(best.keys())
    first_index = best[first_set].get("from")
    last_index = best[last_set].get("to")
    # print(f'After stitching; len(price): {len(price)}, len(stitch): {len(stitch)}, last index tested: {best[last_set].get("to")}')

    new_price = price[first_index:last_index]


    if len(stitch) == len(new_price):
        print(f'\nstitch is same length as input series\n')
    elif len(stitch) > len(new_price):
        print(f'\nstitch is longer than price by {len(stitch) - len(new_price)}\n')
    elif len(stitch) < len(new_price):
        print(f'\nprice is longer than stitch by {len(new_price) - len(stitch)}\n')

    return new_price, stitch

### multiprocessing version of aggregate_results
def aggregate_results_multi(best, price):
    # print(f'best.keys(): {best.keys()}')
    length_set = set([best[i].get('length') for i in best])
    length_list = list(length_set)
    print(f'HMA series to calculate: {len(length_set)}')

    price_list = [price] * len(length_set)
    arguments = zip(price_list, length_list)
    with multiprocessing.Pool() as pool:
        hma_list = pool.starmap(hma_calc_old, arguments)

    hma_dict = {}
    for k in length_list:
        hma_dict[k] = hma_list[k]
    print(f'len(series_dict): {len(hma_dict)}')
    stitch = []

    for setnum in best:
        l = best[setnum].get('length')
        f = best[setnum].get('from')
        t = best[setnum].get('to')
        s = hma_dict.get(l)[f:t]
        stitch.extend(s)

    first_set = min(best.keys())
    last_set = max(best.keys())
    first_index = best[first_set].get("from")
    last_index = best[last_set].get("to")
    print(f'After stitching; len(price): {len(price)}, len(stitch): {len(stitch)}, last index tested: {best[last_set].get("to")}')

    price = price[first_index:last_index]

    if len(stitch) == len(price):
        print(f'\nstitch is same length as input series\n')
    elif len(stitch) > len(price):
        print(f'\nstitch is longer than price by {len(stitch) - len(price)}\n')
    elif len(stitch) < len(price):
        print(f'\nprice is longer than stitch by {len(price) - len(stitch)}\n')

    return price, stitch

def forward_run(strat, pair, timescale, train_length, test_length, params, metric, single_run=True, printout=False):
    # TODO train_length, test_length and params can all be pulled automatically from the folder structure

    start = time.perf_counter()

    price, vol = load_data(pair)
    price, vol = resample_ohlc(price, vol, timescale)
    # price = price[train_length:]  # forward test starts from the beginning of the first test period
    # vol = vol[train_length:]
    days = len(price) / 1440
    train_string = f'{train_length}-{test_length}'
    if printout:
        print(train_string)

    df_dict = load_results(strat, pair, timescale, train_string, params)
    if printout:
        print(f'df_dict: {df_dict}')

    best = get_best_wide(metric, df_dict, train_length, test_length) # returns {set num: {length, from_date, to_date}}
    # print(f'best.values(): {best.values()}')

    print('Running Backtest')
    backtest, new_price, hma_stitch = single_backtest_old(price, None, 'fwd', best, True)
    if printout:
        print(f'backtest: {backtest}')

    print('Calculating Stats')
    fwd_results = calc_stats_one(backtest, days)

    if single_run:
        draw_ohlc(backtest, new_price, hma_stitch)
        # chart the equity curves of the different optimisation metrics
        # plot_eq(backtest.get('equity curve'), pair, metric)
        #TODO get draw_ohlc and plot_eq as subplots of the same chart

    end = time.perf_counter()
    total_time = round(end-start)
    print(f'Time taken: {int(total_time/60)}m, {total_time%60}s')

    print('Forward run completed')
    return fwd_results

def forward_run_all(strat, train_length, test_length, quote):
    print(f'Starting tests at {time.ctime()[11:-8]}')
    start = time.perf_counter()

    train_string = f'{train_length//1000}k-{test_length//1000}k'
    source = Path(f'V:/results/{strat}/walk-forward/{train_string}/{params}')
    pairs_list = create_pairs_list(quote, source)
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

# TODO put all functions in separate modules, strategies in one, utilities in another, scripts in another etc

if __name__ == '__main__':

    walk_forward('hma_strat')

    forward_run('hma_strat', 'ONTBTC', '4h', 1000, 12, 'lengths5-201-2', 'pnl per day')

    print('Starting Forward Run Loop')
    results = {}
    pairs = ['BNBBTC', 'ETHBTC', 'ICXBTC', 'ONTBTC', 'ZILBTC']
    metrics = ['sqn', 'win rate', 'pnl per day']
    for pair in pairs:
        pair_dict = {}
        for metric in metrics:
            res = forward_run('hma_strat', pair, '4h', 1000, 12, 'lengths5-201-2', metric, single_run=False)
            pair_dict['metric'] = res
            print(f'Optimising {pair} by {metric} produced an SQN of {res.get("sqn")}')
            print('\n', '-' * 80, '\n')
        results['pair'] = pair_dict
