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