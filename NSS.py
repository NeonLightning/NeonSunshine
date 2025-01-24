from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog,
    QScrollArea, QComboBox, QMessageBox, QProgressDialog, QSizePolicy,
    QDialog, QListWidget, QListWidgetItem, QLineEdit, QHBoxLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
import os, json, signal

class SortDialog(QDialog):
    def __init__(self, apps, json_file_path, parent=None):
        super().__init__(parent)
        self.setWindowIcon(QIcon('icon.ico'))
        self.setWindowTitle("Sort JSON Entries")
        self.setStyleSheet("""
            QWidget {
                background-color: #2e2e2e;
                color: #ffffff;
            }
            QPushButton {
                background-color: #444444;
                color: #ffffff;
                border: 1px solid #555555;
            }
            QPushButton:hover {
                background-color: #555555;
            }
            QLineEdit {
                background-color: #3e3e3e;
                color: #ffffff;
                border: 1px solid #555555;
            }
        """)
        self.apps = apps
        self.json_file_path = json_file_path
        self.cmd_edits = {}
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
        save_button = QPushButton("Save Sorted JSON")
        save_button.clicked.connect(self.save_sorted_json)
        layout.addWidget(save_button)
        self.showMaximized()

    def create_app_widget(self, app):
        widget = QWidget()
        layout = QHBoxLayout()
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

    def save_sorted_json(self):
        reordered_apps = []
        for i in range(self.list_widget.count()):
            list_item = self.list_widget.item(i)
            item_widget = self.list_widget.itemWidget(list_item)
            name_label = item_widget.layout().itemAt(0).widget()
            cmd_edit = self.cmd_edits[name_label.text()]
            for app in self.apps:
                if app.get("name") == name_label.text():
                    app["cmd"] = cmd_edit.text()
                    reordered_apps.append(app)
                    break
        try:
            with open(self.json_file_path, 'w') as f:
                json.dump({"env": "", "apps": reordered_apps}, f, indent=4)
            QMessageBox.information(self, "Success", f"Configuration saved to {self.json_file_path}")
            self.parent().close()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {e}")

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
                    "working-dir": subfolder_path.replace("/", "\\") + "\\"
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
