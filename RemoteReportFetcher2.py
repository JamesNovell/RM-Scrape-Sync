import os
import zipfile
import requests
import datetime
import argparse
import re
from smb.SMBConnection import SMBConnection


class NetworkAutomation:
    def __init__(self, ip=None, base_path=None, start_date=None, end_date=None, vpn_name="TidelPRODVPN2032", file_regex=None, smb_user="TIDEL\Tservice"):
        self.vpn_name = vpn_name
        self.main_path = base_path or os.getcwd()
        self.serial = ""
        self.ip = ip
        self.loopnum = 1
        self.serial2 = ""
        self.first_three = ""
        self.username = os.getlogin()
        self.start_date = start_date
        self.end_date = end_date
        self.age = None
        self.log_directory = None
        self.file_regex = file_regex
        self.smb_user = smb_user
        self.passwords = [
            os.getenv("E4_PASS1"),
            os.getenv("E4_PASS2")
        ]



    @staticmethod
    def validate_ip(ip):
        parts = ip.split('.')
        return len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts)

    def smb_connect(self, username, password):
        conn = SMBConnection(
            username, password,
            "local_machine", "remote_machine",
            domain="TIDEL", use_ntlm_v2=True
        )
        connected = conn.connect(self.ip, 139)
        return conn if connected else None

    def get_serial(self, directory):
        try:
            txt_files = [f for f in os.listdir(directory) if f.endswith(".txt")]
            txt_files.sort(key=lambda f: os.path.getmtime(os.path.join(directory, f)), reverse=True)
            latest_file = txt_files[0]

            with open(os.path.join(directory, latest_file), 'r') as file:
                for line in file:
                    if "Note Recycler Serial Number:" in line:
                        self.serial = line.strip().split()[-1]
                        return self.serial
        except Exception as e:
            print(f"Failed to extract serial: {e}")

        self.serial = "UNKNOWN"
        return self.serial

    def determine_log_directory(self):
        now = datetime.datetime.now()
        formatted_date = now.strftime("%Y-%m-%d")
        self.serial2 = self.serial
        self.serial = f"{self.serial}_{formatted_date}"
        self.first_three = self.serial2[:3]
        base_paths = {
            "N4R": "logs/GRG_CRM9250T_Logs",
            "N3G": "GloryTraceLogs",
            "N9R": "logs/GRG_CRM9250N_Logs"
        }
        base_path = base_paths.get(self.first_three, "logs/Unknown")

        while True:
            log_dir = os.path.join(self.main_path, base_path, f"{self.serial} ({self.loopnum})")
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
                self.log_directory = log_dir
                break
            self.loopnum += 1

    def download_logs(self):
        smb_paths = {
            "N4R": "ProgramData/R50/Log/Bcr/CRM9250TLog/dev",
            "N3G": "ProgramData/R50/Log/Bcr/TraceLogs",
            "N9R": "Bcr/CRM9250NLog"
        }
        remote_path = smb_paths.get(self.first_three)
        share_name = "C$"

        if not remote_path:
            print("Unknown model prefix.")
            return

        pattern = re.compile(self.file_regex) if self.file_regex else None

        for password in self.passwords:
            conn = self.smb_connect(self.smb_user.split('\')[-1], password)
            if conn:
                try:
                    files = conn.listPath(share_name, remote_path)
                    for file in files:
                        if file.isDirectory or file.filename in ['.', '..']:
                            continue

                        if pattern and not pattern.search(file.filename):
                            continue

                        file_date = datetime.datetime.fromtimestamp(file.last_write_time)
                        if self.start_date:
                            start = datetime.datetime.strptime(self.start_date, "%Y%m%d")
                            if file_date < start:
                                continue
                        if self.end_date:
                            end = datetime.datetime.strptime(self.end_date, "%Y%m%d")
                            if file_date > end:
                                continue

                        local_file_path = os.path.join(self.log_directory, file.filename)
                        with open(local_file_path, 'wb') as f:
                            conn.retrieveFile(share_name, f"{remote_path}/{file.filename}", f)

                        if file.filename.endswith(".zip"):
                            with zipfile.ZipFile(local_file_path, 'r') as zip_ref:
                                zip_ref.extractall(self.log_directory)
                            os.remove(local_file_path)
                except Exception as e:
                    print(f"Error copying files from SMB: {e}")
                finally:
                    conn.close()
                break

    def send_api_notification(self):
        url = "http://54.197.108.163:8000/api/endpoint"
        payload = {"username": self.username, "message": self.serial}
        try:
            requests.post(url, json=payload)
        except requests.RequestException as e:
            print(f"Failed to send API request: {e}")

    def run(self):

        conn = None
        for password in self.passwords:
            if password:
                conn = self.smb_connect(self.smb_user.split('\')[-1], password)
                if conn:
                    break

        if not conn:
            print("Failed to connect via SMB with provided environment credentials.")
            return

        self.determine_log_directory()
        self.download_logs()
        self.get_serial(self.log_directory)
        self.send_api_notification()
        print("Process completed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Network Log Automation Tool")
    parser.add_argument("--user", help="SMB user in the format DOMAIN\username", default="TIDEL\Tservice")
    parser.add_argument("--ip", help="IP address of the unit")
    parser.add_argument("--path", help="Base path to save logs", default=os.getcwd())
    parser.add_argument("--start", help="Start date in YYYYMMDD format")
    parser.add_argument("--end", help="End date in YYYYMMDD format")
    parser.add_argument("--vpn", help="VPN connection name", default="TidelPRODVPN2032")
    parser.add_argument("--regex", help="Regex pattern to filter filenames")
    args = parser.parse_args()

    tool = NetworkAutomation(
        smb_user=args.user,
        ip=args.ip,
        base_path=args.path,
        start_date=args.start,
        end_date=args.end,
        vpn_name=args.vpn,
        file_regex=args.regex
    )
    tool.run()
