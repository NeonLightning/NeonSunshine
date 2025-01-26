from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog,
    QScrollArea, QComboBox, QMessageBox, QProgressDialog, QSizePolicy,
    QDialog, QListWidget, QListWidgetItem, QLineEdit, QHBoxLayout, QCheckBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from functools import partial
import os, json, signal, requests, logging

logging.basicConfig(
    filename="NSS_errors.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
__version__ = "1.0.12"

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
        self.config_dialog = ConfigDialog(self)
        self.config = self.config_dialog.get_config()
        self.download_covers = self.config.get("download_covers", False)
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
        config_button.setFocusPolicy(Qt.NoFocus)
        config_button.clicked.connect(self.open_config_dialog)
        layout.addWidget(config_button)
        save_button = QPushButton("Save Sorted JSON")
        save_button.setFocusPolicy(Qt.NoFocus)
        save_button.clicked.connect(self.save_sorted_json)
        layout.addWidget(save_button)
        self.showMaximized()

    def open_config_dialog(self):
        config_dialog = ConfigDialog(self)
        if config_dialog.exec_():
            self.config = config_dialog.get_config()
            self.download_covers = self.config.get("download_covers", True)

    def create_app_widget(self, app):
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        widget.setLayout(layout)
        drag_handle = QLabel("≡")
        drag_handle.setFixedSize(20, 20)
        drag_handle.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #555555;
            }
        """)
        drag_handle.setAlignment(Qt.AlignLeft)
        drag_handle.setFocusPolicy(Qt.NoFocus)
        layout.addWidget(drag_handle)
        name_label = QLabel(app.get("name", "Unnamed App"))
        name_label.setFocusPolicy(Qt.NoFocus)
        layout.addWidget(name_label)
        name_edit = QLineEdit(app.get("name", "Unnamed App"))
        name_edit.setVisible(False)
        name_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(name_edit)
        cmd_edit = QLineEdit(app.get("cmd", ""))
        cmd_edit.setPlaceholderText("Edit command...")
        cmd_edit.setVisible(False)
        cmd_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(cmd_edit)
        edit_button = QPushButton("Edit Command")
        edit_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        edit_button.setFocusPolicy(Qt.NoFocus)
        layout.addWidget(edit_button)
        self.cmd_edits[app.get("name", "Unnamed App")] = {
            "name_label": name_label,
            "name_edit": name_edit,
            "cmd_edit": cmd_edit
        }
        def toggle_name_edit():
            if name_edit.isVisible():
                updated_name = name_edit.text().strip()
                if updated_name:
                    old_name = name_label.text()
                    name_label.setText(updated_name)
                    name_label.setVisible(True)
                    name_edit.setVisible(False)
                    if old_name in self.cmd_edits:
                        self.cmd_edits[updated_name] = self.cmd_edits.pop(old_name)
                        self.cmd_edits[updated_name]["name_edit"] = name_edit
                    for app_item in self.apps:
                        if app_item.get("name") == old_name:
                            app_item["name"] = updated_name
                            break
            else:
                name_edit.setText(name_label.text())
                name_label.setVisible(False)
                name_edit.setVisible(True)
                name_edit.setFocus()
                
        def save_name():
            updated_name = name_edit.text().strip()
            if updated_name:
                old_name = name_label.text()
                name_label.setText(updated_name)
                name_label.setVisible(True)
                name_edit.setVisible(False)
                if old_name in self.cmd_edits:
                    self.cmd_edits[updated_name] = self.cmd_edits.pop(old_name)
                    self.cmd_edits[updated_name]["name_edit"] = name_edit
                for app_item in self.apps:
                    if app_item.get("name") == old_name:
                        app_item["name"] = updated_name
                        break

        name_edit.editingFinished.connect(save_name)

        def toggle_cmd_edit():
            cmd_edit.setText(app.get("cmd", ""))
            cmd_edit.setVisible(True)
            cmd_edit.setFocusPolicy(Qt.StrongFocus)
            cmd_edit.setFocus()

        def save_command():
            updated_cmd = cmd_edit.text().strip()
            if updated_cmd:
                app["cmd"] = updated_cmd
                for app_item in self.apps:
                    if app_item.get("name") == app.get("name"):
                        app_item["cmd"] = updated_cmd
                        break
            cmd_edit.setVisible(False)

        cmd_edit.editingFinished.connect(save_command)
        name_label.mousePressEvent = lambda event: toggle_name_edit()
        edit_button.clicked.connect(toggle_cmd_edit)
        return widget

    def open_config_dialog(self):
        config_dialog = ConfigDialog(self)
        if config_dialog.exec_():
            self.config = config_dialog.get_config()

    def save_sorted_json(self):
        if not self.json_file_path:
            self.json_file_path, _ = QFileDialog.getSaveFileName(self, "Save Sorted JSON", "", "JSON Files (*.json)")
            if not self.json_file_path:
                QMessageBox.warning(self, "No File Selected", "Please select a file to save the sorted configuration.")
                return
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
                progress_dialog.setValue(i)
                name_label = item_widget.layout().itemAt(1).widget()
                app_fields = self.cmd_edits[name_label.text()]
                name_edit = app_fields["name_edit"]
                cmd_edit = app_fields["cmd_edit"]
                updated_name = name_edit.text().strip()
                updated_cmd = cmd_edit.text().strip().replace("\\", "/")
                for app in self.apps:
                    if app.get("name") == name_label.text():
                        app["name"] = updated_name
                        app["cmd"] = updated_cmd
                        if updated_name == "Desktop":
                            app["image-path"] = "desktop.png"
                        elif updated_name == "Steam Big Picture":
                            app["image-path"] = "steam.png"
                        else:
                            current_image_path = app.get("image-path", "")
                            expected_image_name = f"{updated_name}.png"
                            if (
                                not current_image_path or
                                os.path.basename(current_image_path) != expected_image_name or
                                not os.path.exists(current_image_path)
                            ):
                                if self.download_covers:
                                    logging.debug(f"Fetching new cover for: {updated_name}")
                                    image_path = self.fetch_game_image(updated_name)
                                    if image_path:
                                        app["image-path"] = image_path
                                        logging.debug(f"Updated image-path for {updated_name}: {image_path}")
                                    else:
                                        logging.warning(f"No image found for {updated_name}")
                                else:
                                    app["image-path"] = None
                                    logging.debug(f"Cleared image-path for {updated_name} as downloading is disabled.")
                            else:
                                logging.debug(f"Image-path for {updated_name} is up-to-date: {current_image_path}")

                        reordered_apps.append(app)
                        break
            with open(self.json_file_path, "w") as f:
                json.dump({"env": "", "apps": reordered_apps}, f, indent=4)
            QMessageBox.information(self, "Success", f"Configuration saved to {self.json_file_path}")
            self.accept()
        except Exception as e:
            logging.error(f"Failed to save JSON: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {e}")
        finally:
            progress_dialog.setValue(self.list_widget.count())
            progress_dialog.close()

    def fetch_game_image(self, game_name):
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
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            grids = response.json().get("data", [])
            logging.debug(f"Grid data for {game_name}: {grids}")
            if grids:
                image_url = grids[0]["url"]
                response = requests.get(image_url, stream=True)
                response.raise_for_status()
                image_dir = os.path.join(os.path.dirname(self.json_file_path), "covers")
                os.makedirs(image_dir, exist_ok=True)
                png_path = os.path.join(image_dir, f"{game_name}.png")
                with open(png_path, "wb") as f:
                    f.write(response.content)
                logging.info(f"Image saved as PNG for {game_name} at {png_path}")
                return png_path
        except Exception as e:
            logging.error(f"Failed to download or save cover for {game_name}: {e}")
            QMessageBox.warning(self, "Error", f"Failed to download or save cover for {game_name}: {e}")
        return None

class NoScrollComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()

class FolderScannerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon('icon.ico'))
        self.FILTER_KEYWORDS = ['uninstall', 'setup', 'unins', 'unitycrashhandler64', 'crashpad_handler', 'unitycrashhandler32', 'vcredist_x64', 'vcredist_x642', 'vcredist_x643', 'vcredist_x86', 'vcredist_x862', 'vcredist_x863', 'vc_redist.x864', 'vc_redist.x644', 'oalinst', 'vc_redistx86', 'vc_redistx64', 'vc_redistx64']
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
        self.loaded_apps = []
        self.init_ui()

    def init_ui(self):
        load_json_button = QPushButton("Load JSON")
        load_json_button.clicked.connect(self.load_json)
        self.layout.addWidget(load_json_button)
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
        clear_list_button = QPushButton("Clear List")
        clear_list_button.clicked.connect(self.clear_list)
        self.layout.addWidget(clear_list_button)
        save_button = QPushButton("Sort Configuration")
        save_button.clicked.connect(self.save_configuration)
        self.layout.addWidget(save_button)

    def clear_list(self):
        self.executables.clear()
        self.base_folders.clear()
        self.update_gui()
        QMessageBox.information(self, "List Cleared", "The list has been successfully cleared.")

    def clean_up_special_entries(self):
        special_names = {"Desktop", "Steam Big Picture"}
        for category, subfolders in list(self.executables.items()):
            if category == "Special":
                continue
            for key, data in list(subfolders.items()):
                if data.get("name") in special_names:
                    del subfolders[key]

    def load_json(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select JSON File to Load", "", "JSON Files (*.json)")
        if not file_path:
            return
        try:
            with open(file_path, "r") as f:
                config = json.load(f)
            logging.debug(f"Loaded JSON: {config}")
            if not isinstance(config, dict):
                raise ValueError("Invalid JSON format: Root is not a dictionary.")
            if "apps" not in config:
                raise ValueError("Invalid JSON format: Missing 'apps' key.")
            if not isinstance(config["apps"], list):
                raise ValueError("Invalid JSON format: 'apps' is not a list.")
            total_apps = len(config["apps"])
            progress_dialog = QProgressDialog("Processing apps, please wait...", None, 0, total_apps, self)
            progress_dialog.setWindowTitle("Loading JSON")
            progress_dialog.setCancelButtonText("Cancel")
            progress_dialog.setWindowModality(Qt.ApplicationModal)
            progress_dialog.show()
            QApplication.processEvents()
            self.executables.setdefault("Special", {})
            loaded_app_names = {app.get("name", "") for app in config["apps"] if isinstance(app, dict)}
            special_entries = {
                "Desktop": {
                    "name": "Desktop",
                    "cmd": None,
                    "image-path": "desktop.png",
                    "selected_exe": "Include" if "Desktop" in loaded_app_names else "Skip",
                    "exe_files": ["Skip", "Include"]
                },
                "Steam Big Picture": {
                    "name": "Steam Big Picture",
                    "cmd": "steam://open/bigpicture",
                    "image-path": "steam.png",
                    "selected_exe": "Include" if "Steam Big Picture" in loaded_app_names else "Skip",
                    "exe_files": ["Skip", "Include"]
                }
            }
            for key, entry in special_entries.items():
                self.executables["Special"][key] = entry
            for index, app in enumerate(config["apps"]):
                if not isinstance(app, dict):
                    logging.warning(f"Skipping invalid app at index {index}: {app}")
                    continue
                logging.debug(f"Processing app at index {index}: {app}")
                name = app.get("name", "Unnamed App")
                if name in special_entries:
                    continue
                cmd = os.path.normpath(app.get("cmd", "").strip("\"")) if app.get("cmd") else ""
                image_path = app.get("image-path", "")
                working_dir = os.path.normpath(app.get("working-dir", "").strip("\"")) if app.get("working-dir") else ""
                exe_files = ["Skip"]
                if working_dir and os.path.exists(working_dir):
                    for root, _, files in os.walk(working_dir):
                        exe_files.extend(
                            os.path.normpath(os.path.join(root, file)) 
                            for file in files 
                            if file.endswith(".exe") and not any(keyword in file.lower() for keyword in self.FILTER_KEYWORDS)
                        )
                    exe_files = sorted(set(exe_files))
                if cmd and cmd not in exe_files:
                    exe_files.append(cmd)
                exe_files = ["Skip"] + [item for item in exe_files if item != "Skip"]
                if working_dir:
                    base_folder = os.path.dirname(working_dir)
                    self.executables.setdefault(base_folder, {})
                    self.executables[base_folder][working_dir] = {
                        "exe_files": exe_files,
                        "selected_exe": cmd if cmd in exe_files else "Skip",
                        "image-path": image_path,
                        "name": name
                    }
                else:
                    self.executables.setdefault("Miscellaneous", {})
                    self.executables["Miscellaneous"][name] = {
                        "exe_files": exe_files,
                        "selected_exe": cmd if cmd in exe_files else "Skip",
                        "image-path": image_path,
                        "name": name
                    }
                progress_dialog.setValue(index + 1)
                QApplication.processEvents()
                if progress_dialog.wasCanceled():
                    progress_dialog.close()
                    QMessageBox.warning(self, "Canceled", "JSON loading was canceled.")
                    return
            self.clean_up_special_entries()
            progress_dialog.close()
            QMessageBox.information(self, "Success", f"Loaded and merged {len(config['apps'])} apps.")
            self.update_gui()
        except Exception as e:
            logging.error(f"Failed to load JSON: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load JSON: {e}")

    def load_and_sort_json(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select JSON File", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    config = json.load(f)
                if "apps" in config:
                    apps = config["apps"]
                    logging.info(f"Loaded {len(apps)} apps from {file_path}")
                    sort_dialog = SortDialog(apps, None, self)
                    sort_dialog.exec_()
                else:
                    QMessageBox.warning(self, "Invalid JSON", "The selected JSON file does not contain an 'apps' key.")
            except Exception as e:
                logging.error(f"Failed to load JSON file: {e}")
                QMessageBox.critical(self, "Error", f"Failed to load JSON file: {e}")

    def select_folders(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Scan")
        if folder:
            folder = folder.replace("/", "\\")
            self.base_folders.append(folder)
            self.scan_folders()

    def scan_folders(self):
        total_subfolders = sum(
            len([subfolder for subfolder in os.listdir(folder) if os.path.isdir(os.path.join(folder, subfolder))])
            for folder in self.base_folders
        )
        progress_dialog = QProgressDialog("Scanning folders, please wait...", None, 0, total_subfolders, self)
        progress_dialog.setWindowTitle("Please Wait")
        progress_dialog.setCancelButtonText("Cancel")
        progress_dialog.setWindowModality(Qt.ApplicationModal)
        progress_dialog.show()
        QApplication.processEvents()
        self.executables.setdefault("Special", {})
        special_entries = [
            {
                "name": "Desktop",
                "cmd": None,
                "image-path": "desktop.png",
                "selected_exe": "Include",
                "exe_files": ["Skip", "Include"]
            },
            {
                "name": "Steam Big Picture",
                "cmd": "steam://open/bigpicture",
                "image-path": "steam.png",
                "selected_exe": "Include",
                "exe_files": ["Skip", "Include"]
            }
        ]
        for entry in special_entries:
            self.executables["Special"][entry["name"]] = entry
        processed_subfolders = 0
        for folder in self.base_folders:
            folder = os.path.normpath(folder)
            self.executables.setdefault(folder, {})
            for subfolder in os.listdir(folder):
                subfolder_path = os.path.normpath(os.path.join(folder, subfolder))
                if os.path.isdir(subfolder_path):
                    exe_files = []
                    for root, _, files in os.walk(subfolder_path):
                        exe_files.extend(
                            os.path.normpath(os.path.join(root, f)) for f in files
                            if f.endswith('.exe') and not any(kw in f.lower() for kw in self.FILTER_KEYWORDS)
                        )
                    exe_files = list(set(exe_files))
                    self.executables[folder][subfolder_path] = {
                        "exe_files": ["Skip"] + exe_files,
                        "selected_exe": "Skip",
                        "image-path": "",
                        "name": os.path.basename(subfolder_path)
                    }
                    processed_subfolders += 1
                    progress_dialog.setValue(processed_subfolders)
                    QApplication.processEvents()
                    if progress_dialog.wasCanceled():
                        progress_dialog.close()
                        return
        self.clean_up_special_entries()
        progress_dialog.close()
        self.update_gui()

    def update_gui(self):
        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.takeAt(i).widget()
            if widget:
                widget.deleteLater()
        self.scroll_layout.setAlignment(Qt.AlignTop)
        special_entries = self.executables.get("Special", {})
        if special_entries:
            base_label = QLabel("Special Entries")
            base_label.setStyleSheet("font-weight: bold; color: #FFD700;")
            base_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.scroll_layout.addWidget(base_label)
            for name, data in special_entries.items():
                subfolder_label = QLabel(f"Entry: {data['name']}")
                subfolder_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                self.scroll_layout.addWidget(subfolder_label)
                combo_box = NoScrollComboBox()
                combo_box.addItems(data["exe_files"])
                combo_box.setCurrentText(data["selected_exe"])
                combo_box.currentTextChanged.connect(partial(self.update_selected_exe, data))
                combo_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                self.scroll_layout.addWidget(combo_box)
        for base_folder, subfolders in self.executables.items():
            if base_folder == "Special":
                continue
            base_label = QLabel("Base Folder: " + base_folder.replace("/", "\\"))
            base_label.setStyleSheet("font-weight: bold;")
            base_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.scroll_layout.addWidget(base_label)
            for key, data in subfolders.items():
                subfolder_label = QLabel(f"Entry: {data['name']}")
                subfolder_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                self.scroll_layout.addWidget(subfolder_label)
                combo_box = NoScrollComboBox()
                combo_box.addItems(data["exe_files"])
                combo_box.setCurrentText(data["selected_exe"])
                combo_box.currentTextChanged.connect(partial(self.update_selected_exe, data))
                combo_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                self.scroll_layout.addWidget(combo_box)

    def update_selected_exe(self, subfolder_data, selected_exe):
        subfolder_data["selected_exe"] = selected_exe

    def save_configuration(self):
        flat_apps = []
        added_keys = set()
        for base_folder, subfolders in self.executables.items():
            for subfolder_path, data in subfolders.items():
                if data["selected_exe"] == "Skip":
                    continue
                key = data.get("working-dir", subfolder_path) or data.get("name")
                if key in added_keys:
                    continue
                if base_folder == "Special" and data["selected_exe"] == "Include":
                    flat_apps.append({
                        "name": data["name"],
                        "cmd": None,
                        "exclude-global-prep-cmd": "false",
                        "elevated": "false",
                        "auto-detach": "false",
                        "wait-all": "true",
                        "exit-timeout": "5",
                        "image-path": data.get("image-path", ""),
                        "working-dir": None
                    })
                    added_keys.add(data["name"])
                else:
                    flat_apps.append({
                        "name": data.get("name", os.path.basename(subfolder_path)),
                        "cmd": "\"" + data["selected_exe"].replace("/", "\\") + "\"",
                        "exclude-global-prep-cmd": "false",
                        "elevated": "false",
                        "auto-detach": "false",
                        "wait-all": "true",
                        "exit-timeout": "5",
                        "image-path": data.get("image-path", ""),
                        "working-dir": "\"" + subfolder_path.replace("/", "\\") + "\""
                    })
                    added_keys.add(key)
        for app in self.loaded_apps:
            key = app.get("working-dir") or app.get("name")
            if key not in added_keys:
                flat_apps.append(app)
                added_keys.add(key)
        sort_dialog = SortDialog(flat_apps, None, self)
        sort_dialog.exec_()

def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication([])
    window = FolderScannerApp()
    window.showMaximized()
    app.exec_()

if __name__ == "__main__":
    main()
