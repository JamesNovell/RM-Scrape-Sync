import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit,
    QLabel, QDialog, QLineEdit, QFormLayout, QDialogButtonBox
)
from PyQt5.QtCore import QThread, pyqtSignal
from vpn_log_pull_object import VPNLogPuller

class CredentialDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enter Credentials")
        self.username = ""
        self.password = ""

        layout = QFormLayout(self)

        self.username_input = QLineEdit(self)
        self.password_input = QLineEdit(self)
        self.password_input.setEchoMode(QLineEdit.Password)

        layout.addRow("Username:", self.username_input)
        layout.addRow("Password:", self.password_input)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def get_credentials(self):
        return self.username_input.text(), self.password_input.text()

class VPNWorker(QThread):
    log_signal = pyqtSignal(str)

    def __init__(self, username, password):
        super().__init__()
        self.username = username
        self.password = password

    def run(self):
        self.vpn = VPNLogPuller()
        self.vpn.set_credentials(self.username, self.password)
        self.vpn.login()
        self.log_signal.emit("Logged in.")

        if self.vpn.fetch_vpn_info():
            self.log_signal.emit("VPN info fetched.")
            self.vpn.toggle_vpn(turn_on=True)
            self.log_signal.emit("VPN toggled ON.")
            self.vpn.perform_function()
            self.log_signal.emit("Function performed.")
            self.vpn.toggle_vpn(turn_on=False)
            self.log_signal.emit("VPN toggled OFF.")
        else:
            self.log_signal.emit("No VPN devices found.")

class VPNApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('VPN Log Puller')
        self.setGeometry(200, 200, 400, 300)

        self.layout = QVBoxLayout()

        self.label = QLabel("Click the button to run VPN Log Puller")
        self.layout.addWidget(self.label)

        self.button = QPushButton("Run VPN Log Pull")
        self.button.clicked.connect(self.prompt_credentials)
        self.layout.addWidget(self.button)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.layout.addWidget(self.output)

        self.setLayout(self.layout)

    def prompt_credentials(self):
        dialog = CredentialDialog()
        if dialog.exec_() == QDialog.Accepted:
            username, password = dialog.get_credentials()
            self.run_vpn_task(username, password)

    def run_vpn_task(self, username, password):
        self.worker = VPNWorker(username, password)
        self.worker.log_signal.connect(self.update_log)
        self.worker.start()

    def update_log(self, message):
        self.output.append(message)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = VPNApp()
    ex.show()
    sys.exit(app.exec_())
