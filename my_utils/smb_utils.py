# smb_utils.py
import os
import datetime
import socket
from smb.SMBConnection import SMBConnection

class SMBHandler:
    def __init__(self, ip, smb_user, passwords, share_name="C$"):
        self.ip = ip
        self.smb_user = smb_user
        self.passwords = passwords
        self.share_name = share_name
        self.connection = None


    def connect(self):
        domain, username = self.smb_user.split('\\')
        hostname = socket.gethostname()
        for password in self.passwords:
            if not password:
                continue
            conn = SMBConnection(
                username, password,
                hostname, self.ip,
                domain=domain, use_ntlm_v2=True, is_direct_tcp=True
            )
            if conn.connect(self.ip, 445):
                self.connection = conn
                return True
        return False


    def list_files(self, remote_path, regex=None, start_date=None, end_date=None, days_back=None):
        import re
        files = []
        if not self.connection:
            return files

        pattern = re.compile(regex) if regex else None

        if days_back is not None:
            start_date = datetime.datetime.now() - datetime.timedelta(days=days_back)
        try:
            for file in self.connection.listPath(self.share_name, remote_path):
                if file.isDirectory or file.filename in ['.', '..']:
                    continue
                if pattern and not pattern.search(file.filename):
                    continue
                file_date = datetime.datetime.fromtimestamp(file.last_write_time)
                if start_date and file_date < start_date:
                    continue
                if end_date and file_date > end_date:
                    continue
                files.append(file)
        except Exception as e:
            print(f"Error listing files: {e}")
        return files

    def download_file(self, remote_path, filename, dest_dir):
        local_file_path = os.path.join(dest_dir, filename)
        try:
            with open(local_file_path, 'wb') as f:
                self.connection.retrieveFile(self.share_name, f"{remote_path}/{filename}", f)
            return local_file_path
        except Exception as e:
            print(f"Failed to download {filename}: {e}")
        return None

    def close(self):
        if self.connection:
            self.connection.close()
