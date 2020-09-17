import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import imageio

pair = 'ETHBTC'
timescale = '1h'
train_str = '2000-50'
params = 'lengths5-501-2'
# i = 101
folder = Path(f'V:/results/hma_strat/walk-forward/{pair}/{timescale}/{train_str}/{params}')
files_list = list(folder.glob('*.csv'))
# print(f'files_list: {files_list}')
set_num_list = sorted(int(file.stem) for file in files_list)
# print(f'set_num_list: {set_num_list}')
for i in set_num_list:
    file_path = Path(folder / f'{i}.csv')
    img_path = Path(folder / 'images' / f'{i}.png')

    df = pd.read_csv(file_path, index_col=0)
    df = df.loc[df['num trades'] > 30]

    # print(df['sqn'])

    plt.plot(df['sqn'])
    # plt.plot(df['num trades'])
    plt.xlabel('length')
    plt.ylabel('sqn')
    plt.title(i)
    # plt.show()
    plt.savefig(img_path)
    plt.clf()

# TODO find a way to stitch together all the png images into a gif or avi or something to watch the plot evolve

image_path = Path(folder / 'images')
images = list(image_path.glob('*.png'))
image_list = []
for x in range(1, len(images)+1):
    print(f'Processing {x}')
    image_list.append(imageio.imread(Path(folder / 'images' / f'{x}.png')))

imageio.mimwrite(Path(folder / 'images' / 'animated_from_images.gif'), image_list)