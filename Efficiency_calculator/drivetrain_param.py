import numpy as np
from scipy.interpolate import RectBivariateSpline

# === Drivetrain Characteristics ===
R_e = 0.23  # m, effective rolling radius
i_tot = 7.0      # total gear ratio motor to wheel
efficiency_battery = 1.0        # 1.0 to disable
efficiency_pow_elen = 1.0       # 1.0 to disable
# efficiency transmission : for a chain from motor to wheel without misalginment, one can say 0.98-0.99
efficiency_transmission = 1.0

# === Electric motor Characteristics ===
T_max = 0.768  # Nm
P_max = 400  # W
omega_base = P_max/T_max  # rad/s
omega_max = 7000 / 60 * 2*np.pi  # RPM -> rad/s

# If specified in the datasheet, it is 0.87 for the maxon 400W, 1.0 to disable
efficiency_motor_max = 0.87

# Efficiency coefficients (define the efficiency map however you want, this is from Golverk formula, given in MECA0527)
# a1, a2, a3, a4, a5, a6 = 0.62, 0.42, 0.38, -0.310, -0.140, -0.360  # option 1

# a1, a2, a3, a4, a5, a6 = 0.55, 0.60, 0.42, -0.40, -0.10, -0.45  # option 2

a1, a2, a3, a4, a5, a6 = 0.87, 0, 0.0, -0.0, -0.0, -0.0  # constant efficiency


class Drivetrain:
    def __init__(self):
        self.R_e = R_e  # [m]
        self.i_tot = i_tot  # [-]
        self.T_max = T_max  # [Nm]
        self.P_max = P_max  # [W]
        self.omega_base = self.P_max / self.T_max  # [rad/s]
        self.omega_max = omega_max  # [rad/s]
        self.F_trac_max = (self.T_max * self.i_tot) / R_e  # [N]

        self.efficiency_battery = efficiency_battery
        self.efficiency_pow_elen = efficiency_pow_elen
        self.efficiency_transmission = efficiency_transmission
        self.efficiency_motor_max = efficiency_motor_max

        self.spline = self._build_efficiency_map()

    def _build_efficiency_map(self) -> RectBivariateSpline:
        """
        Builds the efficiency map (as a 2D spline) of the ENTIRE drivetrain from the Golverk coeff,
        without the max Torque & Power constraints
        """
        torques = np.linspace(0.0, self.T_max, 100)
        omegas = np.linspace(5.0, self.omega_max, 100)
        T_grid, Omega_grid = np.meshgrid(torques, omegas, indexing='ij')

        omega_norm = Omega_grid / self.omega_max
        T_norm = T_grid / self.T_max

        eta = a1 + a2 * T_norm + a3 * omega_norm + a4 * \
            (T_norm ** 2) + a5 * T_norm * omega_norm + a6 * (omega_norm ** 2)
        # limit eta at minimum 0.0 % efficiency
        eta = np.clip(eta, 0.0, self.efficiency_motor_max)

        return RectBivariateSpline(torques, omegas, eta * self.efficiency_battery * self.efficiency_pow_elen, kx=2, ky=2)

    def efficiency_map(self, T, Omega):
        """
        Function returning efficiency of the drivetrain
        Introduces max Torque & Power limitations of the motor
        """
        # Compute torque limit line
        Omega_inverseRegion = np.maximum(Omega, omega_base)
        T_limit = np.where(Omega <= self.omega_base,
                           self.T_max, self.P_max / Omega_inverseRegion)

        # Evaluate the smooth spline (grid=False handles both scalars and coordinate arrays)
        eta_val = self.spline(T, Omega, grid=False)

        # Create a validity mask (inside motor limits and non-negative torque)
        valid = (T >= 0.0) & (T <= T_limit)

        # Return vectorized or scalar result safely using np.where
        # Returns 0.0 if the combination (T,omega) is outside motor capabilities
        if np.isscalar(T) and np.isscalar(Omega):

            return float(eta_val) if valid else 0.0
        else:
            return np.where(valid, eta_val, 0.0)
