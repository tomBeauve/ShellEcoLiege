import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import re
import os

# --- Global Plotting Configuration ---
mpl.rcParams.update(mpl.rcParamsDefault)
plt.rcParams.update({
    'font.size': 14,
    'axes.labelsize': 14,
    'axes.titlesize': 12,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'lines.linewidth': 2.2
})

##################################################################################################


def scrape_log_file(file_path):
    """Parses OpenFOAM log file for Force Coefficients."""
    time_list, cd_list, cl_list = [], [], []
    iter_pattern = re.compile(r"^Time = (\d+)")
    header_pattern = re.compile(r"forceCoeffsIncompressible write:")
    cd_pattern = re.compile(r"Cd\s+=\s+([eE\d\.-]+)")
    cl_pattern = re.compile(r"Cl\s+=\s+([eE\d\.-]+)")

    current_time = 0
    found_header = False
    temp_cd = None

    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return None

    with open(file_path, 'r') as f:
        for line in f:
            iter_match = iter_pattern.match(line)
            if iter_match:
                current_time = int(iter_match.group(1))
                found_header = False

            if header_pattern.search(line):
                found_header = True
                continue

            if found_header:
                cd_match = cd_pattern.search(line)
                cl_match = cl_pattern.search(line)
                if cd_match:
                    temp_cd = float(cd_match.group(1))
                if cl_match and temp_cd is not None:
                    time_list.append(current_time)
                    cd_list.append(temp_cd)
                    cl_list.append(float(cl_match.group(1)))
                    found_header = False
    return time_list, cd_list, cl_list


def load_postprocessing_file(file_path, skip_rows=9):
    """Loads data from OpenFOAM postProcessing/forceCoeffs.dat."""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return None
    try:
        data = np.loadtxt(file_path)
        # 0=Time, 2=Cd, 3=Cl. Return as lists for easier extending
        return data[skip_rows:, 0].tolist(), data[skip_rows:, 2].tolist(), data[skip_rows:, 3].tolist()
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

##################################################################################################


def process_results(time, cd, cl, label, window_length=200, step=50):
    """Performs plotting, averaging, and stability checks on merged data."""
    print(f"\n{'#'*60}\n# ANALYSIS: {label}\n{'#'*60}")

    # 1. Plotting
    fig, ax1 = plt.subplots(figsize=(8, 5))
    ax1.set_xlabel('Iterations [-]')
    ax1.set_ylabel('$c_d$ [-]', color='tab:red')
    ax1.plot(time, cd, color='tab:red')
    ax1.set_ylim(np.min(cd[100:]), np.max(cd[100:]))
    ax1.tick_params(axis='y', labelcolor='tab:red')

    ax2 = ax1.twinx()
    ax2.set_ylabel('$c_l$ [-]', color='tab:blue')
    ax2.plot(time, cl, color='tab:blue')
    ax2.set_ylim(np.min(cl[100:]), np.max(cl[100:]))
    ax2.tick_params(axis='y', labelcolor='tab:blue')

    plt.title(f"Force Coefficients - {label}")
    fig.tight_layout()
    plt.savefig(f"aero_merged_{label}.png")
    plt.show()

    # 2. Final Window Average
    if len(time) >= window_length:
        win_cd, win_cl = cd[-window_length:], cl[-window_length:]
        cd_m, cl_m = np.mean(win_cd), np.mean(win_cl)
        cd_p2p, cl_p2p = np.ptp(win_cd), np.ptp(win_cl)

        print("-" * 30)
        print(f"Final Average (Last {window_length} iter)")
        print(f"Range: {time[-window_length]} to {time[-1]}")
        print("-" * 30)
        print(
            f"Mean Cd: {cd_m:.6f} (Amp: {cd_p2p:.6f}, {(cd_p2p/cd_m*100):.2f}%)")
        print(
            f"Mean Cl: {cl_m:.6f} (Amp: {cl_p2p:.6f}, {(cl_p2p/cl_m*100):.2f}%)")
        print("-" * 30)

    # 3. --- Moving Average Stability Check ---
    print("\n" + "="*40)
    print("MOVING AVERAGE STABILITY CHECK")
    print("="*40)
    print(f"{'Window Start':<15} | {'Mean Cl':<12} | {'Mean Cd':<12}")
    print("-" * 45)

    current_start = int(time[0])
    while current_start + window_length <= time[-1]:
        mask = (time >= current_start) & (time < current_start + window_length)

        if np.any(mask):
            cl_m_check = np.mean(cl[mask])
            cd_m_check = np.mean(cd[mask])
            print(f"{current_start:<15} | {cl_m_check:<12.6f} | {cd_m_check:<12.6f}")

        current_start += step

##################################################################################################


# --- MAIN EXECUTION ---
if __name__ == "__main__":

    # Aggregator lists
    all_times, all_cd, all_cl = [], [], []

    # SETTINGS: Define your file sources here
    log_sources = ["log.foamRun"]
    post_sources = [
        "postProcessing/forceCoeffsIncompressible/0/forceCoeffs.dat"]

    # 1. Collect from Logs
    for f in log_sources:
        data = scrape_log_file(f)
        if data:
            all_times.extend(data[0])
            all_cd.extend(data[1])
            all_cl.extend(data[2])

    # 2. Collect from PostProcessing
    for f in post_sources:
        data = load_postprocessing_file(f)
        if data:
            all_times.extend(data[0])
            all_cd.extend(data[1])
            all_cl.extend(data[2])

    if not all_times:
        print("No data found in any source.")
        exit()

    # 3. MERGE, SORT, AND DEDUPLICATE
    # Use a dictionary to store unique time: (cd, cl) pairs (last-one-wins on duplicates)
    merged_data = {t: (d, l) for t, d, l in zip(all_times, all_cd, all_cl)}

    # Sort by time
    sorted_times = sorted(merged_data.keys())
    final_time = np.array(sorted_times)
    final_cd = np.array([merged_data[t][0] for t in sorted_times])
    final_cl = np.array([merged_data[t][1] for t in sorted_times])

    # 4. Final Processing
    process_results(final_time, final_cd, final_cl,
                    label="Merged_Chronological")
