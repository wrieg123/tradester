import matplotlib.pyplot as plt
import numpy as np


def graph_states(stateful, name = None):
    labels, data = [*zip(*stateful.items())]
    plt.boxplot(data)
    plt.xticks(range(1, len(labels)+1), labels)
    if name:
        plt.title(name)
    plt.show()


