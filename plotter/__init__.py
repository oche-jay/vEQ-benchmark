'''
Created on 13 Feb 2015

@author: oche
'''
def plot(alist, title=None):
    import matplotlib.pyplot as plt
    plt.plot(alist)
    if title is None:
        title = "Bitrate"
    plt.ylabel(title)
    plt.savefig(title + ".jpg")
    plt.show()
