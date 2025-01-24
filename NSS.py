from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog,
    QScrollArea, QComboBox, QMessageBox, QProgressDialog, QSizePolicy,
    QDialog, QListWidget, QListWidgetItem, QLineEdit, QHBoxLayout, QCheckBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
import imageio.v3 as iio
import os, json, signal, requests, logging

logging.basicConfig(
    filename="steamgriddb_errors.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
__version__ = "1.0.3"

class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuration")
        self.setLayout(QVBoxLayout())
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("Enter SteamGridDB API Key")
        self.layout().addWidget(QLabel("SteamGridDB API Key:"))
        self.layout().addWidget(self.api_key_edit)
        self.cover_checkbox = QCheckBox("Download Covers")
        self.cover_checkbox.setChecked(True)
        self.layout().addWidget(self.cover_checkbox)
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_config)
        self.layout().addWidget(save_button)
        self.config_file = "NSS-config.json"
        self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                    self.api_key_edit.setText(config.get("api_key", ""))
                    self.cover_checkbox.setChecked(config.get("download_covers", True))
            except Exception as e:
                logging.error(f"Failed to load configuration: {e}")

    def save_config(self):
        config = {
            "api_key": self.api_key_edit.text(),
            "download_covers": self.cover_checkbox.isChecked()
        }
        try:
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=4)
            logging.info("Configuration saved successfully.")
            QMessageBox.information(self, "Success", "Configuration saved!")
            self.accept()
        except Exception as e:
            logging.error(f"Failed to save configuration: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {e}")

    def get_config(self):
        return {
            "api_key": self.api_key_edit.text(),
            "download_covers": self.cover_checkbox.isChecked()
        }

