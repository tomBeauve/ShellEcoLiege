import numpy as np
import pandas as pd
# 1. Load your dataset from the text string
df = pd.read_csv('cut_Track_2DPoints.csv', sep=';', decimal=',', header=None)
points = df.values

# 2. Compute segment lengths and cumulative pixel distance
differences = np.diff(points, axis=0)
segment_lengths = np.sqrt(np.sum(differences**2, axis=1))
pixel_distance = np.insert(np.cumsum(segment_lengths), 0, 0.0)
total_pixel_length = pixel_distance[-1]

print(f"Total Traced Screen Length: {total_pixel_length:.2f} pixels")

# 3. Scale to real-world distance (meters)
# Assuming you know the total length of this specific short circuit configuration (e.g., L_short meters)
# Or if you are scaling relative to the full track layout:
L_full_circuit = 3600.0  # [m]
# scale_factor = L_full_circuit / total_pixel_length  # (meters per pixel)
