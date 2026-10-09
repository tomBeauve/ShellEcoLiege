from scipy.interpolate import interp1d
import pandas as pd
from track_param import Track
import numpy as np
import matplotlib.pyplot as plt
from drivetrain_param import Drivetrain

data = np.load("optimal_run.npz")


df = pd.read_csv('altimetry_profile/silesa_western_tom.csv', sep=';', header=0)
points = df.values
racetrack_x = points[:, 0]
racetrack_z = points[:, 1]
racetrack_length = racetrack_x[-1]


def plotvlines(distance):
    return
    # Lap boundaries within the plotted distance range
    k_min = int(np.ceil(distance.min() / racetrack_length))
    k_max = int(np.floor(distance.max() / racetrack_length))

    for k in range(k_min, k_max + 1):
        x = k * racetrack_length

        # Avoid drawing a line exactly at the plot boundaries
        if distance.min() < x < distance.max():
            plt.axvline(
                x=x,
                color='red',
                linestyle=':',
                linewidth=1
            )


# Extract the variables
optimal_force = data["force"]
optimal_velocity = data["velocity"]
distance = data["distance"]
E_optimal = {
    "E_total_electrical": float(data["E_total_electrical"]),
    "Work_Aero": float(data["Work_Aero"]),
    "Work_RollingResistance": float(data["Work_RollingResistance"]),
    "Work_Inertia": float(data["Work_Inertia"]),
    "Work_Elevation": float(data["Work_Elevation"])
}


plt.plot(distance, optimal_velocity, label='Optimal Velocity [m/s]')
plotvlines(distance)

plt.xlabel('Distance [m]', fontsize=12)
plt.ylabel('Velocity [m/s]', fontsize=12)
plt.title('Optimal Velocity Profile', fontsize=14, fontweight='bold')
plt.savefig('imagesMain/optimal_velocity_profile.png',
            dpi=300, bbox_inches='tight')
plt.close()

plt.plot(distance, optimal_force, label='Optimal Force [N]')
plotvlines(distance)
plt.xlabel('Distance [m]', fontsize=12)
plt.ylabel('Force [N]', fontsize=12)
plt.title('Optimal force Profile', fontsize=14, fontweight='bold')
plt.savefig('imagesMain/optimal_force_profile.png',
            dpi=300, bbox_inches='tight')
plt.close()


categories = ['Aerodynamics', 'Rolling Resistance', 'Inertia', 'Elevation']
values = [
    E_optimal["Work_Aero"],
    E_optimal["Work_RollingResistance"],
    E_optimal["Work_Inertia"],
    E_optimal["Work_Elevation"]
]


abs_values = [abs(v) for v in values]
total_work = sum(abs_values)

percentages = [(v / total_work) * 100 for v in values]

# 3. Create the bar chart
plt.figure(figsize=(8, 5))
bars = plt.bar(categories, percentages, color=[
               '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'], edgecolor='black', alpha=0.85)

# Add data labels on top of each bar
for bar, pct in zip(bars, percentages):
    height = bar.get_height()
    plt.text(
        bar.get_x() + bar.get_width() / 2.0,
        height + 1.0,
        f"{pct:.1f}%",
        ha='center',
        va='bottom',
        fontsize=10,
        fontweight='bold'
    )

plt.ylim(0, max(percentages) + 15)  # Give breathing room for labels
plt.title('Energy Consumption Breakdown by Force Component',
          fontsize=12, fontweight='bold')
plt.ylabel('Percentage of Total Work [%]', fontsize=11)
plt.grid(axis='y', linestyle='--', alpha=0.5)

plt.tight_layout()
plt.savefig('imagesMain/energy_consumption_breakdown.png',
            dpi=300, bbox_inches='tight')
plt.close()


print("Total Electrical Energy Consumption (Joules):",
      E_optimal["E_total_electrical"])

w = 2.0
print("jitter objective :",  w *
      np.sum((optimal_force[1:] - optimal_force[:-1])**2))


