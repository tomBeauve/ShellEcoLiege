import numpy as np

from vehicle_param import Vehicle
from drivetrain_param import Drivetrain
from track_param import Track
from simulateLap import lapConsumption_optimize
from time import time

# Initialize domain objects
vehicle = Vehicle()
drivetrain = Drivetrain()
track = Track()

start = time()
optimal_force, optimal_velocity, E_optimal = lapConsumption_optimize(
    vehicle, drivetrain, track
)
print("Elapsed time for opt:", round(time() - start, 2))
np.savez(
    "results/optimalRun/optimal_run.npz",
    force=optimal_force,
    velocity=optimal_velocity,
    distance=track.distance,
    **E_optimal
)

E_opt_elec = E_optimal["E_total_electrical"]
energy_kwh = E_opt_elec / 3600000.0
total_dist_km = track.run_length / 1000.0
efficiency_km_kwh = total_dist_km / energy_kwh

print(f"Efficiency: {efficiency_km_kwh:.2f} km/kWh")
