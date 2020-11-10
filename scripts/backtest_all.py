from functions import hma_strat, hma_dvb_strat_new, create_pairs_list, load_data, exp_ranges, resample_ohlc, optimise_backtest, calc_stats_many
# from config import ind_cache
import time

'''
Cycles through all pairs and all timescales, each time producing a dictionary of results for a range of param settings
Saves these dictionaries as dataframes in csv files for further analysis
Prints best result (according to sqn score) for each pair in each timescale
'''

strat = 'hma_dvb'
printout=True

strat_dict = {'hma': {'name': 'hma_strat', 'func': hma_strat, 'params': ['hma']},
              'hma_dvb': {'name': 'hma_dvb', 'func': hma_dvb_strat_new, 'params': ['hma', 'dvb']},
              }
strategy = strat_dict.get(strat)
name = strategy.get('name')
strat_func = strategy.get('func')

print(f'Starting tests on {time.ctime()[:3]} {time.ctime()[9]} at {time.ctime()[11:-8]}')
start = time.perf_counter()

pairs = create_pairs_list('BTC')
pairs = ['BTCUSDT', 'ETHBTC', 'BNBBTC', 'ETHUSDT', 'BNBUSDT', 'LINKBTC', 'VETBTC', 'ADABTC', 'ATOMBTC', 'TOMOBTC']

for pair in pairs:
    print(f'Testing {pair}')
    price, vol = load_data(pair)
    days = len(vol) / 1440
    for timescale in exp_ranges.keys():
        print(f'Testing {timescale}')
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
            backtest = optimise_backtest(r_price, strat_func, *params)
            results = calc_stats_many(backtest, days, pair, timescale, name, param_str)
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