class SortDialog(QDialog):
    def __init__(self, apps, json_file_path, parent=None):
        super().__init__(parent)
        self.apps = apps
        self.json_file_path = json_file_path
        self.cmd_edits = {}
        self.config = self.load_config()
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.list_widget = QListWidget(self)
        self.list_widget.setDragDropMode(QListWidget.InternalMove)
        for app in apps:
            item_widget = self.create_app_widget(app)
            list_item = QListWidgetItem(self.list_widget)
            list_item.setSizeHint(item_widget.sizeHint())
            self.list_widget.addItem(list_item)
            self.list_widget.setItemWidget(list_item, item_widget)
        layout.addWidget(self.list_widget)
        config_button = QPushButton("Configure")
        config_button.clicked.connect(self.open_config_dialog)
        layout.addWidget(config_button)
        save_button = QPushButton("Save Sorted JSON")
        save_button.clicked.connect(self.save_sorted_json)
        layout.addWidget(save_button)
        self.showMaximized()

    def create_app_widget(self, app):
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        widget.setLayout(layout)
        name_label = QLabel(app.get("name", "Unnamed App"))
        layout.addWidget(name_label)
        cmd_edit = QLineEdit(app.get("cmd", ""))
        cmd_edit.setPlaceholderText("Edit command...")
        cmd_edit.setVisible(False)
        layout.addWidget(cmd_edit)
        cmd_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        edit_button = QPushButton("Edit Command")
        layout.addWidget(edit_button)
        edit_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        def toggle_cmd_edit():
            if cmd_edit.isVisible():
                cmd_edit.setVisible(False)
                edit_button.setText("Edit Command")
            else:
                cmd_edit.setVisible(True)
                cmd_edit.setFocus()
                edit_button.setText("Done")
        edit_button.clicked.connect(toggle_cmd_edit)
        self.cmd_edits[app.get("name", "Unnamed App")] = cmd_edit
        return widget

    def open_config_dialog(self):
        config_dialog = ConfigDialog(self)
        if config_dialog.exec_():
            self.config = config_dialog.get_config()

    def save_sorted_json(self):
        reordered_apps = []
        progress_dialog = QProgressDialog("Please wait, this may take a few minutes...", "Cancel", 0, self.list_widget.count(), self)
        progress_dialog.setWindowTitle("Processing")
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setMinimumDuration(0)
        progress_dialog.setValue(0)
        try:
            for i in range(self.list_widget.count()):
                if progress_dialog.wasCanceled():
                    QMessageBox.warning(self, "Canceled", "The operation was canceled.")
                    return
                list_item = self.list_widget.item(i)
                item_widget = self.list_widget.itemWidget(list_item)
                name_label = item_widget.layout().itemAt(0).widget()
                cmd_edit = self.cmd_edits[name_label.text()]
                for app in self.apps:
                    if app.get("name") == name_label.text():
                        if app["name"] == "Desktop":
                            app["image-path"] = "desktop.png"
                            app["cmd"] = ""
                        elif app["name"] == "Steam Big Picture":
                            app["image-path"] = "steam.png"
                            app["cmd"] = "steam://open/bigpicture"
                            app["auto-detatch"] = True
                            app["wait-all"] = True
                        else:
                            app["cmd"] = cmd_edit.text()
                            if self.config.get("download_covers"):
                                image_path = self.fetch_game_image(name_label.text())
                                if image_path:
                                    app["image-path"] = '"' + image_path.replace("/", "\\") + '"'
                        reordered_apps.append(app)
                        break
                progress_dialog.setValue(i + 1)
            with open(self.json_file_path, "w") as f:
                json.dump({"env": "", "apps": reordered_apps}, f, indent=4)
            QMessageBox.information(self, "Success", f"Configuration saved to {self.json_file_path}")
            self.accept()
        except Exception as e:
            logging.error(f"Failed to save JSON: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {e}")
        finally:
            progress_dialog.close()
            
    def fetch_game_image(self, game_name):
        if game_name in ["Desktop", "Steam Big Picture"]:
            logging.info(f"Skipping image fetch for {game_name}")
            return None
        api_key = self.config.get("api_key")
        if not api_key:
            logging.error("SteamGridDB API Key is not configured.")
            QMessageBox.warning(self, "Configuration Error", "SteamGridDB API Key is missing. Please configure the settings.")
            return None
        url = f"https://www.steamgriddb.com/api/v2/search/autocomplete/{game_name}"
        headers = {"Authorization": f"Bearer {api_key}"}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            results = response.json().get("data", [])
            logging.debug(f"SteamGridDB response for {game_name}: {results}")

            if results:
                game_id = results[0]["id"]
                return self.download_cover(game_id, game_name, api_key)
        except Exception as e:
            logging.error(f"Failed to fetch game data for {game_name}: {e}")
            QMessageBox.warning(self, "Error", f"Failed to fetch game data for {game_name}: {e}")
        return None

    def download_cover(self, game_id, game_name, api_key):
        url = f"https://www.steamgriddb.com/api/v2/grids/game/{game_id}"
        headers = {"Authorization": f"Bearer {api_key}"}
        try:
            # Fetch grid data for the game
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            grids = response.json().get("data", [])
            logging.debug(f"Grid data for {game_name}: {grids}")

            if grids:
                # Download the first available image
                image_url = grids[0]["url"]
                response = requests.get(image_url, stream=True)
                response.raise_for_status()

                # Save the image as a PNG
                image_dir = os.path.join(os.path.dirname(self.json_file_path), "covers")
                os.makedirs(image_dir, exist_ok=True)
                png_path = os.path.join(image_dir, f"{game_name}.png")

                # Convert the image to PNG format
                with open(png_path, "wb") as f:
                    f.write(response.content)
                logging.info(f"Image saved as PNG for {game_name} at {png_path}")

                return png_path

        except Exception as e:
            logging.error(f"Failed to download or save cover for {game_name}: {e}")
            QMessageBox.warning(self, "Error", f"Failed to download or save cover for {game_name}: {e}")
        return None

    def load_config(self):
        config_file = "NSS-config.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, "r") as f:
                    config = json.load(f)
                    logging.info("Configuration loaded successfully.")
                    return config
            except Exception as e:
                logging.error(f"Failed to load configuration: {e}")
        logging.warning("No configuration found, using defaults.")
        return {"api_key": "", "download_covers": True}

class NoScrollComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()

class FolderScannerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon('icon.ico'))
        self.FILTER_KEYWORDS = ['uninstall', 'setup', 'unins', 'unitycrashhandler64', 'crashpad_handler', 'unitycrashhandler32', 'vcredist_x64', 'vcredist_x642', 'vcredist_x643', 'vcredist_x86', 'vcredist_x862', 'vcredist_x863', 'vc_redist.x864', 'vc_redist.x644', 'oalinst']
        self.setWindowTitle("Folder and Executable Selector")
        self.setStyleSheet("""
            QWidget {
                background-color: #2e2e2e;
                color: #ffffff;
                font-size: 14px;
            }
            QPushButton {
                background-color: #444444;
                color: #ffffff;
                border: 1px solid #555555;
            }
            QPushButton:hover {
                background-color: #555555;
            }
            QComboBox {
                background-color: #444444;
                color: #ffffff;
                border: 1px solid #555555;
            }
            QLabel {
                color: #ffffff;
            }
        """)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.base_folders = []
        self.executables = {}
        self.init_ui()

    def init_ui(self):
        select_button = QPushButton("Add Folder")
        select_button.clicked.connect(self.select_folders)
        self.layout.addWidget(select_button)
        load_sort_button = QPushButton("Load and Sort JSON")
        load_sort_button.clicked.connect(self.load_and_sort_json)
        self.layout.addWidget(load_sort_button)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout()
        self.scroll_content.setLayout(self.scroll_layout)
        self.scroll_area.setWidget(self.scroll_content)
        self.layout.addWidget(self.scroll_area)
        save_button = QPushButton("Save Configuration")
        save_button.clicked.connect(self.save_configuration)
        self.layout.addWidget(save_button)

    def load_and_sort_json(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select JSON File", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    config = json.load(f)
                if "apps" in config:
                    apps = config["apps"]
                    sort_dialog = SortDialog(apps, file_path, self)
                    sort_dialog.exec_()
                else:
                    QMessageBox.warning(self, "Invalid JSON", "The selected JSON file does not contain an 'apps' key.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load JSON file: {e}")

    def select_folders(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Scan")
        if folder:
            folder = folder.replace("/", "\\")
            self.base_folders.append(folder)
            self.scan_folders()

    def scan_folders(self):
        progress_dialog = QProgressDialog("Scanning folders, please wait...", None, 0, 0, self)
        progress_dialog.setWindowTitle("Please Wait")
        progress_dialog.setCancelButton(None)
        progress_dialog.setWindowModality(Qt.ApplicationModal)
        progress_dialog.show()
        QApplication.processEvents()
        self.executables = {}
        for folder in self.base_folders:
            subfolder_data = {}
            for subfolder in os.listdir(folder):
                subfolder_path = os.path.join(folder, subfolder)
                if os.path.isdir(subfolder_path):
                    exe_files = []
                    for root, _, files in os.walk(subfolder_path):
                        exe_files.extend(
                            os.path.join(root, f) for f in files
                            if f.endswith('.exe') and not any(kw in f.lower() for kw in self.FILTER_KEYWORDS)
                        )
                    if exe_files:
                        subfolder_data[subfolder_path] = {
                            "exe_files": exe_files,
                            "selected_exe": "Skip"
                        }
            if subfolder_data:
                self.executables[folder] = subfolder_data
        progress_dialog.close()
        self.update_gui()

    def update_gui(self):
        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.takeAt(i).widget()
            if widget:
                widget.deleteLater()
        for base_folder, subfolders in self.executables.items():
            base_label = QLabel("Base Folder: " + base_folder.replace("/", "\\"))  # Use concatenation
            base_label.setStyleSheet("font-weight: bold;")
            self.scroll_layout.addWidget(base_label)
            for subfolder_path, data in subfolders.items():
                subfolder_label = QLabel("Subfolder: " + os.path.basename(subfolder_path).replace("/", "\\"))  # Concatenation
                self.scroll_layout.addWidget(subfolder_label)
                combo_box = NoScrollComboBox()
                combo_box.addItem("Skip")
                combo_box.addItems(data["exe_files"])
                combo_box.currentTextChanged.connect(lambda selected, data=data: self.update_selected_exe(data, selected))
                self.scroll_layout.addWidget(combo_box)

    def update_selected_exe(self, subfolder_data, selected_exe):
        subfolder_data["selected_exe"] = selected_exe

    def save_configuration(self):
        flat_apps = []
        flat_apps.append({
            "name": "Desktop",
            "image-path": "desktop.png"
        })
        flat_apps.append({
            "name": "Steam Big Picture",
            "cmd": "steam://open/bigpicture",
            "auto-detach": "true",
            "wait-all": "true",
            "image-path": "steam.png"
        })
        for base_folder, subfolders in self.executables.items():
            for subfolder_path, data in subfolders.items():
                if data["selected_exe"] == "Skip":
                    continue
                flat_apps.append({
                    "name": os.path.basename(subfolder_path),
                    "base_folder": base_folder.replace("/", "\\"),
                    "cmd": "\"" + data['selected_exe'].replace("/", "\\") + "\"",
                    "exclude-global-prep-cmd": "false",
                    "elevated": "false",
                    "auto-detach": "false",
                    "wait-all": "true",
                    "exit-timeout": "5",
                    "image-path": "",
                    "working-dir": "\"" + subfolder_path.replace("/", "\\") + "\""
                })
        config = {
            "env": "",
            "apps": flat_apps
        }
        output_file, _ = QFileDialog.getSaveFileName(self, "Save Configuration as JSON", "", "JSON Files (*.json)")
        if output_file:
            try:
                with open(output_file, 'w') as f:
                    json.dump(config, f, indent=4)
                sort_dialog = SortDialog(flat_apps, output_file, self)
                sort_dialog.exec_()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save configuration: {e}")

def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication([])
    window = FolderScannerApp()
    window.showMaximized()
    app.exec_()

if __name__ == "__main__":
    main()
