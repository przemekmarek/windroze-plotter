import streamlit as st
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import io
import os
import tempfile
from pathlib import Path


def read_windographer_tab(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    lines = [line.strip() for line in lines if line.strip()]
    line2_parts = [x for x in lines[2].split('\t') if x]
    num_sectors = int(line2_parts[0])
    dir_freq_parts = [float(x) for x in lines[3].split('\t') if x and x.replace('.', '').replace('-', '').isdigit()]
    direction_frequencies = np.array(dir_freq_parts)
    speed_bins = []
    speed_data = []
    for line in lines[4:]:
        if line:
            parts = line.split('\t')
            if len(parts) > 1:
                try:
                    speed_bin = float(parts[0])
                    frequencies = [float(x) for x in parts[1:] if x and x.replace('.', '').replace('-', '').isdigit()]
                    if len(frequencies) == num_sectors:
                        speed_bins.append(speed_bin)
                        speed_data.append(frequencies)
                except ValueError:
                    continue
    return np.array(speed_bins), direction_frequencies, np.array(speed_data), num_sectors


def rebin_to_custom_intervals(speed_bins, speed_matrix):
    max_speed = int(np.ceil(speed_bins[-1]))
    speed_boundaries = [0, 3, 9, 13, 25, max_speed]
    new_speed_matrix = np.zeros((len(speed_boundaries)-1, speed_matrix.shape[1]))
    new_speed_bins = []
    for i in range(len(speed_boundaries)-1):
        new_speed_bins.append(speed_boundaries[i+1])
    for i in range(len(speed_boundaries)-1):
        lower_bound = speed_boundaries[i]
        upper_bound = speed_boundaries[i+1]
        mask = (speed_bins > lower_bound) & (speed_bins <= upper_bound)
        if np.any(mask):
            new_speed_matrix[i] = np.sum(speed_matrix[mask], axis=0)
    return np.array(new_speed_bins), new_speed_matrix


def get_color_schemes():
    return {
        "Caribbean Sea": {
            "colors": ['#cce5e5', "#7cd3d3", "#39ACAC", '#006666', "#420202", "#8F0058", "#FF0000"],
            "freq_color": "#39ACAC"
        },
        "Blood Orange": {
            "colors": ['#ffb3b3', '#ff6666', '#cc0000', '#800000', '#4d0000', '#1a0000'],
            "freq_color": "#a70000"
        },
        "Autumn Leaves": {
            "colors": ["#fff36d", '#ffd700', '#daa520', '#b8860b', '#8b6914', '#654321'],
            "freq_color": '#daa520'
        }
    }


def create_frequency_distribution_plot(speed_bins, speed_matrix, dir_frequencies, figsize=(10, 6), max_x_axis=None, x_axis_resolution=1, color_scheme="Caribbean Sea"):
    weighted_speed_matrix = np.zeros_like(speed_matrix, dtype=float)
    for sector_idx in range(len(dir_frequencies)):
        weighted_speed_matrix[:, sector_idx] = (speed_matrix[:, sector_idx] / 1000.0) * dir_frequencies[sector_idx]
    total_frequencies = np.sum(weighted_speed_matrix, axis=1)
    shifted_speed_bins = speed_bins - 0.5
    fig, ax = plt.subplots(figsize=figsize, facecolor='white')
    schemes = get_color_schemes()
    color = schemes[color_scheme]["freq_color"]
    ax.bar(shifted_speed_bins, total_frequencies, width=0.8, color=color, edgecolor='white', linewidth=0.5, alpha=0.9)
    ax.set_xlabel('Wind speed bin [m/s]', fontsize=20, color='#000000')
    ax.set_ylabel('Frequency [%]', fontsize=20, color='#000000')
    ax.grid(True, alpha=0.3, color='#BDBDBD', linewidth=0.8, axis='y')
    ax.set_facecolor('white')
    ax.tick_params(axis='both', colors='#000000', labelsize=12)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#BDBDBD')
    ax.spines['bottom'].set_color('#BDBDBD')
    if max_x_axis is None:
        max_x_axis = shifted_speed_bins[-1] + 1
    ax.set_xlim(0, max_x_axis)
    tick_positions = shifted_speed_bins[::x_axis_resolution]
    tick_positions = tick_positions[tick_positions <= max_x_axis]
    ax.set_xticks(tick_positions)
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'{int(x)}%'))
    plt.tight_layout()
    return fig


