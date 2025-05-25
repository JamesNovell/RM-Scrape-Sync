import requests
from bs4 import BeautifulSoup
import creds
from soup2dict import convert
import re

class VPNLogPuller:
    def __init__(self):
        self.session = requests.Session()
        self.login_url = 'https://rsm.tidel.com/Account/Login'
        self.device_list_url = 'https://rsm.tidel.com/DeviceList?pageIndex='
        self.activity_url = 'https://rsm.tidel.com/ActivityTracker/SaveActivity'
        self.toggle_url = 'https://rsm.tidel.com/VPN/ToggleVPN'
        self.serial_number_list = []

    def login(self):
        g = self.session.get(self.login_url)
        token = BeautifulSoup(g.text, 'html.parser').find('input', {'name': '__RequestVerificationToken'})['value']
        payload = {
            'Username': creds.username,
            'Password': creds.password,
            '__RequestVerificationToken': token
        }
        self.session.post(self.login_url, data=payload)

    def fetch_vpn_info(self):
        for page_number in range(1, 273):
            r = self.session.get(self.device_list_url + str(page_number))
            soup = BeautifulSoup(r.content, 'lxml')
            vpn_buttons = str(soup.find_all("button", class_='btn btn-sm btn-success text-white font-weight-bold'))

            serial_number_compiler = re.compile(r'[A-Z][A-Z0-9]{2,}[0-9]{4,5}')
            serial_number = serial_number_compiler.findall(vpn_buttons)

            if serial_number:
                print('page', page_number, '>>> found >>>', serial_number)
                self.serial_number_list.append(serial_number)
                self.device_codes = re.findall(r'[\w\d]+\-[\w\d]+\-[\w\d]+\-[\w\d]+\-[\w\d]+', vpn_buttons)
                self.serial_vpn = re.findall(r'[A-Z0-9]+[0-9]{5}', vpn_buttons)
                return True  # Exit after finding the first one
            else:
                print('page', page_number)
        return False

    def toggle_vpn(self, turn_on=True):
        if not hasattr(self, 'device_codes') or not hasattr(self, 'serial_vpn'):
            raise Exception("No VPN device info loaded. Run fetch_vpn_info() first.")

        payload2 = {
            'email': creds.username,
            'device': self.device_codes,
            'function': 'VPN'
        }
        payload3 = {
            'deviceId': self.device_codes,
            'serialNumber': self.serial_vpn
        }

        if turn_on:
            self.session.post(self.activity_url, data=payload2)
            self.session.post(self.toggle_url, data=payload3)
            print("VPN toggled ON")
        else:
            self.session.post(self.toggle_url, data=payload3)
            print("VPN toggled OFF")

    def perform_function(self):
        print("Performing your function with the VPN connection active...")
        # Example: pull logs
        # logs = self.session.get("https://rsm.tidel.com/log_url_here")
        # print(logs.text)
        print("Function complete.")

    def run(self):
        self.login()
        if self.fetch_vpn_info():
            self.toggle_vpn(turn_on=True)
            self.perform_function()
            self.toggle_vpn(turn_on=False)
        else:
            print("No VPN devices found.")

if __name__ == "__main__":
    vpn = VPNLogPuller()
    vpn.run()