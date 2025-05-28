import os, re

serial_pattern = re.compile(r"[NR][497F3][RFG/-]\d{4,5}")

#file to parse is located in c$\ProgramData\R50\Axeda\Reports\*.txt
def extract_serial_from_axeda_reports(directory):
    serial_pattern = re.compile(r"[NR][497F3][RFG/-]\d{4,5}")
    try:
        txt_files = [f for f in os.listdir(directory) if f.endswith(".txt")]
        txt_files.sort(key=lambda f: os.path.getmtime(os.path.join(directory, f)), reverse=True)
        if not txt_files:
            return "UNKNOWN"

        latest_file = txt_files[0]
        with open(os.path.join(directory, latest_file), 'r') as file:
            for line in file:
                match = serial_pattern.search(line)
                if match:
                    return match.group(0)
    except Exception as e:
        print(f"Error reading serial from reports: {e}")

    return "UNKNOWN"

#file to parse C$\R50\DeviceConfiguration.config
def extract_serial_from_deviceconfiguration(directory):
    config_file = "DeviceConfiguration.config"
    try:
        full_path = os.path.join(directory, config_file)
        if not os.path.exists(full_path):
            return "UNKNOWN"

        with open(full_path, 'r') as file:
            for line in file:
                match = serial_pattern.search(line)
                if match:
                    return match.group(0)
    except Exception as e:
        print(f"Error reading serial from config: {e}")

    return "UNKNOWN"

#file to parse is located in c$\ProgramData\R50\Axeda\Reports\*.txt
def extract_odometer_lifetime_values(file_path):
    marker = "----------------- ----------------- ----------------- -----------------"
    block_found = False
    line_count = 0
    dispenses = acceptance = bnr_total = None

    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line == marker:
                block_found = True
                line_count = 0
                continue

            if block_found:
                line_count += 1
                parts = line.split()
                if not parts or len(parts) < 2:
                    continue

                if parts[0] == "Dispenses":
                    dispenses = int(parts[1])
                elif parts[0] == "Acceptance":
                    acceptance = int(parts[1])
                elif parts[0] == "BNR" and parts[1] == "Total":
                    bnr_total = int(parts[2])

                if line_count >= 3:
                    break

    return dispenses, acceptance, bnr_total