##################

drivetrain = Drivetrain()

# Create the torque and speed meshgrids for evaluation
torques = np.linspace(0.0, drivetrain.T_max, 1000)
omegas = np.linspace(5.0, drivetrain.omega_max, 1000)
T_mesh, Omega_mesh = np.meshgrid(torques, omegas, indexing='ij')

# Evaluate efficiency across the 2D mesh arrays directly
eta_grid = drivetrain.efficiency_map(T_mesh, Omega_mesh)

# Convert omega to RPM for the main plot axis
RPM_mesh = Omega_mesh * 60.0 / (2.0 * np.pi)

# --- Plotting ---
fig, ax = plt.subplots(figsize=(8, 6))

contour = ax.contourf(RPM_mesh, T_mesh, eta_grid *
                      100.0, levels=40, cmap='viridis')
cbar = fig.colorbar(contour, ax=ax)
cbar.set_label('Efficiency [%]', fontsize=11)

contour_lines = ax.contour(
    RPM_mesh, T_mesh, eta_grid * 100.0, levels=10, colors='white', linewidths=0.6)
ax.clabel(contour_lines, inline=True, fmt='%.1f%%', fontsize=9)

ax.set_title('Drivetrain & Motor Efficiency Map',
             fontsize=12, fontweight='bold')
ax.set_xlabel('Motor Speed [RPM]', fontsize=11)
ax.set_ylabel('Motor Torque [Nm]', fontsize=11)
ax.grid(True, linestyle='--', alpha=0.3)

# --- Secondary Axes (Top & Right) ---
# Conversion functions for X-axis (RPM -> Vehicle Speed in m/s)


def rpm_to_velocity(rpm):
    omega_rads = rpm * 2.0 * np.pi / 60.0
    return (omega_rads * drivetrain.R_e) / drivetrain.i_tot


def velocity_to_rpm(v):
    omega_rads = (v * drivetrain.i_tot) / drivetrain.R_e
    return omega_rads * 60.0 / (2.0 * np.pi)


ax_top = ax.secondary_xaxis(
    'top', functions=(rpm_to_velocity, velocity_to_rpm))
ax_top.set_xlabel('Vehicle Speed [m/s]', fontsize=11)

# Conversion functions for Y-axis (Motor Torque -> Wheel Tractive Force in N)


def torque_to_force(t_motor):
    return (t_motor * drivetrain.i_tot) / drivetrain.R_e


def force_to_torque(f_trac):
    return (f_trac * drivetrain.R_e) / drivetrain.i_tot


ax_right = ax.secondary_yaxis(
    'right', functions=(torque_to_force, force_to_torque))
ax_right.set_ylabel('Tractive Force [N]', fontsize=11)

plt.tight_layout()
plt.savefig('imagesMain/efficiencyMap.png', dpi=300, bbox_inches='tight')
plt.close()


# ALTIMETRY PLOT
track = Track()

df = pd.read_csv('altimetry_profile/silesa_western_tom.csv', sep=';', header=0)
points = df.values
racetrack_x = points[:, 0]
racetrack_z = points[:, 1]
racetrack_length = racetrack_x[-1]
plot_x = np.arange(0, track.run_length + 1.0, 1.0)
wrapped_x = plot_x % racetrack_length

# Quadratic interpolation
interpolation = interp1d(
    racetrack_x,
    racetrack_z,
    kind='linear',
    bounds_error=False
)
plotvlines(distance)

# Interpolated elevation
plot_z = interpolation(wrapped_x)

plt.plot(plot_x, plot_z,
         label="true elevation interpolated ")

plt.plot(track.distance, track.elevation,
         label="track.elevation ")
plt.title('Altimetry profile',
          fontsize=12, fontweight='bold')
plt.legend()
plt.ylabel('Elevation [m]', fontsize=11)
plt.xlabel('Distance [m]', fontsize=11)
plt.savefig("imagesMain/altimetry.png",  dpi=300, bbox_inches='tight')
plt.close()
