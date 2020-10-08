from functions import get_best_wide, load_results, aggregate_results, load_data, resample_ohlc, hma_calc
import math

pair = 'TOMOBTC'
strat = 'hma_strat'
timescale = '1h'
train = 2000
test = 50
train_string = f'{train}-{test}'
params = 'lengths5-501-2'
metric = 'sqn'

print('- Loading data')
price, vol = load_data(pair)
print('- Resampling data')
price, vol = resample_ohlc(price, vol, timescale)
print(f'len(price): {len(price)}')

print('- Loading results')
df_dict = load_results(strat, pair, timescale, train_string, params)

print('- Running get_best')
best = get_best_wide(metric, df_dict, train, test)

print('Running hma_calc')
hma_25 = hma_calc(price, 25)
print('Running hma_calc')
hma_327 = hma_calc(price, 327)

nan_count = 0
for q in range(len(hma_25)):
    if math.isnan(hma_25[q]):
        nan_count += 1
print(f'-*- individual hma_25 nan_count: {nan_count}')

nan_count = 0
for q in range(len(hma_327)):
    if math.isnan(hma_327[q]):
        nan_count += 1
print(f'-*- individual hma_327 nan_count: {nan_count}')

print('- Running aggregate_results')
hma = aggregate_results(best, price)