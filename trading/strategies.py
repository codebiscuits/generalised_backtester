from trading.indicators import *
from config import ind_cache


def hma_dvb_strat(price, args):
    hma_len, dvb_lb = args

    hma_calc(price, hma_len)
    dvb_calc(price, dvb_lb)

    prev = None
    signals = []
    colours = []
    for i in range(len(price)):
        if price.hma[i] > price.hma[i - 2] and price.hma[i - 1] > price.hma[i - 3] and price.dvb[i] < 0.25 and (prev == 'r' or prev == None):
            signal = (i, 'b', price.close[i])
            signals.append(signal)
            colours.append('g')
            prev = 'g'
        elif price.hma[i] < price.hma[i - 2] and price.hma[i - 1] < price.hma[i - 3] and price.dvb[i] > 0.75 and (prev == 'g' or prev == None):
            signal = (i, 's', price.close[i])
            signals.append(signal)
            colours.append('r')
            prev = 'r'
        else:
            colours.append(prev)

    price['bg_col'] = colours
    return signals

def hma_dvb_strat_new(price, args):
    global ind_cache
    hma_len, dvb_lb = args

    # print(f'hma_len: {hma_len}, dvb_lb: {dvb_lb}')

    if hma_len in ind_cache['p1']:
        price['hma'] = ind_cache['p1'].get(hma_len)
    else:
        hma = hma_calc_new(price, hma_len)
        price['hma'] = hma
        ind_cache['p1'][hma_len] = hma

    if dvb_lb in ind_cache['p2']:
        price['dvb'] = ind_cache['p2'].get(dvb_lb)
    else:
        dvb = dvb_calc_new(price, dvb_lb)
        price['dvb'] = dvb
        ind_cache['p2'][dvb_lb] = dvb

    prev = None
    signals = []
    colours = []
    for i in range(len(price)):
        if price.hma[i] > price.hma[i - 2] and price.hma[i - 1] > price.hma[i - 3] and price.dvb[i] < 0.25 and (prev == 'r' or prev == None):
            signal = (i, 'b', price.close[i])
            signals.append(signal)
            colours.append('g')
            prev = 'g'
        elif price.hma[i] < price.hma[i - 2] and price.hma[i - 1] < price.hma[i - 3] and price.dvb[i] > 0.75 and (prev == 'g' or prev == None):
            signal = (i, 's', price.close[i])
            signals.append(signal)
            colours.append('r')
            prev = 'r'
        else:
            colours.append(prev)

    price['bg_col'] = colours
    return signals

# TODO write some risk management into the strategies, either trailing stop or fixed stop and tp

### calls hma_calc to produce a list of tuples containing signals: (index, b/s, price)
def hma_strat(price, length):
    hma = hma_calc_old(price, length)

    signals = []
    for i in range(len(price)):
        if hma[i] > hma[i-2] and hma[i-1] > hma[i-3]:
            signal = (i, 'b', price)
            signals.append(signal)
        if hma[i] < hma[i-2] and hma[i-1] < hma[i-3]:
            signal = (i, 's', price)
            signals.append(signal)

    return signals

### calls aggregate_results to produce a list of tuples containing signals: (index, b/s, price)
def hma_strat_forward(best, price):
    start = time.perf_counter()
    new_price, hma = aggregate_results(best, price)
    # hma = aggregate_results_multi(best, price)
    end = time.perf_counter()
    total = end - start
    print(f'agg results calculated in {total // 60}m {round(total % 60)}s')


    signals = []
    print(f'(hma_strat_fwd) len(price): {len(new_price)}, len(hma): {len(hma)}')
    for i in range(len(hma)):
        # print(f'i: {i}')
        if hma[i] > hma[i-2] and hma[i-1] > hma[i-3]:
            signal = (i, 'b')
            signals.append(signal)
        if hma[i] < hma[i-2] and hma[i-1] < hma[i-3]:
            signal = (i, 's')
            signals.append(signal)

    return signals, new_price, hma

#TODO create hma_dvb_strat and hma_dvb_strat_fwd

strat_dict = {'hma': {'name': 'hma_strat', 'func': hma_strat, 'params': ['hma']},
              'hma_dvb': {'name': 'hma_dvb', 'func': hma_dvb_strat_new, 'params': ['hma', 'dvb']},
              }