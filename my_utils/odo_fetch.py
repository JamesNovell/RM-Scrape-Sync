from RM_scraper import VPNLogPuller
from smb_utils import SMBHandler
from log_parser import extract_serial_from_axeda_reports, extract_odometer_lifetime_values
import os
import tempfile
import sys
import argparse
from datetime import datetime, timedelta

class OdometerFetcher:
    def __init__(self, serial):
        print(f"[INIT] Initializing fetcher for serial: {serial}")
        self.serial = serial
        self.username = os.getenv("RSM_USERNAME")
        self.password = os.getenv("RSM_PASSWORD")
        self.smb_user = os.getenv("SMB_USER")
        self.smb_passwords = [os.getenv("SMB_PASSWORD"), os.getenv("SMB_PASSWORD2")]

        if not self.smb_user:
            sys.exit("[ERROR] SMB_USER environment variable not set.")

        self.vpn = VPNLogPuller(self.username, self.password)
        self.smb = None
        self.ip = None

    def fetch_ip(self):
        print("[INFO] Attempting to fetch IP...")
        self.ip = self.vpn.search_and_toggle_by_serial(self.serial)
        if not self.ip:
            sys.exit("[ERROR] Failed to obtain IP.")
        print(f"[SUCCESS] IP obtained: {self.ip}")

    def connect_smb(self):
        print("[INFO] Attempting SMB connection...")
        self.smb = SMBHandler(self.ip, self.smb_user, self.smb_passwords)
        if not self.smb.connect():
            sys.exit("[ERROR] SMB connection failed.")
        print("[SUCCESS] SMB connection established.")
        
    def fetch_and_parse_log(self, target_date=None, fallback_if_none=True):
        print("[INFO] Fetching and parsing log...")
        remote_path = "ProgramData\\R50\\Axeda\\Reports"
        try:
            all_files = self.smb.list_files(remote_path)
            print(f"[DEBUG] Total files in directory '{remote_path}': {len(all_files)}")
            for f in all_files:
                print(f" - {f.filename} (Last modified: {datetime.fromtimestamp(f.last_write_time)})")
            
            files = [f for f in all_files if f.filename.endswith(".txt")]
            print(f"[INFO] Found {len(files)} .txt files in remote path.")        
        except Exception as e:
            print(f"[ERROR] Failed to list files: {e}")
            return None, None, None

        if not files:
            print("[ERROR] No log files found.")
            return None, None, None

        selected_file = None
        if target_date:
            print(f"[INFO] Filtering by date: {target_date}")
            try:
                base_date = datetime.strptime(target_date, "%m/%d/%Y")
                max_offset_days = 5  # max days to look ahead/behind
                for offset in range(max_offset_days + 1):
                    for delta in [-offset, offset] if offset != 0 else [0]:
                        check_date = base_date + timedelta(days=delta)
                        check_str = check_date.strftime("%Y%m%d")
                        matching_files = [f for f in files if check_str in f.filename]
                        if matching_files:
                            print(f"[INFO] Found {len(matching_files)} files for {check_str} (offset {delta} days)")
                            selected_file = sorted(matching_files, key=lambda f: f.last_write_time, reverse=True)[0]
                            break
                    if selected_file:
                        break
                if not selected_file:
                    print(f"[ERROR] No files found within +/- {max_offset_days} days of {target_date}")
                    return None, None, None
            except ValueError:
                print("[ERROR] Invalid date format. Use MM/DD/YYYY.")
                return None, None, None
            except Exception as e:
                print(f"[ERROR] Unexpected error during date scan: {e}")
                return None, None, None
        else:
            print("[INFO] No date specified, using latest file available.")
            selected_file = sorted(files, key=lambda f: f.last_write_time, reverse=True)[0]

        print(f"[INFO] Selected file: {selected_file.filename}")
        with tempfile.TemporaryDirectory() as tmp_dir:
            try:
                local_path = self.smb.download_file(remote_path, selected_file.filename, tmp_dir)
                print(f"[INFO] File downloaded to: {local_path}")
            except Exception as e:
                print(f"[ERROR] Failed to download file: {e}")
                return None, None, None

            if local_path:
                try:
                    print("[INFO] Extracting odometer values...")
                    dispenses, acceptance, bnr_total = extract_odometer_lifetime_values(local_path)
                    print(f"[RESULTS] Dispenses: {dispenses}, Acceptance: {acceptance}, BNR Total: {bnr_total}")
                    if fallback_if_none and all(v is None for v in [dispenses, acceptance, bnr_total]) and target_date:
                        print("[WARN] All values are None. Retrying with ±5 day scan.")
                        return self.fetch_and_parse_log(target_date=target_date, fallback_if_none=False)
                    return dispenses, acceptance, bnr_total
                except Exception as e:
                    print(f"[ERROR] Failed to extract odometer values: {e}")
                    return None, None, None
            else:
                print("[ERROR] File download returned None.")
                return None, None, None

    def cleanup(self):
        print("[INFO] Cleaning up...")
        if self.smb:
            self.smb.close()
            print("[INFO] SMB connection closed.")
        self.vpn.search_and_toggle_off_by_serial(self.serial)
        print("[INFO] VPN toggled off.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch and analyze odometer log for a given serial number.")
    parser.add_argument("serial", nargs="?", default="N4R01384", help="Serial number of the unit")
    parser.add_argument("--date", help="Target log file date in MM/DD/YYYY format (e.g. 1/28/2025)", default=None)
    args = parser.parse_args()

    print(f"[MAIN] Starting for serial: {args.serial}, Date: {args.date}")
    fetcher = OdometerFetcher(args.serial)
    fetcher.fetch_ip()
    fetcher.connect_smb()
    fetcher.fetch_and_parse_log(target_date=args.date)
    fetcher.cleanup()
    print("[MAIN] Done.")