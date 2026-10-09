import numpy as np
from matplotlib import pyplot as plt
import pandas as pd

df = pd.read_csv('short_track_profile.csv', sep=';', header=1)
points = df.values
distance = points[:, 0]
elevation = points[:, 1]

plt.plot(distance, elevation)
plt.show()
