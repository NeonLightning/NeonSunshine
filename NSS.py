import os
import json
from tkinter import Tk, filedialog

# List of keywords to identify uninstall files
FILTER_KEYWORDS = ['uninstall', 'setup', 'unins', 'unitycrashhandler64', 'crashpad_handler', 'unitycrashhandler32']

def select_executable(folder):
    # Filter out files that contain uninstall keywords
    exe_files = [f for f in os.listdir(folder) if f.endswith('.exe') and not any(kw in f.lower() for kw in FILTER_KEYWORDS)]
    
    if not exe_files:
        return None
    print(f"Select an executable in: {folder}")
    for idx, exe in enumerate(exe_files):
        print(f"{idx + 1}: {exe}")
    choice = input("Enter number (or press Enter to skip): ").strip()
    if choice.isdigit() and 0 < int(choice) <= len(exe_files):
        return exe_files[int(choice) - 1]
    return None

def scan_folder(folders):
    apps = []
    for folder in folders:
        print(f"\nScanning folder: {folder}")
        for subfolder in os.listdir(folder):
            subfolder_path = os.path.join(folder, subfolder)
            if os.path.isdir(subfolder_path):
                exe = select_executable(subfolder_path)
                if exe:
                    full_path = os.path.join(subfolder_path, exe)
                    app_entry = {
                        "name": subfolder,
                        "output": "",
                        "cmd": f'"{full_path}"',
                        "exclude-global-prep-cmd": "false",
                        "elevated": "false",
                        "auto-detach": "false",
                        "wait-all": "true",
                        "exit-timeout": "5",
                        "image-path": "",
                        "working-dir": f'"{subfolder_path}\\\\"'
                    }
                    apps.append(app_entry)
    return apps

def main():
    # Initialize Tkinter for file dialog
    root = Tk()
    root.withdraw()  # Hide the root window

    # Select multiple folders
    folders = filedialog.askdirectory(title="Select Folders to Scan")
    if not folders:
        print("No folders selected. Exiting.")
        return
    folders = [folders]  # Wrap the result in a list if it's a single folder selected
    
    # If the user wants to add more folders, repeat the selection
    while True:
        add_more = input("Do you want to select more folders? (y/n): ").strip().lower()
        if add_more == 'y':
            folder = filedialog.askdirectory(title="Select Another Folder to Scan")
            if folder:
                folders.append(folder)
        elif add_more == 'n':
            break

    # Get the configuration data
    config = {
        "env": "",
        "apps": scan_folder(folders)
    }

    # Ask the user where to save the resulting JSON file
    output_file = filedialog.asksaveasfilename(
        title="Save Configuration as JSON",
        defaultextension=".json",
        filetypes=[("JSON Files", "*.json")]
    )
    
    if not output_file:
        print("No file selected. Exiting.")
        return

    # Save the configuration to the selected file
    with open(output_file, 'w') as f:
        json.dump(config, f, indent=4)
    print(f"Configuration saved to {output_file}")

if __name__ == "__main__":
    main()
