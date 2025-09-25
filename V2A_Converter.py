import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import subprocess
import threading
import os
import re
import time
from tkinterdnd2 import DND_FILES, TkinterDnD
# NEW: Import the library for loading custom fonts
from tkextrafont import Font 

class V2AConverter(TkinterDnD.Tk):
    """
    A fully responsive Video to Audio (V2A) converter using a custom font.
    """
    def __init__(self):
        super().__init__()

        self.title("V2A Converter - Custom Font")
        self.geometry("800x600")
        self.minsize(650, 450)

        # --- Load Custom Font ---
        # We wrap this in a try/except block in case the font file is missing.
        try:
            # Construct the full path to the font file
            font_path = os.path.join(os.path.dirname(__file__), "fonts", "Inter-Regular.ttf")
            # Load the font file. The .name attribute gives us the family name Tkinter can use.
            self.app_font_family = Font(file=font_path, family="Inter").name
            print(f"Successfully loaded font: '{self.app_font_family}'")
        except Exception as e:
            print(f"Could not load custom font: {e}. Falling back to default font.")
            # If the font fails to load, use a safe default.
            self.app_font_family = "Segoe UI"


        # --- UI Styling ---
        # Now, we use the loaded font family name throughout the app.
        self.style = ttk.Style(self)
        self.style.configure('.', font=(self.app_font_family, 12))
        self.style.configure('TButton', padding=8)
        self.style.configure('Accent.TButton', font=(self.app_font_family, 12, 'bold'))

        self.ffmpeg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ffmpeg", "ffmpeg.exe")
        self.ffmpeg_process = None
        self.is_converting = False

        self.create_widgets()
        self.center_window()

        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.handle_drop)

    def create_widgets(self):
        """Creates and places all GUI widgets using a responsive grid layout."""
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(expand=True, fill="both")

        main_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)

        # --- Row 0: File Queue Section ---
        queue_frame = ttk.LabelFrame(main_frame, text="Conversion Queue", padding="10")
        queue_frame.grid(row=0, column=0, sticky="nsew")
        
        queue_frame.rowconfigure(0, weight=1)
        queue_frame.columnconfigure(0, weight=1)

        # Apply the custom font to the Listbox as well
        self.file_listbox = tk.Listbox(queue_frame, selectmode=tk.EXTENDED, font=(self.app_font_family, 11))
        self.file_listbox.grid(row=0, column=0, sticky="nsew")
        
        scrollbar = ttk.Scrollbar(queue_frame, orient="vertical", command=self.file_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.file_listbox.config(yscrollcommand=scrollbar.set)

        # --- Row 1: File Management Buttons ---
        file_button_frame = ttk.Frame(main_frame)
        file_button_frame.grid(row=1, column=0, sticky="ew", pady=(10, 5))
        
        ttk.Button(file_button_frame, text="Add File(s)", command=self.add_files).pack(side="left", padx=(0, 5))
        ttk.Button(file_button_frame, text="Add Folder", command=self.add_folder).pack(side="left", padx=5)
        ttk.Button(file_button_frame, text="Remove Selected", command=self.remove_selected).pack(side="left", padx=5)
        ttk.Button(file_button_frame, text="Clear Queue", command=self.clear_queue).pack(side="left", padx=5)

        # --- Row 2: Output Configuration ---
        output_settings_frame = ttk.LabelFrame(main_frame, text="Output Settings", padding="15")
        output_settings_frame.grid(row=2, column=0, sticky="ew", pady=5)

        ttk.Label(output_settings_frame, text="Output Folder:").grid(row=0, column=0, sticky="w", padx=5, pady=10)
        self.output_dir_entry = ttk.Entry(output_settings_frame)
        self.output_dir_entry.grid(row=0, column=1, sticky="ew", padx=5, ipady=4)
        ttk.Button(output_settings_frame, text="Browse", command=self.browse_output_dir).grid(row=0, column=2, padx=5)

        ttk.Label(output_settings_frame, text="Audio Format:").grid(row=1, column=0, sticky="w", padx=5, pady=10)
        self.format_var = tk.StringVar(value="mp3")
        format_menu = ttk.Combobox(output_settings_frame, textvariable=self.format_var, values=["mp3", "wav", "flac", "aac", "ogg"], state="readonly")
        format_menu.grid(row=1, column=1, sticky="w", padx=5)
        
        ttk.Label(output_settings_frame, text="Audio Quality:").grid(row=2, column=0, sticky="w", padx=5, pady=10)
        self.quality_var = tk.StringVar(value="High")
        quality_menu = ttk.Combobox(output_settings_frame, textvariable=self.quality_var, values=["Standard", "High", "Lossless"], state="readonly")
        quality_menu.grid(row=2, column=1, sticky="w", padx=5)

        output_settings_frame.columnconfigure(1, weight=1)

        # --- Row 3: Progress & Status ---
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=3, column=0, sticky="ew", pady=5, ipady=5)
        self.progress_bar = ttk.Progressbar(progress_frame, orient="horizontal", mode="determinate")
        self.progress_bar.pack(expand=True, fill="x")
        self.status_label = ttk.Label(progress_frame, text="Ready. Add files to the queue or drag them here.", anchor="center")
        self.status_label.pack(fill="x", pady=5)

        # --- Row 4: Main Action Buttons ---
        action_button_frame = ttk.Frame(main_frame)
        action_button_frame.grid(row=4, column=0, pady=(10, 0))
        self.run_button = ttk.Button(action_button_frame, text="Start Conversion", command=self.start_conversion_thread, style="Accent.TButton")
        self.run_button.pack(side="left", padx=10, ipady=10)
        self.cancel_button = ttk.Button(action_button_frame, text="Cancel", command=self.cancel_conversion, state="disabled")
        self.cancel_button.pack(side="left", padx=10, ipady=10)

    def center_window(self):
        """Centers the main window on the screen."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    # --- File Handling and Conversion Methods (No changes below this line) ---
    def handle_drop(self, event):
        files = self.tk.splitlist(event.data)
        for file in files:
            if file.lower().endswith(('.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv')):
                if file not in self.file_listbox.get(0, tk.END):
                    self.file_listbox.insert(tk.END, file)

    def add_files(self):
        file_paths = filedialog.askopenfilenames(
            title="Select video files",
            filetypes=[("Video files", "*.mp4;*.mkv;*.avi;*.mov;*.webm;*.flv")]
        )
        for file_path in file_paths:
             if file_path not in self.file_listbox.get(0, tk.END):
                self.file_listbox.insert(tk.END, file_path)

    def add_folder(self):
        folder_path = filedialog.askdirectory(title="Select a folder containing videos")
        if folder_path:
            for root, _, files in os.walk(folder_path):
                for file in files:
                    if file.lower().endswith(('.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv')):
                        full_path = os.path.join(root, file)
                        if full_path not in self.file_listbox.get(0, tk.END):
                            self.file_listbox.insert(tk.END, full_path)

    def remove_selected(self):
        selected_indices = self.file_listbox.curselection()
        for i in sorted(selected_indices, reverse=True):
            self.file_listbox.delete(i)
    
    def clear_queue(self):
        self.file_listbox.delete(0, tk.END)

    def browse_output_dir(self):
        dir_path = filedialog.askdirectory(title="Select Output Folder")
        if dir_path:
            self.output_dir_entry.delete(0, tk.END)
            self.output_dir_entry.insert(0, dir_path)

    def get_ffmpeg_options(self):
        quality = self.quality_var.get()
        audio_format = self.format_var.get()

        if audio_format in ['flac', 'wav']:
             if quality == "Lossless":
                 return ["-vn", "-c:a", "flac" if audio_format == 'flac' else "pcm_s16le"]
             else:
                 messagebox.showinfo("Info", f"'{quality}' is not a lossless setting. Use 'Lossless' preset for FLAC/WAV for best results.")

        if quality == "Standard":
            return ["-vn", "-b:a", "192k"]
        elif quality == "High":
            return ["-vn", "-q:a", "0"] 
        elif quality == "Lossless":
            messagebox.showwarning("Quality Mismatch", f"Lossless is only available for FLAC or WAV. Defaulting to 'High' quality for the {audio_format.upper()} format.")
            return ["-vn", "-q:a", "0"]
        return ["-vn", "-q:a", "0"] 

    def start_conversion_thread(self):
        files_to_convert = self.file_listbox.get(0, tk.END)
        output_dir = self.output_dir_entry.get()

        if not os.path.exists(self.ffmpeg_path):
            messagebox.showerror("Error", f"FFmpeg not found at '{self.ffmpeg_path}'.")
            return
        if not files_to_convert:
            messagebox.showwarning("Warning", "The conversion queue is empty.")
            return
        if not output_dir or not os.path.isdir(output_dir):
            messagebox.showwarning("Warning", "Please select a valid output folder.")
            return

        self.run_button.config(state="disabled")
        self.cancel_button.config(state="normal")
        self.is_converting = True

        threading.Thread(target=self.run_batch_conversion, args=(files_to_convert, output_dir), daemon=True).start()

    def run_batch_conversion(self, files, output_dir):
        total_files = len(files)
        for i, input_file in enumerate(files):
            if not self.is_converting:
                self.status_label.config(text="Conversion cancelled by user.")
                break

            self.progress_bar["value"] = 0
            self.status_label.config(text=f"Processing file {i+1} of {total_files}: {os.path.basename(input_file)}")

            base_name = os.path.splitext(os.path.basename(input_file))[0]
            output_format = self.format_var.get()
            output_file = os.path.join(output_dir, f"{base_name}.{output_format}")
            
            command = [self.ffmpeg_path, "-y", "-i", input_file]
            command.extend(self.get_ffmpeg_options())
            command.append(output_file)

            self.execute_command(command, input_file)

        if self.is_converting: 
            self.status_label.config(text=f"Batch conversion complete! {total_files} files processed.")
        self.is_converting = False
        self.run_button.config(state="normal")
        self.cancel_button.config(state="disabled")
        self.progress_bar["value"] = 100

    def execute_command(self, command, input_file):
        try:
            duration_cmd = [self.ffmpeg_path, "-i", input_file, "-hide_banner"]
            result = subprocess.run(duration_cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW, encoding='utf-8')
            duration_match = re.search(r"Duration: (\d{2}):(\d{2}):(\d{2})\.(\d{2})", result.stderr)
            total_seconds = 0
            if duration_match:
                h, m, s = map(int, duration_match.group(1, 2, 3))
                total_seconds = h * 3600 + m * 60 + s
            
            self.ffmpeg_process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                universal_newlines=True, creationflags=subprocess.CREATE_NO_WINDOW, encoding='utf-8'
            )

            start_time = time.time()
            for line in self.ffmpeg_process.stdout:
                if not self.is_converting: break
                
                time_match = re.search(r"time=(\d{2}):(\d{2}):(\d{2})\.(\d{2})", line)
                if time_match and total_seconds > 0:
                    h, m, s = map(int, time_match.group(1, 2, 3))
                    current_seconds = h * 3600 + m * 60 + s
                    
                    progress = (current_seconds / total_seconds) * 100
                    self.progress_bar["value"] = progress
                    
                    elapsed_time = time.time() - start_time
                    if current_seconds > 0 and elapsed_time > 1:
                        speed = current_seconds / elapsed_time
                        remaining_seconds = total_seconds - current_seconds
                        eta = remaining_seconds / speed
                        eta_str = time.strftime('%H:%M:%S', time.gmtime(eta))
                        self.status_label.config(text=f"Converting... {int(progress)}% (ETA: {eta_str})")
                    else:
                         self.status_label.config(text=f"Converting... {int(progress)}%")

            self.ffmpeg_process.wait()
            if self.ffmpeg_process.returncode != 0 and self.is_converting:
                print(f"FFmpeg error on file {input_file}")
        
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            self.ffmpeg_process = None

    def cancel_conversion(self):
        self.status_label.config(text="Cancelling...")
        self.is_converting = False
        if self.ffmpeg_process and self.ffmpeg_process.poll() is None:
            self.ffmpeg_process.terminate()

if __name__ == "__main__":
    ffmpeg_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ffmpeg")
    if not os.path.exists(os.path.join(ffmpeg_dir, "ffmpeg.exe")):
        messagebox.showerror("FFmpeg Not Found", 
                             f"ffmpeg.exe was not found in the '{ffmpeg_dir}' subfolder.\n\n"
                             "Please download FFmpeg and place ffmpeg.exe in that folder.")
    else:
        app = V2AConverter()
        app.mainloop()