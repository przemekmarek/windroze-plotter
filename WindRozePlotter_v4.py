import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from pathlib import Path
import threading
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend to reduce dependencies
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


class WindRoseGeneratorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Wind rose and FD plotter")
        self.root.geometry("650x650")
        self.root.resizable(True, True)
        
        # Set window icon (uncomment and modify path as needed)
        # self.root.iconbitmap('icon.ico')  # For .ico files
        # self.root.iconphoto(False, tk.PhotoImage(file='icon.png'))  # For .png files
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Variables for parameters
        self.gap_degrees = tk.DoubleVar(value=2.0)
        self.freq_max_x_axis = tk.IntVar(value=30)
        self.freq_x_axis_resolution = tk.IntVar(value=2)
        self.color_scheme = tk.StringVar(value="Caribbean Sea")
        self.selected_files = []
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Wind rose and FD plotter", 
                               font=('Arial', 16 )) #,'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # File selection section
        file_frame = ttk.LabelFrame(main_frame, text="File Selection", padding="10")
        file_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        file_frame.columnconfigure(0, weight=1)
        
        # File selection button
        select_btn = ttk.Button(file_frame, text="Select .tab Files", 
                               command=self.select_files, width=20)
        select_btn.grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        # Clear selection button
        clear_btn = ttk.Button(file_frame, text="Clear Selection", 
                              command=self.clear_files, width=15)
        clear_btn.grid(row=0, column=1, sticky=tk.W)
        
        # Selected files listbox with scrollbar
        files_label = ttk.Label(file_frame, text="Selected files:")
        files_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        
        # Frame for listbox and scrollbar
        listbox_frame = ttk.Frame(file_frame)
        listbox_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        listbox_frame.columnconfigure(0, weight=1)
        
        self.files_listbox = tk.Listbox(listbox_frame, height=6, selectmode=tk.SINGLE)
        self.files_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.files_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.files_listbox.configure(yscrollcommand=scrollbar.set)
        
        # Parameters section
        params_frame = ttk.LabelFrame(main_frame, text="Parameters", padding="10")
        params_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        params_frame.columnconfigure(1, weight=1)
        
        # Gap degrees parameter
        ttk.Label(params_frame, text="Wind rose gap (deg):").grid(row=0, column=0, sticky=tk.W, pady=5)
        gap_spinbox = ttk.Spinbox(params_frame, from_=0.0, to=10.0, increment=0.5, 
                                 textvariable=self.gap_degrees, width=10)
        gap_spinbox.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        ttk.Label(params_frame, text="(Gap in degrees on either side of each wind rose sector)").grid(
            row=0, column=2, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Frequency max x-axis parameter
        ttk.Label(params_frame, text="FD max wind speed:").grid(row=1, column=0, sticky=tk.W, pady=5)
        freq_max_spinbox = ttk.Spinbox(params_frame, from_=10, to=100, increment=1, 
                                      textvariable=self.freq_max_x_axis, width=10)
        freq_max_spinbox.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        ttk.Label(params_frame, text="(Maximum value for frequency distribution x-axis)").grid(
            row=1, column=2, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Frequency x-axis resolution parameter
        ttk.Label(params_frame, text="FD wind speed label res:").grid(row=2, column=0, sticky=tk.W, pady=5)
        freq_res_spinbox = ttk.Spinbox(params_frame, from_=1, to=10, increment=1, 
                                      textvariable=self.freq_x_axis_resolution, width=10)
        freq_res_spinbox.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        ttk.Label(params_frame, text="(Show every nth tick on frequency distribution x-axis)").grid(
            row=2, column=2, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Color scheme parameter
        ttk.Label(params_frame, text="Color Scheme:").grid(row=3, column=0, sticky=tk.W, pady=5)
        color_combo = ttk.Combobox(params_frame, textvariable=self.color_scheme, 
                                  values=["Caribbean Sea", "Blood Orange", "Autumn Leaves"], 
                                  state="readonly", width=20)
        color_combo.grid(row=3, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        ttk.Label(params_frame, text="(Color scheme for wind rose and frequency distribution)").grid(
            row=3, column=2, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Progress section
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_var = tk.StringVar(value="Ready to process files...")
        self.progress_label = ttk.Label(progress_frame, textvariable=self.progress_var)
        self.progress_label.grid(row=0, column=0, sticky=tk.W)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Generate button
        self.generate_btn = ttk.Button(main_frame, text="Generate Wind Roses", 
                                      command=self.start_generation, 
                                      style='Accent.TButton')
        self.generate_btn.grid(row=4, column=0, columnspan=3, pady=10)
        
        # Configure button style
        style = ttk.Style()
        style.configure('Accent.TButton', font=('Arial', 10))  # , 'bold'))
        
    def select_files(self):
        files = filedialog.askopenfilenames(
            title="Select .tab files",
            filetypes=[("Tab files", "*.tab"), ("All files", "*.*")]
        )
        if files:
            self.selected_files = list(files)
            self.update_files_listbox()
            
    def clear_files(self):
        self.selected_files = []
        self.update_files_listbox()
        
    def update_files_listbox(self):
        self.files_listbox.delete(0, tk.END)
        for file_path in self.selected_files:
            filename = os.path.basename(file_path)
            self.files_listbox.insert(tk.END, filename)
            
    def start_generation(self):
        if not self.selected_files:
            messagebox.showwarning("No Files Selected", "Please select at least one .tab file to process.")
            return
            
        # Disable the generate button during processing
        self.generate_btn.config(state='disabled')
        
        # Start processing in a separate thread to keep UI responsive
        thread = threading.Thread(target=self.generate_wind_roses)
        thread.daemon = True
        thread.start()
        
    def generate_wind_roses(self):
        try:
            total_files = len(self.selected_files)
            self.progress_bar.config(maximum=total_files)
            
            successful = 0
            failed = 0
            
            for i, file_path in enumerate(self.selected_files):
                try:
                    # Update progress
                    filename = os.path.basename(file_path)
                    self.progress_var.set(f"Processing {filename}...")
                    self.progress_bar.config(value=i)
                    self.root.update_idletasks()
                    
                    # Generate wind roses
                    wind_rose_fig, freq_dist_fig = create_wind_rose_with_speed_bins(
                        file_path,
                        gap_degrees=self.gap_degrees.get(),
                        freq_max_x_axis=self.freq_max_x_axis.get(),
                        freq_x_axis_resolution=self.freq_x_axis_resolution.get(),
                        color_scheme=self.color_scheme.get()
                    )
                    
                    # Save figures
                    base_name = Path(file_path).stem
                    output_dir = Path(file_path).parent
                    
                    wind_rose_path = output_dir / f"{base_name}_WR.png"
                    freq_dist_path = output_dir / f"{base_name}_FD.png"
                    
                    wind_rose_fig.savefig(wind_rose_path, dpi=300, bbox_inches='tight')
                    freq_dist_fig.savefig(freq_dist_path, dpi=300, bbox_inches='tight')
                    
                    # Close figures to free memory
                    plt.close(wind_rose_fig)
                    plt.close(freq_dist_fig)
                    
                    successful += 1
                    
                except Exception as e:
                    print(f"Error processing {filename}: {str(e)}")
                    failed += 1
                    
            # Update final progress
            self.progress_bar.config(value=total_files)
            self.progress_var.set(f"Complete! {successful} files processed successfully, {failed} failed.")
            
            if successful > 0:
                messagebox.showinfo("Generation Complete", 
                                  f"Successfully generated wind roses for {successful} files!\n"
                                  f"Output files saved in the same directories as input files.")
            if failed > 0:
                messagebox.showwarning("Some Files Failed", 
                                     f"{failed} files could not be processed. Check console for details.")
                
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")
            
        finally:
            # Re-enable the generate button
            self.generate_btn.config(state='normal')


def read_windographer_tab(filepath):
    """Read and parse a Windographer .tab file for wind rose data."""
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
    """Rebin wind speed data to custom intervals."""
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
    """Define color schemes for wind rose plotting."""
    return {
        "Caribbean Sea": {
            "colors": ['#cce5e5', "#7cd3d3", "#39ACAC", '#006666', "#420202", "#8F0058", "#FF0000"],
            "freq_color": "#39ACAC"  
        },
        "Blood Orange": {
            "colors": [ '#ffb3b3', '#ff6666', '#cc0000', '#800000', '#4d0000', '#1a0000'],
            "freq_color": "#a70000"  
        },
        "Autumn Leaves": {
            "colors": [ "#fff36d", '#ffd700', '#daa520', '#b8860b', '#8b6914', '#654321'],
            "freq_color": '#daa520'  
        }
    }


def create_frequency_distribution_plot(speed_bins, speed_matrix, dir_frequencies, figsize=(10, 6), max_x_axis=None, x_axis_resolution=1, color_scheme="Caribbean Sea"):
    """Create an all-directional frequency distribution plot."""
    weighted_speed_matrix = np.zeros_like(speed_matrix, dtype=float)
    for sector_idx in range(len(dir_frequencies)):
        weighted_speed_matrix[:, sector_idx] = (speed_matrix[:, sector_idx] / 1000.0) * dir_frequencies[sector_idx]
    
    total_frequencies = np.sum(weighted_speed_matrix, axis=1)
    shifted_speed_bins = speed_bins - 0.5
    
    fig, ax = plt.subplots(figsize=figsize, facecolor='white')
    
    # Get color from selected scheme
    schemes = get_color_schemes()
    color = schemes[color_scheme]["freq_color"]
    
    bars = ax.bar(shifted_speed_bins, total_frequencies, width=0.8, 
                  color=color, edgecolor='white', linewidth=0.5, alpha=0.9)
    
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
    """Create a wind rose with wind speed bins shown as different shades."""
    
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
    
    # Get colors from selected scheme
    schemes = get_color_schemes()
    speed_colors = schemes[color_scheme]["colors"]
    speed_ranges = ['0-3 m/s', '3-9 m/s','9-13 m/s', '13-25 m/s', f'25-{int(np.max(speed_bins)):.0f} m/s']
    
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
            bars = ax.bar(theta_sectors, frequencies, width=width, bottom=bottom,
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
    root = tk.Tk()
    app = WindRoseGeneratorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()