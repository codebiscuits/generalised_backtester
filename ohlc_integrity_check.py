import pandas as pd
from binance.client import Client
import keys
import time
from pathlib import Path


def drop_dups(ohlc):
    dupl_list = []
    try:
        for i in range(len(ohlc.index)):
            if ohlc.index[i] in dupl_list:
                ohlc = ohlc.drop(ohlc.index[i])
            else:
                dupl_list.append(ohlc.index[i])
    except IndexError:
        pass
    return ohlc


def find_gaps(pair, ohlc):
    new_time = pd.date_range(start=ohlc.index[0], end=ohlc.index[-1], freq='1min')
    diff = len(new_time) - len(ohlc)
    if diff:
        cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time',
                'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore']
        new_mins = []
        count = 1
        for i in new_time:
            if i not in ohlc.index:
                i = i.strftime("%d %b %Y %H:%M:%S")
                count += 1
                new_min = client.get_historical_klines(symbol=pair, interval='1m', start_str=i, end_str=i)
                new_mins.append(new_min[0])
        new_data = pd.DataFrame(new_mins, columns=cols)
        new_data['timestamp'] = pd.to_datetime(new_data['timestamp'], unit='ms')
        new_data.set_index('timestamp', inplace=True)
        ohlc = ohlc.append(new_data)
        ohlc.sort_index(inplace=True)
    return ohlc


def check_valid(pair, ohlc):
    new_dt = pd.date_range(start=ohlc.index[0], end=ohlc.index[-1], freq='1min')
    invalid_dt = 0
    for i in range(len(new_dt) - 1):
        if new_dt[i] != data.index[i]:
            invalid_dt += 1
            break
    #     print(invalid_dt)
    return not invalid_dt


def create_pairs_list(quote, source='ohlc'):
    if source == 'ohlc':
        stored_files_path = Path(f'V:/ohlc_data/')
        files_list = list(stored_files_path.glob(f'*{quote}-1m-data.csv'))
        pairs = [str(pair)[13:-12] for pair in files_list]
    else:
        folders_list = list(source.iterdir())
        pairs = [str(pair.stem) for pair in folders_list]

    return pairs


def load_data(pair):
    filepath = Path(f'V:/ohlc_data/{pair}-1m-data.csv')
    data = pd.read_csv(filepath, index_col=0)

    data.index = pd.to_datetime(data.index)

    return data


def save_data(pair, data):
    filepath = Path(f'V:/ohlc_data/{pair}-1m-data.csv')
    data.to_csv(filepath)
    print(f'{pair} data saved successfuly')


if __name__ == '__main__':

    client = Client(api_key=keys.Pkey, api_secret=keys.Skey)
    usdt_pairs = create_pairs_list('USDT')
    btc_pairs = create_pairs_list('BTC')
    pairs = usdt_pairs + btc_pairs
    pairs = ['XVSUSDT', 'XVSBTC']

    print(f'Starting checks on {time.ctime()[:3]} {time.ctime()[9]} at {time.ctime()[11:-8]}')
    start = time.perf_counter()

    for pair in pairs:
        data = load_data(pair)
        data = drop_dups(data)
        data = find_gaps(pair, data)
        all_good = check_valid(pair, data)
        if all_good:
            save_data(pair, data)
        else:
            print(f'{pair} not fixed yet')

    end = time.perf_counter()
    seconds = round(end - start)
    print(f'Time taken: {seconds // 60} minutes, {seconds % 60} seconds')