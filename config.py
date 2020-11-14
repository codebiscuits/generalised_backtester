ind_cache = {'p1': {}, 'p2': {}, 'p3': {}} # The indicator cache is stored in this 'config' module, which is exclusively
# for global variables. i import the config module in every other module so that these global variables are available
# everywhere without any danger of circular imports. So the variable is available to all functions in the 'functions'
# module and the strategy function can set values (and keys) inside it without issue, but the 'optimise_backtest'
# function does an explicit assignment to the variable name so must invoke the global keyword first to tell python its
# not making a new local variable.

exp_ranges = {
        # '1w': ({'hma': (2, 23, 20), 'dvb': (2, 23, 20)}, 0.142857, 50, 1),
        # '3d': ({'hma': (3, 23, 20), 'dvb': (3, 23, 20)}, 0.333333, 50, 1),
        # '1d': ({'hma': (3, 443, 40), 'dvb': (3, 23, 20)}, 1, 90, 1),
        # '12h': ({'hma': (3, 200, 60), 'dvb': (3, 200, 20)}, 2, 360, 4),
        # '4h': ({'hma': (3, 400, 60), 'dvb': (3, 200, 20)}, 6, 1000, 12),
        # '1h': ({'hma': (3, 500, 60), 'dvb': (3, 300, 20)}, 24, 2000, 50),
        # '30min': ({'hma': (3, 500, 60), 'dvb': (3, 400, 20)}, 48, 3000, 75),
        # '15min': ({'hma': (3, 1000, 60), 'dvb': (3, 600, 20)}, 96, 6000, 150),
        # '5min': ({'hma': (3, 1000, 60), 'dvb': (3, 800, 20)}, 288, 18000, 450),
        '1min': ({'hma': (3, 1000, 60), 'dvb': (3, 1000, 20)}, 1440, 80000, 2000)
        }