def create_wind_rose_with_speed_bins(filepath, figsize=(12, 12), title=None, save_path=None, gap_degrees=5,
                                     freq_max_x_axis=None, freq_x_axis_resolution=1, color_scheme="Caribbean Sea"):
    speed_bins, dir_frequencies, speed_matrix, num_sectors = read_windographer_tab(filepath)
    freq_fig = create_frequency_distribution_plot(speed_bins, speed_matrix, dir_frequencies,
                                                  max_x_axis=freq_max_x_axis,
                                                  x_axis_resolution=freq_x_axis_resolution,
                                                  color_scheme=color_scheme)
    speed_matrix = speed_matrix / 10.0
    new_speed_bins, new_speed_matrix = rebin_to_custom_intervals(speed_bins, speed_matrix)
    sector_width_deg = 360 / num_sectors
    sector_angles = np.arange(0, 360, sector_width_deg)
    fig, ax = plt.subplots(figsize=figsize, subplot_kw=dict(projection='polar'), facecolor='white')
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    theta_sectors = np.radians(sector_angles)
    effective_width_deg = sector_width_deg - (2 * gap_degrees)
    width = np.radians(effective_width_deg)
    schemes = get_color_schemes()
    speed_colors = schemes[color_scheme]["colors"]
    speed_ranges = ['0-3 m/s', '3-9 m/s', '9-13 m/s', '13-25 m/s', f'25-{int(np.max(speed_bins)):.0f} m/s']
    rebinned_totals = np.sum(new_speed_matrix, axis=0)
    frequency_mismatch = np.abs(dir_frequencies - rebinned_totals)
    if np.max(frequency_mismatch) > 0.001:
        scaling_factors = np.where(rebinned_totals > 0, dir_frequencies / rebinned_totals, 1.0)
        for speed_idx in range(len(new_speed_bins)):
            new_speed_matrix[speed_idx] = new_speed_matrix[speed_idx] * scaling_factors
    for speed_idx in range(len(new_speed_bins)):
        color = speed_colors[speed_idx]
        frequencies = new_speed_matrix[speed_idx]
        if speed_idx == 0:
            bottom = np.zeros(num_sectors)
        else:
            bottom = np.sum(new_speed_matrix[:speed_idx], axis=0)
        if np.any(frequencies > 0):
            ax.bar(theta_sectors, frequencies, width=width, bottom=bottom,
                   color=color, edgecolor='white', linewidth=0.5,
                   alpha=0.9, label=speed_ranges[speed_idx])
    ax.set_title(title or ' ', pad=25, fontsize=20, color="#000000")
    max_freq = np.max(dir_frequencies)
    max_radius = max_freq * 1.2
    ax.set_ylim(0, max_radius)
    max_tick = int(np.ceil(max_radius / 2)) * 2
    radial_ticks = np.arange(2, max_tick + 2, 2)
    ax.set_rticks(radial_ticks)
    ax.set_rlabel_position(22.5)
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'{int(x)}%'))
    ax.tick_params(axis='y', colors="#000000", labelsize=20)
    ax.set_thetagrids(np.arange(0, 360, 45),
                      ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'],
                      fontsize=20, color="#000000", fontweight='bold')
    ax.grid(True, alpha=0.3, color='#BDBDBD', linewidth=0.8)
    ax.set_facecolor('white')
    for i, sector_angle in enumerate(sector_angles):
        angle_rad = np.radians(sector_angle)
        ax.plot([angle_rad, angle_rad], [0, max_radius],
                color='#BDBDBD', linewidth=0.8, alpha=0.6, zorder=1)
    legend = ax.legend(loc='upper left', bbox_to_anchor=(1.1, 1),
                       title='Wind Speed Bins', frameon=False,
                       fancybox=False, shadow=False, title_fontsize=20, fontsize=18)
    legend.get_frame().set_facecolor('white')
    legend.get_frame().set_edgecolor('#1e3a5f')
    legend.get_title().set_color("#000000")
    plt.tight_layout()
    return fig, freq_fig


def main():
    st.title("Wind Rose and FD Plotter")

    uploaded_files = st.file_uploader(
        "Upload .tab files", type=["tab"], accept_multiple_files=True
    )

    with st.sidebar:
        st.header("Parameters")
        gap_degrees = st.number_input("Wind rose gap (deg)", 0.0, 10.0, 2.0, step=0.5)
        freq_max = st.number_input("FD max wind speed", 10, 100, 30, step=1)
        freq_res = st.number_input("FD wind speed label resolution", 1, 10, 2, step=1)
        color_scheme = st.selectbox(
            "Color scheme", ["Caribbean Sea", "Blood Orange", "Autumn Leaves"]
        )

    if uploaded_files and st.button("Generate Wind Roses"):
        for uploaded_file in uploaded_files:
            st.subheader(uploaded_file.name)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".tab") as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name
            try:
                wr_fig, fd_fig = create_wind_rose_with_speed_bins(
                    tmp_path,
                    gap_degrees=gap_degrees,
                    freq_max_x_axis=freq_max,
                    freq_x_axis_resolution=freq_res,
                    color_scheme=color_scheme,
                )
                col1, col2 = st.columns(2)
                with col1:
                    st.pyplot(wr_fig)
                with col2:
                    st.pyplot(fd_fig)
                for fig, label in [(wr_fig, "WR"), (fd_fig, "FD")]:
                    buf = io.BytesIO()
                    fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
                    buf.seek(0)
                    stem = os.path.splitext(uploaded_file.name)[0]
                    st.download_button(
                        f"Download {label} PNG",
                        buf,
                        file_name=f"{stem}_{label}.png",
                        mime="image/png",
                    )
                    plt.close(fig)
            except Exception as e:
                st.error(f"Error processing {uploaded_file.name}: {e}")
            finally:
                os.unlink(tmp_path)


if __name__ == "__main__":
    main()
