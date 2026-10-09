import numpy as np
import pandas as pd


def build_precise_short_track(full_distance, full_elevation, s_start=2370.0, s_end=3600.0, L_bridge=48.3):
    """
    Builds the precise short track profile:
    1. Interpolates exact elevation at s_start and s_end from full track data.
    2. Extracts all true track data points between s_start and s_end, shifting distance by -s_start.
    3. Appends the final interpolated return bridge point of length L_bridge.
    """

    # 1. Exact interpolation at start (2370m) and end (3600m)
    z_start = np.interp(s_start, full_distance, full_elevation)
    z_end = np.interp(s_end, full_distance, full_elevation)

    # 2. Extract true track points strictly between s_start and s_end
    mask = (full_distance >= s_start) & (full_distance <= s_end)
    true_x_segment = full_distance[mask] - s_start
    true_z_segment = full_elevation[mask]

    # Prepend the exact interpolated start point if not precisely on a grid point
    if true_x_segment[0] > 0.0:
        true_x_segment = np.insert(true_x_segment, 0, 0.0)
        true_z_segment = np.insert(true_z_segment, 0, z_start)
    else:
        true_z_segment[0] = z_start  # Force exact interpolated elevation

    # Append the exact interpolated end point of the real track section
    if true_x_segment[-1] < (s_end - s_start):
        true_x_segment = np.append(true_x_segment, s_end - s_start)
        true_z_segment = np.append(true_z_segment, z_end)
    else:
        true_z_segment[-1] = z_end

    # 3. Add the final point for the straight connector bridge
    # The bridge goes from x = (s_end - s_start) to x = (s_end - s_start) + L_bridge
    # Its final elevation must match the start elevation (z_start) to close the circuit loop smoothly.
    total_short_length = (s_end - s_start) + L_bridge

    short_distance = np.append(true_x_segment, total_short_length)
    short_elevation = np.append(true_z_segment, z_start)

    return short_distance, short_elevation


df = pd.read_csv('fullTrackAltimetry.csv', sep=';', decimal=',', header=None)
points = df.values
distance = points[:, 0]
elevation = points[:, 1]


cut_distance, cut_z = build_precise_short_track(
    distance, elevation, s_start=2370, s_end=3600)

export_data = np.column_stack((cut_distance, cut_z))

np.savetxt(
    'short_track_profile.csv',
    export_data,
    delimiter=';',
    fmt='%.4f',
    header='distance_m;elevation_m',
    comments=''
)
