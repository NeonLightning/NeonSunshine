import os
import json
from tkinter import Tk, filedialog, StringVar, Label, Button, OptionMenu, Frame, Canvas, Scrollbar, messagebox

FILTER_KEYWORDS = ['uninstall', 'setup', 'unins', 'unitycrashhandler64', 'crashpad_handler', 'unitycrashhandler32', 'vcredist_x64', 'vcredist_x642', 'vcredist_x643', 'vcredist_x86', 'vcredist_x862', 'vcredist_x863', 'vc_redist.x864', 'vc_redist.x644', "oalinst"]

# Dark mode styles
DARK_MODE_STYLES = {
    "bg": "#2e2e2e",
    "fg": "#ffffff",
    "button_bg": "#444444",
    "button_fg": "#ffffff",
    "highlight_bg": "#555555",
    "highlight_fg": "#ffffff",
    "menu_bg": "#2e2e2e",
    "menu_fg": "#ffffff"
}

def apply_dark_mode(widget):
    widget.configure(bg=DARK_MODE_STYLES["bg"], fg=DARK_MODE_STYLES["fg"])

def apply_dark_mode_button(widget):
    widget.configure(bg=DARK_MODE_STYLES["button_bg"], fg=DARK_MODE_STYLES["button_fg"], activebackground=DARK_MODE_STYLES["highlight_bg"], activeforeground=DARK_MODE_STYLES["highlight_fg"])

def scan_folders(base_folders):
    executables = {}
    for folder in base_folders:
        subfolder_data = {}
        for subfolder in os.listdir(folder):
            subfolder_path = os.path.join(folder, subfolder)
            if os.path.isdir(subfolder_path):
                exe_files = []
                for root, _, files in os.walk(subfolder_path):
                    exe_files.extend(
                        os.path.join(root, f) for f in files
                        if f.endswith('.exe') and not any(kw in f.lower() for kw in FILTER_KEYWORDS)
                    )
                if exe_files:
                    subfolder_data[subfolder_path] = {
                        "exe_files": exe_files,
                        "selected_exe": "Skip"
                    }
        if subfolder_data:
            executables[folder] = subfolder_data
    return executables

def update_selected_exe(subfolder_data, selected_exe):
    subfolder_data["selected_exe"] = selected_exe
    print(f"Updated selection: {selected_exe}")

def create_gui(apps, save_callback):
    root = Tk()
    root.title("Folder and Executable Selector")
    root.configure(bg=DARK_MODE_STYLES["bg"])
    root.protocol("WM_DELETE_WINDOW", root.quit)

    canvas = Canvas(root, bg=DARK_MODE_STYLES["bg"], highlightbackground=DARK_MODE_STYLES["highlight_bg"])
    scrollbar = Scrollbar(root, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)

    frame = Frame(canvas, bg=DARK_MODE_STYLES["bg"])
    canvas.create_window((0, 0), window=frame, anchor="nw")
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(-1 * (event.delta // 120), "units"))

    row_index = 0
    for base_folder, subfolders in apps.items():
        label = Label(frame, text=f"Base Folder: {base_folder}", font=("Arial", 12, "bold"), bg=DARK_MODE_STYLES["bg"], fg=DARK_MODE_STYLES["fg"])
        label.grid(row=row_index, column=0, pady=10, sticky="w")
        row_index += 1
        for subfolder_path, data in subfolders.items():
            subfolder_label = Label(frame, text=f"Subfolder: {os.path.basename(subfolder_path)}", bg=DARK_MODE_STYLES["bg"], fg=DARK_MODE_STYLES["fg"])
            subfolder_label.grid(row=row_index, column=0, pady=5, sticky="w")

            selected_exe_var = StringVar(frame)
            selected_exe_var.set(data["selected_exe"])

            formatted_exe_files = ["Skip"] + [exe.replace("\\", "/") for exe in data["exe_files"]]
            option_menu = OptionMenu(
                frame, selected_exe_var, *formatted_exe_files,
                command=lambda selected, data=data: update_selected_exe(data, selected)
            )

            # Apply dark mode styles to OptionMenu
            menu = option_menu.nametowidget(option_menu.menuname)
            menu.configure(bg=DARK_MODE_STYLES["menu_bg"], fg=DARK_MODE_STYLES["menu_fg"])
            option_menu.configure(bg=DARK_MODE_STYLES["button_bg"], fg=DARK_MODE_STYLES["button_fg"], activebackground=DARK_MODE_STYLES["highlight_bg"], activeforeground=DARK_MODE_STYLES["highlight_fg"])
            option_menu.grid(row=row_index + 1, column=0, pady=5, sticky="w")
            row_index += 2

    save_button = Button(frame, text="Save Configuration", command=lambda: save_callback(apps))
    apply_dark_mode_button(save_button)
    save_button.grid(row=row_index, column=0, pady=10)

    frame.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))
    root.mainloop()

def main():
    base_folders = []
    root = Tk()
    root.withdraw()
    while True:
        folder = filedialog.askdirectory(title="Select Folder to Scan")
        if not folder:
            break
        base_folders.append(folder)
        add_more = messagebox.askyesno("Add More Folders", "Do you want to select more folders?")
        if not add_more:
            break
    if not base_folders:
        messagebox.showinfo("Info", "No folders selected. Exiting.")
        return
    executables = scan_folders(base_folders)
    if not executables:
        messagebox.showinfo("Info", "No executables found.")
        return

    def save_callback(apps):
        flat_apps = []
        for base_folder, subfolders in apps.items():
            for subfolder_path, data in subfolders.items():
                if data["selected_exe"] == "Skip":
                    continue
                flat_apps.append({
                    "name": os.path.basename(subfolder_path),
                    "base_folder": base_folder,
                    "cmd": data["selected_exe"],
                    "exclude-global-prep-cmd": "false",
                    "elevated": "false",
                    "auto-detach": "false",
                    "wait-all": "true",
                    "exit-timeout": "5",
                    "image-path": "",
                    "working-dir": subfolder_path.replace("\\", "/") + "/"
                })
        config = {
            "env": "",
            "apps": flat_apps
        }
        output_file = filedialog.asksaveasfilename(
            title="Save Configuration as JSON",
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")]
        )
        if output_file:
            try:
                with open(output_file, 'w') as f:
                    json.dump(config, f, indent=4)
                messagebox.showinfo("Success", f"Configuration saved to {output_file}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save configuration: {e}")
    create_gui(executables, save_callback)

if __name__ == "__main__":
    main()
