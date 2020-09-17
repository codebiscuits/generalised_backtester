import pandas as pd
from functions import load_results, walk_fwd_ranges
from pathlib import Path


def compare_timeframes_back(strat, pair, metric):
    '''
    takes in results from backtesting a pair in all timeframes at a range of param settings, and returns a dataframe of
    statistics about which timeframe was most profitable on average, which had the most consistent returns,
    what param settings actually returned results etc.
    '''

    folder = Path(f'V:/results/{strat}/backtest/{pair}')

    times_list = list(folder.glob('*'))

    # TODO create a set of lengths for each timescale to eliminate duplicates, convert to an ordered list, and look at
    #  the first and last values in the list to return the range of parameter settings which actually produced results

    # TODO create a list for each timescale which you fill with all the values for the chosen metric, from which you can
    #  compute the mean, median, stdev, min and max

    for item in times_list:
        time_scale = item.stem
        params = walk_fwd_ranges.get(time_scale)[:3]
        full_path = item / f'lengths{params[0]}-{params[1]}-{params[2]}.csv'
        results = pd.read_csv(full_path)
        results = results[results['num trades'] >= 30]
        print(f'{"*" * 20} {item} {"*" * 20}')
        print(results)


def compare_timeframes_fwd(strat, pair, metric):
    '''
    takes in results from backtesting a pair in all timeframes at a range of param settings, and returns a dataframe of
    statistics about which timeframe was most profitable on average, which had the most consistent returns,
    what param settings actually returned results etc.
    '''

    folder = Path(f'V:/results/{strat}/walk-forward/{pair}')


    times_list = list(folder.glob('*'))

    # TODO create a set of lengths for each timescale to eliminate duplicates, convert to an ordered list, and look at
    #  the first and last values in the list to return the range of parameter settings which actually produced results

    # TODO create a list for each timescale which you fill with all the values for the chosen metric, from which you can
    #  compute the mean, median, stdev, min and max


    for item in times_list:
        time_scale = item.stem
        params = walk_fwd_ranges.get(time_scale)[:3]
        periods = walk_fwd_ranges.get(time_scale)[-2:]
        subfolder = Path(f'{periods[0]}-{periods[1]}/lengths{params[0]}-{params[1]}-{params[2]}')
        folder_path = item / subfolder
        print(folder_path)
        files_list = list(folder_path.glob('*'))
        for j in range(len(files_list)):
            full_path = folder_path / f'{j+1}.csv'
            results = pd.read_csv(full_path)
            results = results[results['num trades'] >= 30]
            print(results)
            break

compare_timeframes_back('hma_strat', 'ETHBTC', 'sqn')