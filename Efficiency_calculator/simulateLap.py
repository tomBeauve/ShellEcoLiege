import numpy as np
from scipy.optimize import minimize


def lapConsumption_postProcess(vehicle, drivetrain, track, velocity):
    """
    Returns :
    the total electrical energy consumption 
    and 
    all the individual mechanical works / losses to identify where energy goes

    Inputs :
    car parameters, track data and a velocity profile
    (velocity and track.distance arrays must be the same size : the velocity at each point of track.distance)
    """
    v = velocity
    x = track.distance
    z = track.elevation

    # Acceleration via chain rule: a = v * (dv/dx)
    dv_dx = np.gradient(v, x)
    a = v * dv_dx
    dz_dx = np.gradient(z, x)

    # Individual force functions (at wheel level)
    def F_aero(v):
        return 0.5 * 1.225 * vehicle.SCx * v**2

    def F_RR(dz_dx):
        return vehicle.crr * vehicle.mass * 9.81 * np.cos(dz_dx)

    def F_inertia(a):
        return vehicle.mass_e * a

    def F_elevation(dz_dx):
        return vehicle.mass * 9.81 * np.sin(dz_dx)

    # Accumulators for wheel-level work (Joules)
    work_aero = 0.0
    work_rr = 0.0
    work_inertia = 0.0
    work_elevation = 0.0

    # Accumulator for total electrical/source energy (Joules)
    E_tot = 0.0

    # Performs Simpson integration of energy consumed (using point i, i+1 and their mid i+1/2)
    for i in range(len(velocity) - 1):
        x_mid = (x[i] + x[i+1]) / 2.0
        z_mid = (z[i] + z[i+1]) / 2.0
        v_mid = (v[i] + v[i+1]) / 2.0
        a_mid = v_mid * (dv_dx[i] + dv_dx[i+1]) / 2.0
        dz_dx_mid = (dz_dx[i] + dz_dx[i+1]) / 2.0
        deltax = x[i+1] - x[i]

        # --- 1. Evaluate individual forces at start, mid, and end nodes ---
        fa_i, fr_i, fi_i, fe_i = F_aero(v[i]), F_RR(
            dz_dx[i]), F_inertia(a[i]), F_elevation(dz_dx[i])

        fa_mid, fr_mid, fi_mid, fe_mid = F_aero(v_mid), F_RR(
            dz_dx_mid), F_inertia(a_mid), F_elevation(dz_dx_mid)

        fa_e, fr_e, fi_e, fe_e = F_aero(
            v[i+1]), F_RR(dz_dx[i+1]), F_inertia(a[i+1]), F_elevation(dz_dx[i+1])

        # Total tractive force at start, mid, and end nodes
        f_tot_i = fa_i + fr_i + fi_i + fe_i
        f_tot_mid = fa_mid + fr_mid + fi_mid + fe_mid
        f_tot_e = fa_e + fr_e + fi_e + fe_e

        # --- 2. Simpson Integration for individual force work components (Joules) ---
        work_aero += (deltax / 6.0) * (fa_i + 4.0 * fa_mid + fa_e)
        work_rr += (deltax / 6.0) * (fr_i + 4.0 * fr_mid + fr_e)
        work_inertia += (deltax / 6.0) * (fi_i + 4.0 * fi_mid + fi_e)
        work_elevation += (deltax / 6.0) * (fe_i + 4.0 * fe_mid + fe_e)

        # --- 3. Electrical Energy Integrand (Force / Efficiency per meter) ---
        def integrand_electrical(force, vel):
            if force <= 0:
                return 0.0  # coasting consumes zero source energy, no regen

            omega = (vel / drivetrain.R_e) * drivetrain.i_tot
            torque = (force * drivetrain.R_e) / \
                (drivetrain.i_tot * drivetrain.efficiency_transmission)

            eta_raw = drivetrain.efficiency_map(torque, omega)
            # Just in case eta_raw = a single value in an array like [0.97]
            if isinstance(eta_raw, np.ndarray):
                eta_val = eta_raw.item()
            else:
                eta_val = float(eta_raw)

            # efficiency bounded from 0.1 to 1.0 (to avoid some problems)
            eta_clamped = max(min(eta_val, 1.0), 0.1)
            return force / eta_clamped

        val_i = integrand_electrical(f_tot_i, v[i])
        val_mid = integrand_electrical(f_tot_mid, v_mid)
        val_e = integrand_electrical(f_tot_e, v[i+1])

        # Simpson integration for total electrical source energy
        E_tot += (deltax / 6.0) * (val_i + 4.0 * val_mid + val_e)

    return {
        "E_total_electrical": E_tot,
        "Work_Aero": work_aero,
        "Work_RollingResistance": work_rr,
        "Work_Inertia": work_inertia,
        "Work_Elevation": work_elevation,
        "mean_efficiency": (work_aero + work_elevation + work_inertia + work_rr) / E_tot
    }


