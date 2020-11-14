from finta import TA
import talib


### Hull moving average
def hma_calc_old(price, length):
    hma_list = list(TA.HMA(price, length))
    return hma_list

def hma_calc(price, length):
    price['hma'] = TA.HMA(price, length)

def hma_calc_new(price, length):
    return TA.HMA(price, length)

def my_hma(ohlc, period, mode='close'):
    if mode == 'close':
        price = ohlc.loc[:, 'close']
    else:
        pass
    fast_wma = talib.WMA(price, int(period/2))
    slow_wma = talib.WMA(price, period)
    diff = 2*fast_wma - slow_wma
    hma = talib.WMA(diff, int(math.sqrt(period)))
    # print(hma)
    return hma

def percentrank(data):
    '''returns the percentage rank of the last value in the input (pandas series) compared to other values'''
    ranked = data.rank(pct=True)
    return ranked.iloc[-1]

def dvb_calc(data, lb=50, p=2):
    '''https://cssanalytics.wordpress.com/2009/07/29/differential-dv2-calculation/'''
    data['comb'] = data['close'] / (data['high'] + data['low'])
    data['avg'] = data['comb'].rolling(p).mean()
    data['dvb'] = data['avg'].rolling(lb).apply(percentrank, raw=False)
    data.drop(columns=['comb', 'avg'], axis=1, inplace=True)

def dvb_calc_new(data, lb=50, p=2):
    '''https://cssanalytics.wordpress.com/2009/07/29/differential-dv2-calculation/'''
    data['comb'] = data['close'] / (data['high'] + data['low'])
    data['avg'] = data['comb'].rolling(p).mean()
    dvb = data['avg'].rolling(lb).apply(percentrank, raw=False)
    data.drop(columns=['comb', 'avg'], axis=1, inplace=True)
    return dvb
