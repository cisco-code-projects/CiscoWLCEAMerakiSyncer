import requests
from requests.auth import HTTPBasicAuth
import urllib3
import logging
from typing import List, Dict

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class WLCConnector:
    def __init__(self, host, username, password, port=22): 
        # Port argument kept for compatibility but not used for HTTP (assumes 443)
        self.host = host
        self.username = username
        self.password = password
        self.logger = logging.getLogger(__name__)
        self.base_url = f"https://{self.host}/restconf/data"
        self.headers = {
            "Accept": "application/yang-data+json",
            "Content-Type": "application/yang-data+json"
        }

    def get_aps(self) -> List[Dict[str, str]]:
        """
        Retrieves details of all APs via RESTCONF 'access-point-oper-data'.
        Returns a list of dictionaries with keys: 'name', 'model', 'radio_mac', 'eth_mac', 'serial', 'meraki_serial'.
        """
        try:
            self.logger.info(f"Connecting to WLC at {self.host} (HTTPS)...")
            
            auth = HTTPBasicAuth(self.username, self.password)
            ap_url = f"{self.base_url}/Cisco-IOS-XE-wireless-access-point-oper:access-point-oper-data"
            
            response = requests.get(ap_url, auth=auth, headers=self.headers, verify=False, timeout=30)
            
            if response.status_code != 200:
                self.logger.error(f"Failed to fetch AP data. Status: {response.status_code}, Response: {response.text}")
                response.raise_for_status()
                
            data = response.json()
            return self._parse_ap_inventory(data)
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve APs from WLC via RESTCONF: {e}")
            raise

    def _parse_ap_inventory(self, data: Dict) -> List[Dict[str, str]]:
        """
        Parses the RESTCONF JSON output.
        """
        aps = []
        
        # Navigate to capwap-data list
        root = data.get("Cisco-IOS-XE-wireless-access-point-oper:access-point-oper-data", {})
        capwap_list = root.get("capwap-data", [])
        
        for item in capwap_list:
            try:
                # Basic fields
                name = item.get("name", "Unknown")
                radio_mac = item.get("wtp-mac", "")
                
                # Nested fields
                # Check for meraki capability first or extract it
                meraki_info = item.get("meraki-info", {})
                meraki_serial = meraki_info.get("serial-num", "")
                
                # Check deep device details
                device_detail = item.get("device-detail", {})
                static_info = device_detail.get("static-info", {})
                
                # Model
                ap_models = static_info.get("ap-models", {})
                model = ap_models.get("model", "Unknown")
                
                # Eth MAC & Serial
                board_data = static_info.get("board-data", {})
                eth_mac = board_data.get("wtp-enet-mac", "")
                serial = board_data.get("wtp-serial-num", "")
                
                # Filter logic: Must have a Meraki Serial to be relevant?
                # The original logic didn't strictly enforce it IF the regex failed, but 
                # here we can be generous or strict. Original: validated starts with Q.
                
                if meraki_serial:
                     ap_data = {
                        'name': name,
                        'model': model,
                        'radio_mac': radio_mac,
                        'eth_mac': eth_mac,
                        'serial': serial,
                        'meraki_serial': meraki_serial
                    }
                     aps.append(ap_data)
                
            except AttributeError:
                continue
            except Exception as e:
                self.logger.warning(f"Error parsing AP item: {e}")
                continue
        
        self.logger.info(f"Found {len(aps)} Meraki-capable APs from WLC.")
        return aps
