import pandas as pd
from functions import load_results, walk_fwd_ranges
from pathlib import Path
import statistics
import matplotlib.pyplot as plt


def compare_timeframes_back(strat, pair, metric):
    '''
    takes in results from backtesting a pair in all timeframes at a range of param settings, and returns a dataframe of
    statistics about which timeframe was most profitable on average, which had the most consistent returns,
    what param settings actually returned results etc.
    '''

    folder = Path(f'V:/results/{strat}/backtest/{pair}')

    times_list = list(folder.glob('*'))

    for item in times_list:
        try:
            time_scale = item.stem
            print(f'\n{time_scale}')
            params = walk_fwd_ranges.get(time_scale)[:3]
            full_path = item / f'lengths{params[0]}-{params[1]}-{params[2]}.csv'
            results = pd.read_csv(full_path, index_col=0)
            print(f'Data rows before filter: {len(results)}')
            results = results[results['num trades'] >= 30]
            # results = results[results['sqn'] >= 0]
            print(f'Data rows after filter: {len(results)}')
            if time_scale == '1h':
                x = list(results['length'])
                y = list(results['num trades'])
                z = list(results['sqn'])
            # print(results)
            lengths_set = set(results['length'])
            metric_list = list(results[metric])
            if lengths_set:
                print(f'Lengths range: {min(lengths_set)} - {max(lengths_set)}')
            if len(metric_list) > 2:
                metric_mean = statistics.mean(metric_list)
                metric_med = statistics.median(metric_list)
                metric_stdev = statistics.stdev(metric_list)
                print(f'{metric}\nmean: {metric_mean}\nmedian: {metric_med}\nstandard deviation: {metric_stdev}')
        except:
            pass

    return x, y, z


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
            results = pd.read_csv(full_path, index_col=0)
            results = results[results['num trades'] >= 30]
            print(results)
            break


if __name__ == '__main__':

    x, y, z = compare_timeframes_back('hma_strat', 'ETHBTC', 'sqn')

    # plt.plot(x, y)
    plt.plot(x, z)

    plt.xlabel('hma length')
    plt.ylabel('number of trades generated')
    plt.show()