def lapConsumption_optimize(vehicle, drivetrain, track):
    """
    Optimize the tractive force profile to minimize total electrical energy consumption over a run.
    """

    N = len(track.distance)
    x = track.distance
    z = track.elevation

    g = 9.81
    rho = 1.225

    # initial guess for the optimal force profile,
    # You may change it to see potentially different results
    f_trac_guess = np.ones(N) * 10.0

    def compute_velocity_profile(f_trac):
        """
        Computes the velocity profile that results from a tractive force profile
        """
        v = np.zeros(N)

        # Start from a complete stop (regulation), avoid 0 for numerical problems
        v[0] = 0.001  # or track.min_avg_velocity if you want a warm start

        dz_dx = np.gradient(z, x)

        for i in range(N - 1):
            # Resistive forces at node i
            f_aero = 0.5 * rho * vehicle.SCx * v[i]**2
            f_rr = vehicle.crr * vehicle.mass * g * np.cos(dz_dx[i])
            f_slope = vehicle.mass * g * np.sin(dz_dx[i])

            # Net force
            f_net = f_trac[i] - (f_aero + f_rr + f_slope)

            # Acceleration: a = F_net / m_e
            a = f_net / vehicle.mass_e

            dx = x[i+1] - x[i]
            # Kinematic step: v_{i+1}^2 = v_i^2 + 2 * a * dx ( + prevent negative velocity via clip)
            v_next_sq = v[i]**2 + 2.0 * a * dx
            v[i+1] = np.sqrt(max(0.0, v_next_sq))

        return v

    def objective(f_trac):
        v = compute_velocity_profile(f_trac)
        # Penalty weight : 0.0 to disable, 1.0 seems quite appropriate to damp jitter (if optimal force profile ~smooth)
        w = 0.0
        # Adds a penalization term to avoid jitter in force profile
        return lapConsumption_postProcess(vehicle, drivetrain, track, v)["E_total_electrical"] + w * np.sum((f_trac[1:] - f_trac[:-1])**2)

    constraints = []

    # Constraint: Total lap time must be <= max_time (to enforce v_avg_min)
    def time_constraint(f_trac):
        v = compute_velocity_profile(f_trac)
        v_mid = 0.5 * (v[:-1] + v[1:])
        dx = np.diff(track.distance)
        total_time = np.sum(dx / np.clip(v_mid, 0.01, 30.0))
        return track.max_time - total_time  # Must be >= 0

    constraints.append({'type': 'ineq', 'fun': time_constraint})

    # Bounds for control input (e.g., min force = 0 [coasting], max force = ... N [motor limit])
    bounds = [(0.0, drivetrain.F_trac_max)]

    # Run optimization on force controls
    # One may change 'maxiter' or 'ftol' to get more/less precise, this will impact CPU time strongly
    result = minimize(objective, f_trac_guess, method='SLSQP', bounds=bounds,
                      constraints=constraints, options={'maxiter': 100, 'ftol': 1e-4})

    # Return both the optimal force profile and the resulting velocity profile
    optimal_force = result.x
    optimal_velocity = compute_velocity_profile(optimal_force)
    E_optimal = lapConsumption_postProcess(
        vehicle, drivetrain, track, optimal_velocity)

    return optimal_force, optimal_velocity, E_optimal
