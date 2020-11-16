from config import exp_ranges
from utilities import create_pairs_list, load_data, resample_ohlc
from trading.strategies import strat_dict # contains all strategies with metadata
from functions import optimise_backtest, optimise_bt_multi, calc_stats_many
import time

'''
Cycles through all pairs and all timescales, each time producing a dictionary of results for a range of param settings
Saves these dictionaries as dataframes in csv files for further analysis
Prints best result (according to sqn score) for each pair in each timescale
'''

if __name__ == '__main__':

    strat = 'hma_dvb' # 'hma','hma_dvb'
    printout=True

    strategy = strat_dict.get(strat)
    name = strategy.get('name')
    strat_func = strategy.get('func')

    start = time.perf_counter()

    pairs = create_pairs_list('BTC')
    pairs = ['BTCUSDT', 'ETHBTC', 'BNBBTC', 'ETHUSDT', 'BNBUSDT', 'XMRBTC']

    for pair in pairs:
        print(f'Testing {pair} on {time.ctime()[:3]} {time.ctime()[9]} at {time.ctime()[11:-8]}')
        price, vol = load_data(pair)
        days = len(vol) / 1440
        for timescale in exp_ranges.keys():
            ts_start = time.perf_counter()
            print(f'Testing {timescale} at {time.ctime()[11:-8]}')
            first_price = price.iloc[0, 0]
            last_price = price.iloc[-1, 3]
            hodl_profit = profit = (100 * (last_price - first_price) / first_price)
            all_param_ranges = exp_ranges.get(timescale)[0]
            param_ranges = {k:v for (k, v) in all_param_ranges.items() if k in strat_dict.get(strat)['params']}
            params = tuple(param_ranges.values()) # *args for optimise_backtest
            param_str_list = [f'{k}_{v[0]}-{v[1]}-{v[2]}' for (k, v) in param_ranges.items()]
            param_str = '_'.join(param_str_list)
            if timescale != '1min':
                r_price, r_vol = resample_ohlc(price, vol, timescale)
            else:
                r_price, r_vol = price, vol
            if len(r_vol) > 0:
                # print(ind_cache)
                backtest = optimise_bt_multi(r_price, strat_func, *params)
                # print(ind_cache.get('p1').keys())
                # ind_cache['p1'] = {}
                # ind_cache['p2'] = {}
                # ind_cache['p3'] = {}
                results = calc_stats_many(backtest, days, pair, timescale, name, param_str, hodl_profit)
                if printout:
                    print(f'Tests recorded: {len(results.index)}')
                if len(results.index) > 0 and results["sqn"].max() > 2:
                    best = results['sqn'].argmax()
                    if printout:
                        print(f'Best SQN: {results["sqn"].max()}, Best settings: {results.iloc[best, 0]}')
            ts_end = time.perf_counter()
            print(f'{pair} {timescale} took {round((ts_end-ts_start)/60)}m {round((ts_end-ts_start)%60)}s')
            print('-' * 80)
        mid = time.perf_counter()
        seconds = round(mid - start)
        print(f'{pair} took: {seconds // 60} minutes, {seconds % 60} seconds')
        print('-' * 40)

    end = time.perf_counter()
    seconds = round(end - start)
    print(f'Time taken: {seconds // 60} minutes, {seconds % 60} seconds')