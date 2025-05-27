import requests
from bs4 import BeautifulSoup
from soup2dict import convert
import re
import pickle
import os
import json

class VPNLogPuller:
    def __init__(self, username, password):
        self.session = requests.Session()
        self.login_url = 'https://rsm.tidel.com/Account/Login'
        self.device_list_url = 'https://rsm.tidel.com/DeviceList?pageIndex='
        self.activity_url = 'https://rsm.tidel.com/ActivityTracker/SaveActivity'
        self.toggle_url = 'https://rsm.tidel.com/VPN/ToggleVPN'
        self.serial_number_list = []
        self.cookie_file = 'session_cookies.pkl'
        self.username = username
        self.password = password

    def save_session(self):
        with open(self.cookie_file, 'wb') as f:
            pickle.dump(self.session.cookies, f)

    def load_session(self):
        if os.path.exists(self.cookie_file):
            with open(self.cookie_file, 'rb') as f:
                cookies = pickle.load(f)
                self.session.cookies.update(cookies)
                print("Session loaded from file.")
                return True
        return False

    def login(self):
        if self.load_session():
            test_response = self.session.get(self.device_list_url + '1')
            if "Login" not in test_response.text:
                print("Already logged in.")
                return
            else:
                print("Session expired, logging in again.")

        g = self.session.get(self.login_url)
        token = BeautifulSoup(g.text, 'html.parser').find('input', {'name': '__RequestVerificationToken'})['value']
        payload = {
            'Username': self.username,
            'Password': self.password,
            '__RequestVerificationToken': token
        }
        self.session.post(self.login_url, data=payload)
        self.save_session()
        print("Logged in and session saved.")

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
                return True
            else:
                print('page', page_number)
        return False

    def search_and_toggle_by_serial(self, target_serial):
        self.login()
        search_url = f"https://rsm.tidel.com/DeviceList?SearchSerialNumber={target_serial}&PageSize=25&PageIndex=1"
        r = self.session.get(search_url)
        soup = BeautifulSoup(r.content, 'lxml')
    
        # Try to get IP address
        td = soup.find("td", id=f'{target_serial}Address')
        ip = td.text.strip() if td else None
    
        if ip:
            print(f"IP for {target_serial} is {ip}")
            return ip  # Exit early if IP is already available
    
        # If IP not found, attempt to toggle VPN
        activity_response, toggle_response = self._toggle_VPN(target_serial)
    
        # Parse the returned response
        try:
            raw = toggle_response.text
            if raw.startswith('"') and raw.endswith('"'):
                raw = raw[1:-1]
            raw = raw.replace('\\u0022', '"')
            response_data = json.loads(raw)
            vpn_address = response_data["MessageData"]["VPNAddress"]
            print(f"New VPN IP: {vpn_address}")
            return vpn_address
        except json.JSONDecodeError as e:
            print("Failed to parse JSON:", e)
            print("Raw response:", raw)
            return None
        except KeyError as e:
            print("Key not found in response data:", e)
            print("Parsed response:", response_data)
            return None
        except Exception as e:
            print("Unexpected error:", e)
            print("Raw response:", raw)
            return None
    
    def search_and_toggle_off_by_serial(self, target_serial):
        self.login()
        search_url = f"https://rsm.tidel.com/DeviceList?SearchSerialNumber={target_serial}&PageSize=25&PageIndex=1"
        r = self.session.get(search_url)
        soup = BeautifulSoup(r.content, 'lxml')
    
        td = soup.find("td", id=f'{target_serial}Address')
        ip = td.text.strip() if td else None
    
        if ip:
            print(f"The VPN is on for {target_serial}, turning it off.")
            self._toggle_VPN(target_serial, turn_on=False)
    
    def _toggle_VPN(self, target_serial, turn_on=True):
        search_url = f"https://rsm.tidel.com/DeviceList?SearchSerialNumber={target_serial}&PageSize=25&PageIndex=1"
        r = self.session.get(search_url)
        soup = BeautifulSoup(r.content, 'lxml')
    
        vpn_button = soup.find("button", id=f"{target_serial}VPN")
        if not vpn_button:
            print("VPN button not found.")
            return None, None
    
        onclick_attr = vpn_button.get("onclick", "")
        device_id_match = re.search(r"'([0-9a-fA-F\-]{36})'", onclick_attr)
    
        if not device_id_match:
            print("Device ID not found in onclick attribute.")
            return None, None
    
        device_id = device_id_match.group(1)
        print(f"Device ID: {device_id}")
    
        payload2 = {
            'email': self.username,
            'device': device_id,
            'function': 'VPN'
        }
        payload3 = {
            'deviceId': device_id,
            'serialNumber': target_serial
        }
    
        if turn_on:
            activity_response = self.session.post(self.activity_url, data=payload2)
            toggle_response = self.session.post(self.toggle_url, data=payload3)
            print(f"VPN toggled ON for serial {target_serial}")
        else:
            toggle_response = self.session.post(self.toggle_url, data=payload3)
            print(f"VPN toggled OFF for serial {target_serial}")
            activity_response = None
    
        return activity_response, toggle_response

    def perform_function(self):
        print("Performing your function with the VPN connection active...")
        # Example: pull logs
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
    vpn = VPNLogPuller(os.getenv("RSM_USERNAME"), os.getenv("RSM_PASSWORD"))
    # vpn.run()  # Normal run
    vpn.search_and_toggle_by_serial("N4R02011")    # Search for one serial
    vpn._toggle_VPN("N4R02011", turn_on=False)