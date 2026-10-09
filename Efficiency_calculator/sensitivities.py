import numpy as np
import matplotlib.pyplot as plt
from vehicle_param import Vehicle
from drivetrain_param import Drivetrain
from track_param import Track
from simulateLap import lapConsumption_optimize

# ==========================================
# 1. BASELINE PARAMETERS
# ==========================================
track = Track()
vehicle_baseline = Vehicle()
drivetrain = Drivetrain()


def compute_efficiency(E_total_joules):
    # Helper function to compute efficiency (km/kWh) from energy (J)
    energy_kwh = E_total_joules / 3_600_000.0
    total_dist_km = track.run_length / 1000.0
    return total_dist_km / energy_kwh if energy_kwh > 0 else 0.0


# Run baseline first
print("Running baseline optimization...")
_, _, E_base = lapConsumption_optimize(vehicle_baseline, drivetrain, track)
baseline_eff = compute_efficiency(E_base["E_total_electrical"])
print(f"Baseline Efficiency: {baseline_eff:.2f} km/kWh\n")

# ==========================================
# 2. SENSITIVITY ANALYSIS (± 10% Perturbation)
# ==========================================
parameters = ["Mass", "SCx", "Crr"]
perturbation = 0.10  # 10% change
eff_minus_list = []
eff_plus_list = []

print("Running sensitivity analysis...")
for name in parameters:
    # Test +10%
    v_plus = Vehicle()
    if name == "Mass":
        v_plus.car_mass *= (1.0 + perturbation)
    elif name == "SCx":
        v_plus.SCx *= (1.0 + perturbation)
    elif name == "Crr":
        v_plus.crr *= (1.0 + perturbation)

    _, _, E_plus = lapConsumption_optimize(v_plus, drivetrain, track)
    eff_plus = compute_efficiency(E_plus["E_total_electrical"])
    eff_plus_list.append(eff_plus)

    # Test -10%
    v_minus = Vehicle()
    if name == "Mass":
        v_minus.car_mass *= (1.0 - perturbation)
    elif name == "SCx":
        v_minus.SCx *= (1.0 - perturbation)
    elif name == "Crr":
        v_minus.crr *= (1.0 - perturbation)

    _, _, E_minus = lapConsumption_optimize(v_minus, drivetrain, track)
    eff_minus = compute_efficiency(E_minus["E_total_electrical"])
    eff_minus_list.append(eff_minus)

# ==========================================
# PLOTTING SENSITIVITY CHART
# ==========================================
plt.figure(figsize=(7, 4))
y_pos = np.arange(len(parameters))

pct_minus = [(m - baseline_eff) / baseline_eff * 100.0 for m in eff_minus_list]
pct_plus = [(p - baseline_eff) / baseline_eff * 100.0 for p in eff_plus_list]

xerr_lower = []
xerr_upper = []
for m, p in zip(pct_minus, pct_plus):
    min_val = min(m, p)
    max_val = max(m, p)
    # Distance from 0% baseline
    xerr_lower.append(0.0 - min_val)
    xerr_upper.append(max_val - 0.0)

xerr = np.array([xerr_lower, xerr_upper])

plt.errorbar(
    [0.0] * len(parameters),
    y_pos,
    xerr=xerr,
    fmt='o',
    color='black',
    elinewidth=2.5,
    capsize=4,
    markersize=6,
    zorder=3
)

plt.yticks(y_pos, parameters)
plt.axvline(0.0, color='gray', linestyle='--', linewidth=0.8, label='Baseline')
plt.title('Parameter Sensitivity Analysis (Efficiency % Shift for ±10% Variation)',
          fontsize=11, fontweight='bold')
plt.xlabel('Relative Efficiency Change [%]', fontsize=10)
plt.legend(loc='lower right')
plt.grid(axis='x', linestyle='--', alpha=0.3)
plt.tight_layout()
plt.savefig('images/sensitivity_analysis.png', dpi=300, bbox_inches='tight')
plt.close()


# ==========================================
# 3. MASS vs. SCx TRADE-OFF MAP SWEEP
# ==========================================

print("\nRunning Mass vs SCx trade-off grid sweep...")
car_mass_sweep = np.linspace(35, 60, 5)
SCx_sweep = np.linspace(0.02, 0.06, 5)

M_grid, SCx_grid = np.meshgrid(car_mass_sweep, SCx_sweep)
Eff_grid = np.zeros_like(M_grid)

for i in range(len(SCx_sweep)):
    for j in range(len(car_mass_sweep)):
        print(
            f"Evaluating Mass: {car_mass_sweep[j]} kg, SCx: {SCx_sweep[i]} m^2...")
        v_sweep = Vehicle()
        v_sweep.car_mass = car_mass_sweep[j]
        v_sweep.SCx = SCx_sweep[i]

        _, _, E_grid = lapConsumption_optimize(v_sweep, drivetrain, track)
        Eff_grid[i, j] = compute_efficiency(E_grid["E_total_electrical"])

# ==========================================
# 4. PLOTTING TRADE-OFF CONTOUR MAP
# ==========================================
plt.figure(figsize=(8, 6))
contour = plt.contourf(M_grid, SCx_grid, Eff_grid, levels=20, cmap='plasma')
cbar = plt.colorbar(contour)
cbar.set_label('Efficiency [km/kWh]', fontsize=11)

contour_lines = plt.contour(
    M_grid, SCx_grid, Eff_grid, levels=10, colors='white', linewidths=0.6)
plt.clabel(contour_lines, inline=True, fmt='%.1f', fontsize=9)

plt.scatter(vehicle_baseline.car_mass, vehicle_baseline.SCx, color='cyan', s=100,
            edgecolors='black', label='Current Baseline', zorder=5)

plt.title('Vehicle Efficiency Trade-Off: Mass vs. Aerodynamic Drag ($C_d A$)',
          fontsize=12, fontweight='bold')
plt.xlabel('Total Vehicle Mass [kg]', fontsize=11)
plt.ylabel('Aerodynamic Drag Area ($C_d A$) [m^2]', fontsize=11)
plt.legend(loc='upper left')
plt.grid(True, linestyle='--', alpha=0.3)
plt.tight_layout()
plt.savefig('images/mass_vs_SCx_tradeoff.png', dpi=300, bbox_inches='tight')
plt.close()
