import sys
import os
import winreg
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLineEdit,
    QPushButton, QLabel, QMessageBox
)

class EnvEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Windows Environment Variable Setter")
        self.setGeometry(300, 300, 400, 200)

        self.layout = QVBoxLayout()

        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("Variable name (e.g., RSM_USERNAME)")
        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("Value (e.g., myuser@domain.com)")

        self.save_button = QPushButton("Save to User Environment")
        self.save_button.clicked.connect(self.save_env_var)

        self.layout.addWidget(QLabel("Set Environment Variable"))
        self.layout.addWidget(self.key_input)
        self.layout.addWidget(self.value_input)
        self.layout.addWidget(self.save_button)

        self.setLayout(self.layout)

    def save_env_var(self):
        key = self.key_input.text().strip()
        value = self.value_input.text().strip()

        if not key or not value:
            QMessageBox.warning(self, "Missing Input", "Both key and value are required.")
            return

        try:
            # Save to user environment variables (not system-wide)
            reg_key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                "Environment",
                0,
                winreg.KEY_SET_VALUE
            )
            winreg.SetValueEx(reg_key, key, 0, winreg.REG_SZ, value)
            winreg.CloseKey(reg_key)

            # Notify the system that env vars have changed (current session won't see it until restart)
            import ctypes
            HWND_BROADCAST = 0xFFFF
            WM_SETTINGCHANGE = 0x001A
            SMTO_ABORTIFHUNG = 0x0002
            ctypes.windll.user32.SendMessageTimeoutW(HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment", SMTO_ABORTIFHUNG, 5000, None)

            QMessageBox.information(self, "Success", f"{key} was saved as a user environment variable.\nYou may need to restart apps to see changes.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to set environment variable:\n{str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = EnvEditor()
    editor.show()
    sys.exit(app.exec_())
