# NeonSunshine

`NeonSunshine` is a PyQt5-based GUI application designed to simplify adding games to Sunshine. It supports JSON file loading, sorting, and saving, with optional integration to download cover images from the SteamGridDB API.

## Features

- **Folder Selection**: Add folders to scan for executable files.
- **Manual Entry**: Add custom applications manually, including commands, working directories, and optional cover images.
- **JSON Management**: Load, validate, sort, and save JSON configuration files containing application data.
- **Customization**: Edit application names and commands directly in the interface.
- **SteamGridDB Integration**: Fetch and save cover images for applications (requires API key). Covers are saved in a folder named `covers` alongside the saved JSON.
- **Configuration Management**: Save and load application settings via a configuration dialog.
- **Clear Covers Folder**: Option to clear the `covers` folder directly from the UI.

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

2. **Add Manual Entry**:

   - Use the "Add Manual Entry" button to add custom applications, including specifying commands, working directories, and cover images.

3. **Load JSON Configuration**:

   - Use the "Load JSON" button to load an existing JSON configuration file.(It will update the loaded folders entries aswell.)

4. **Sort Applications**:

   - Click "Load and Sort JSON" to open the sorting and editing interface.

5. **Save Configuration**:

   - Save your sorted configuration by clicking "Sort Configuration."

6. **Configure Application Settings**:

   - Open the configuration dialog to enter your SteamGridDB API key, toggle download options, or manage the application settings.

7. **Clear Covers Folder**:

   - Use the "Clear Covers Folder" button to delete all downloaded covers.

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

- [Sunshine](https://github.com/LizardByte/Sunshine) for the program this is for.
- [SteamGridDB API](https://www.steamgriddb.com/) for providing application cover images.
- PyQt5 for the GUI framework.

---

Enjoy managing your applications effortlessly with `NeonSunshine`! What started as a quick project to add games individually turned into a full-fledged program.

