import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

mpl.rcParams.update(mpl.rcParamsDefault)

plt.rcParams.update({
    'font.size': 14,
    'axes.labelsize': 14,
    'axes.titlesize': 14,
    'xtick.labelsize': 12,
    'ytick.labelsize': 12
})
plt.rcParams['lines.linewidth'] = 2.2


#############

TIME_START = 0
time_start_plot = 150


def load(path):
    return np.loadtxt(path)


forces_total = load(
    f"postProcessing/forceCoeffsIncompressible/{TIME_START}/forceCoeffs.dat")
forces_body = load(f"postProcessing/bodyForces/{TIME_START}/forceCoeffs.dat")
forces_FW = load(
    f"postProcessing/frontWingForces/{TIME_START}/forceCoeffs.dat")
forces_RW = load(f"postProcessing/rearWingForces/{TIME_START}/forceCoeffs.dat")
forces_wh = load(f"postProcessing/wheelsForces/{TIME_START}/forceCoeffs.dat")

time = forces_total[time_start_plot+9:, 0]

data = {
    "Total": forces_total,
    "Body": forces_body,
    "Front wing": forces_FW,
    "Rear wing": forces_RW,
    # "Wheels": forces_wh
}

fig, axes = plt.subplots(len(data), 1, figsize=(10, 12), sharex=True)

for ax, (name, f) in zip(axes, data.items()):

    cd = f[time_start_plot+9:, 2]
    cl = f[time_start_plot+9:, 3]

    ax.set_title(name)

    # Cd (left axis)
    color1 = "tab:red"
    ax.set_ylabel(r"$c_d$", color=color1)
    ax.plot(time, cd, color=color1)
    ax.tick_params(axis='y', labelcolor=color1)
    ax.grid(True)

    # Cl (right axis)
    ax2 = ax.twinx()
    color2 = "tab:blue"
    ax2.set_ylabel(r"$c_l$", color=color2)
    ax2.plot(time, cl, color=color2)
    ax2.tick_params(axis='y', labelcolor=color2)

axes[-1].set_xlabel("Iterations [-]")

plt.tight_layout()
plt.savefig("aeroCoeffs.png", dpi=300)
plt.show()
