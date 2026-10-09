import numpy as np
import pandas as pd
from scipy.interpolate import interp1d


df = pd.read_csv('altimetry_profile/silesa_western_tom.csv', sep=';', header=0)
points = df.values
racetrack_x = points[:, 0]
racetrack_z = points[:, 1]

lap_distance = racetrack_x[-1]
run_length = 7.0 * lap_distance  # m
min_avg_velocty = 7.0  # m/s


class Track:
    def __init__(self):
        self.run_length = run_length  # [m]
        self.min_avg_velocity = min_avg_velocty  # [m/s]
        self.max_time = self.run_length / self.min_avg_velocity  # [s]

        dx = 50
        # nb_points = int(run_length / dx)+1
        self.distance = np.arange(0, run_length + dx, dx)

        # --------------------------------------------------
        # Altimetry interpolation
        # --------------------------------------------------
        altimetry_length = racetrack_x[-1]
        wrapped_x = self.distance % altimetry_length

        # Quadratic interpolation
        interpolation = interp1d(
            racetrack_x,
            racetrack_z,
            kind='linear',
            bounds_error=False
        )

        # Interpolated elevation
        self.elevation = interpolation(wrapped_x)
