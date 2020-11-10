ind_cache = {'p1': {}, 'p2': {}, 'p3': {}} # The indicator cache is stored in this 'config' module, which is exclusively
# for global variables. i import the config module in every other module so that these global variables are available
# everywhere without any danger of circular imports. So the variable is available to all functions in the 'functions'
# module and the strategy function can set values (and keys) inside it without issue, but the 'optimise_backtest'
# function does an explicit assignment to the variable name so must invoke the global keyword first to tell python its
# not making a new local variable.