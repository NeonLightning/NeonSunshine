# NeonSunshine

`NeonSunshine` is a PyQt5-based GUI application that helps ease the adding of games to sunshine. The application supports JSON file loading, sorting, and saving, with optional integration to download cover images from the SteamGridDB API.

## Features

- **Folder Selection**: Add folders to scan for executable files.
- **JSON Management**: Load, sort, and save JSON configuration files containing application data.
- **Customization**: Edit application names and commands.
- **Drag-and-Drop Sorting**: Reorder applications using a simple drag-and-drop interface.
- **SteamGridDB Integration**: Fetch and save cover images for applications (requires API key).
- **Configuration Management**: Save and load application settings via a configuration dialog.

## Screenshots

### Main Screen
![Main Screen](screenshots/screenshot1.png)

### Sort Dialog
![Sort Dialog](screenshots/screenshot2.png)

### Configuration Screen
![Configuration Screen](screenshots/screenshot3.png)

## Installation

### Requirements

- Python 3.8+
- PyQt5
- Requests

### Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/NeonLightning/NeonSunshine.git
   cd NeonSunshine
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:

   ```bash
   python NSS.py
   ```

## Usage

1. **Add Folders**:

   - Click "Add Folder" to select folders to scan for executables.

2. **Load JSON Configuration**:

   - Use the "Load JSON" button to load an existing JSON configuration file.

3. **Sort Applications**:

   - Click "Load and Sort JSON" to open the saving and editing interface.

4. **Save Configuration**:

   - Save your sorted configuration by clicking "Sort Configuration."

5. **Configure Application Settings**:

   - Open the configuration dialog to enter your SteamGridDB API key or toggle download options.

## Configuration

The configuration is stored in `NSS-config.json` in the following format:

```json
{
    "api_key": "your_steamgriddb_api_key",
    "download_covers": true
}
```

## Logging

Errors and logs are saved in the `NSS_errors.log` file in the application directory.

## Troubleshooting

- Ensure Python 3.8+ is installed and added to your PATH.
- Verify dependencies are installed correctly.
- Provide a valid SteamGridDB API key for cover image downloads.

## Acknowledgments

- [SteamGridDB API](https://www.steamgriddb.com/) for providing application cover images.
- PyQt5 for the GUI framework.

---

Enjoy managing your applications effortlessly with `NeonSunshine`!

