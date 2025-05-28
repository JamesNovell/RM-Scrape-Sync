from RM_scraper import VPNLogPuller
from smb_utils import SMBHandler
from log_parser import extract_serial_from_axeda_reports, extract_odometer_lifetime_values
import os
import tempfile
import sys
import argparse

class OdometerFetcher:
    def __init__(self, serial):
        self.serial = serial
        self.username = os.getenv("RSM_USERNAME")
        self.password = os.getenv("RSM_PASSWORD")
        self.smb_user = os.getenv("SMB_USER")
        self.smb_passwords = [os.getenv("SMB_PASSWORD"), os.getenv("SMB_PASSWORD2")]

        if not self.smb_user:
            sys.exit("SMB_USER environment variable not set.")

        self.vpn = VPNLogPuller(self.username, self.password)
        self.smb = None
        self.ip = None

    def fetch_ip(self):
        self.ip = self.vpn.search_and_toggle_by_serial(self.serial)
        if not self.ip:
            sys.exit("Failed to obtain IP.")

    def connect_smb(self):
        self.smb = SMBHandler(self.ip, self.smb_user, self.smb_passwords)
        if not self.smb.connect():
            sys.exit("SMB connection failed.")

    def fetch_and_parse_log(self):
        remote_path = "ProgramData\\R50\\Axeda\\Reports"
        files = self.smb.list_files(remote_path, regex=r"\.txt$", days_back=7)
        if not files:
            sys.exit("No recent log files found.")

        latest_file = sorted(files, key=lambda f: f.last_write_time, reverse=True)[0]

        with tempfile.TemporaryDirectory() as tmp_dir:
            local_path = self.smb.download_file(remote_path, latest_file.filename, tmp_dir)
            if local_path:
                print(f"Downloaded: {local_path}")
                dispenses, acceptance, bnr_total = extract_odometer_lifetime_values(local_path)
                print(f"Dispenses: {dispenses}, Acceptance: {acceptance}, BNR Total: {bnr_total}")
                return dispenses, acceptance, bnr_total
            else:
                print("File download failed.")
                return None, None, None

    def cleanup(self):
        if self.smb:
            self.smb.close()
        self.vpn.search_and_toggle_off_by_serial(self.serial)

if __name__ == "__main__":
    print(os.getenv("SMB_USER"))

    parser = argparse.ArgumentParser(description="Fetch and analyze odometer log for a given serial number.")
    parser.add_argument("serial", nargs="?", default="N4R02011", help="Serial number of the unit")
    args = parser.parse_args()

    fetcher = OdometerFetcher(args.serial)
    fetcher.fetch_ip()
    fetcher.connect_smb()
    fetcher.fetch_and_parse_log()
    fetcher.cleanup()
