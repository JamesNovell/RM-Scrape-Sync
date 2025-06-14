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
    dispenses = acceptance = bnr_total = None

    with open(file_path, 'r') as f:
        for line in f:
            line = line.rstrip()

            if line.startswith("Dispenses"):
                dispenses = int(line[20:32].strip())
            elif line.startswith("Acceptance"):
                acceptance = int(line[20:32].strip())
            elif line.startswith("BNR Total"):
                bnr_total = int(line[20:32].strip())

            if dispenses is not None and acceptance is not None and bnr_total is not None:
                break

    return dispenses, acceptance, bnr_total

