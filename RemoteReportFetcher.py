import os
import shutil
import re
import subprocess
from datetime import datetime, timedelta

class ReportProcessor:
    def __init__(self, ip, file_dir, start_date=None, end_date=None):
        self.ip = ip
        self.file_dir = file_dir
        self.start_date = start_date
        self.end_date = end_date or start_date
        self.serial = None
        self.output_paths = []
        self.temp_file = "temp_report.txt"
        self.password1 = os.getenv("PROD_ENV1", "")
        self.password2 = os.getenv("PROD_ENV2", "")

    def mount_share(self):
        unc_path = f"\\{self.ip}\\c$"
        result = subprocess.run(
            ["net", "use", unc_path, "/user:TIDEL\\Tservice", self.password1],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        if result.returncode != 0:
            result = subprocess.run(
                ["net", "use", unc_path, "/user:TIDEL\\Tservice", self.password2],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        return result.returncode == 0

    def find_matching_file(self, pattern):
        try:
            for file in os.listdir(self.file_dir):
                if re.search(pattern, file):
                    return file
        except FileNotFoundError:
            pass
        return None

    def extract_serial(self):
        try:
            files = [f for f in os.listdir(self.file_dir) if f.endswith(".txt")]
            files.sort(key=lambda f: os.path.getmtime(os.path.join(self.file_dir, f)), reverse=True)
            latest_file = files[0]
            with open(os.path.join(self.file_dir, latest_file), 'r') as file:
                for line in file:
                    if "Note Recycler Serial Number:" in line:
                        self.serial = line.strip().split()[-1]
                        return self.serial
        except Exception:
            pass
        self.serial = "UNKNOWN"
        return self.serial

    def extract_report_block(self, date):
        block_found = False
        line_count = 0
        mm, dd, yyyy = date.strftime('%m'), date.strftime('%d'), date.strftime('%Y')

        output_dir = os.path.join("Reports", self.serial)
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{self.serial}_{mm}_{dd}_{yyyy}.txt")

        with open(self.temp_file, 'r') as file, open(output_path, 'w') as out:
            out.write(f"{self.serial} on {date.strftime('%m/%d/%Y')}\n")
            for line in file:
                if "----------------- ----------------- ----------------- -----------------" in line:
                    block_found = True
                    line_count = 0
                    continue

                if block_found:
                    line_count += 1
                    if 1 <= line_count <= 3:
                        parts = line.strip().split()
                        if len(parts) >= 3:
                            if parts[0] + ' ' + parts[1] == "BNR Total":
                                out.write(f"BNR Total:     {parts[2]}\n")
                            else:
                                out.write(f"{parts[0]}:     {parts[1]}\n")
                    elif line_count > 3:
                        break

        self.output_paths.append(output_path)

    def process(self):
        if not self.mount_share():
            raise ConnectionError("Failed to authenticate to the remote system.")

        if not self.start_date:
            self.start_date = datetime.now() - timedelta(days=1)
            self.end_date = self.start_date

        current_date = self.start_date
        while current_date <= self.end_date:
            pattern = current_date.strftime("%Y%m%d.*\\.txt")
            file_name = self.find_matching_file(pattern)
            if not file_name:
                print(f"No matching report for {current_date.strftime('%Y-%m-%d')}")
            else:
                shutil.copy(os.path.join(self.file_dir, file_name), self.temp_file)
                self.extract_serial()
                self.extract_report_block(current_date)
            current_date += timedelta(days=1)

        return self.output_paths

# Example usage
if __name__ == "__main__":
    processor = ReportProcessor(
        ip="192.168.1.100",
        file_dir=r"\\192.168.1.100\c$\ProgramData\R50\Reports",
        start_date=datetime(2025, 5, 20),
        end_date=datetime(2025, 5, 22)
    )

    try:
        result_paths = processor.process()
        for path in result_paths:
            print(f"Report saved to: {path}")
    except Exception as e:
        print(f"Error: {e}")
