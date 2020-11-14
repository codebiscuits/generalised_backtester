import time
from utilities import load_data, resample_ohlc
from trading.strategies import hma_dvb_strat_new
from functions import single_backtest, calc_stats_one, draw_ohlc, hodl_profit


pair = 'BNBBTC'
strat = hma_dvb_strat_new
args = 50, 60
timescale='1h'
print_all=False


print(f'Starting single_test on {time.ctime()[:3]} {time.ctime()[9]} at {time.ctime()[11:-8]}')
start = time.perf_counter()

price, vol = load_data(pair)

hodl = hodl_profit(price)

days = len(vol) / 1440
if timescale != '1min':
    price, vol = resample_ohlc(price, vol, timescale)
backtest = single_backtest(price, strat, *args, printout=print_all)
if print_all:
    print(backtest)
calc_stats_one(backtest, days, hodl)
draw_ohlc(backtest, price, pair)

end = time.perf_counter()
seconds = round(end - start)
print(f'Time taken: {seconds // 60} minutes, {seconds % 60} seconds')