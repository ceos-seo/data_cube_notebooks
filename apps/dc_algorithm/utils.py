import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import numpy as np
from collections import Iterable


def create_2d_plot(path, dates=None, datasets=None, data_labels=None, style='', titles=None, vertical=True):
    """Create a 2d image and save it to disk

    Args:
        path: path to save the image
        dates: list of datetimes, will be put on the x axis
        datasets: iterable or list of iterables, plot in seperate figures side by side.
        data_labels: string or list of strings of the same len as datasets, used as axis labels.
        title: string or list of strings of the same len as datasets, used as plot titles.

    """
    _iterable = isinstance(datasets[0], list) or isinstance(datasets[0], np.ndarray)

    datasets = datasets if _iterable else [datasets]
    data_labels = data_labels if _iterable else [data_labels]
    titles = titles if _iterable else [titles]

    plot_count = len(datasets)
    figure = plt.figure(figsize=(6, plot_count * 4)) if vertical else plt.figure(figsize=(plot_count * 6, 4))
    for index, dataset in enumerate(datasets):
        axes = figure.add_subplot(plot_count, 1, index + 1) if vertical else figure.add_subplot(1, plot_count,
                                                                                                index + 1)
        axes.plot(dates, datasets[index], style if isinstance(style, str) else style[index])
        axes.set_title(titles[index])
        axes.set_xlabel('Acquisition Date')
        axes.set_ylabel(data_labels[index])

    figure.tight_layout()
    figure.autofmt_xdate()
    orientation = "portrait" if vertical else "landscape"
    figure.savefig(path, orientation=orientation, format='png')
