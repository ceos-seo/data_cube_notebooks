import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from collections import Iterable


def create_2d_image(path, dates=None, datasets=None, data_labels=None, titles=None):
    """Create a 2d image and save it to disk

    Args:
        path: path to save the image
        dates: list of datetimes, will be put on the x axis
        datasets: iterable or list of iterables, plot in seperate figures side by side.
        data_labels: string or list of strings of the same len as datasets, used as axis labels.
        title: string or list of strings of the same len as datasets, used as plot titles.

    """
    _iterable = isinstance(datasets[0], list)

    datasets = datasets if _iterable else [datasets]
    data_labels = data_labels if _iterable else [data_labels]
    titles = titles if _iterable else [titles]

    columns = len(datasets)
    figure = plt.figure(figsize=(columns * 6, 4))
    for index, dataset in enumerate(datasets):
        axes = figure.add_subplot(1, columns, index + 1)
        axes.plot(dates, datasets[index])
        axes.set_title(titles[index])
        axes.set_xlabel('Acquisition Date')
        axes.set_ylabel(data_labels[index])

    figure.tight_layout()
    figure.autofmt_xdate()
    figure.savefig(path, orientation="landscape", format='png')
