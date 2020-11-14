from pathlib import Path
import pandas as pd
from finta.utils import resample

def create_pairs_list(quote, source='ohlc'):
    '''Retrieves a list of all pairs from the folder of OHLC data'''
    if source == 'ohlc':
        stored_files_path = Path(f'V:/ohlc_data/')
        files_list = list(stored_files_path.glob(f'*{quote}-1m-data.csv'))
        pairs = [str(pair)[13:-12] for pair in files_list]
    else:
        folders_list = list(source.iterdir())
        pairs = [str(pair.stem) for pair in folders_list]
        pairs = [pair[-len(quote):] == quote for pair in pairs]


    return pairs

def get_dates(counter, long, short, set):
    '''calculates the index numbers for slicing the ohlc data to feed into the walk-forward testing function'''
    if set == 'train':
        from_date = counter * short
        to_date = from_date + long
    elif set == 'test':
        from_date = (counter * short) + long
        to_date = from_date + short
    return from_date, to_date

def load_data(pair, mode='ohlcv'):
    '''returns a dataframe containing OHLCV data, and a list containing volume data'''
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

def exp_range(min, max, num=50, pow=2):
    '''min and max are the lower and upper bounds of the desired list of integers, num is the target number of integers
    output (not always accurate due to duplicates being dropped), pow is the exponent used to transform the slope.
    if the range of the desired output is less than the number of values needed, the curve will be linear.
    returns a list of integers that roughly describes an exponential series which conforms to the arguments given'''
    val_range = max - min
    if num > val_range:
        num = val_range
        pow = 1
    elif (val_range / num) < pow:
        pow = val_range / num
    steps = round(val_range / num)
    base = list(range(min, max, steps))
    exps = [x**pow for x in base]
    adj_exps = [y-exps[0] for y in exps]
    scaling = adj_exps[-1] / (val_range)
    adj_exps_2 = [round(z/scaling)+min for z in adj_exps]
    return sorted(set(adj_exps_2))