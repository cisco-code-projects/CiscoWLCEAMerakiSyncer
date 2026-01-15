from netmiko import ConnectHandler
import re
from typing import List, Dict
import logging

class WLCConnector:
    def __init__(self, host, username, password, port=22):
        self.device_config = {
            'device_type': 'cisco_ios', # cisco_xe is often compatible/same for netmiko purposes
            'host': host,
            'username': username,
            'password': password,
            'port': port,
        }
        self.logger = logging.getLogger(__name__)

    def get_aps(self) -> List[Dict[str, str]]:
        """
        Connects to the WLC and retrieves details of all APs.
        Returns a list of dictionaries with keys: 'name', 'model', 'radio_mac', 'eth_mac', 'serial', 'meraki_serial'.
        """
        try:
            self.logger.info(f"Connecting to WLC at {self.device_config['host']}...")
            with ConnectHandler(**self.device_config) as net_connect:
                # Disable paging to get full output
                net_connect.send_command("terminal length 0")
                
                self.logger.info("Executing 'show ap management-mode meraki capability summary'...")
                output = net_connect.send_command("show ap management-mode meraki capability summary")
                
                return self._parse_ap_inventory(output)
        except Exception as e:
            self.logger.error(f"Failed to retrieve APs from WLC: {e}")
            raise

    def _parse_ap_inventory(self, output: str) -> List[Dict[str, str]]:
        """
        Parses the output of 'show ap management-mode meraki capability summary'.
        Ref:
        AP Name                          AP Model             Radio MAC        MAC Address      AP Serial Number       Meraki Serial Number
        -----------------------------------------------------------------------------------------------------------------------------------
        AP-NAME                          CW9176I              aaaa.bbbb.cccc   dddd.eeee.ffff   FJC12345678            Q2AA-BB33-CC44
        """
        aps = []
        lines = output.splitlines()
        
        start_parsing = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect header row
            if "Meraki Serial Number" in line:
                start_parsing = True
                continue
            
            # Skip separator lines
            if "---" in line:
                continue
            
            if start_parsing:
                # Assuming 6 columns based on the header
                parts = line.split()
                if len(parts) >= 6:
                    ap_data = {
                        'name': parts[0],
                        'model': parts[1],
                        'radio_mac': parts[2],
                        'eth_mac': parts[3],
                        'serial': parts[4],
                        'meraki_serial': parts[5]
                    }
                    
                    # Basic validation for Meraki Serial (Start with Q, ~14 chars with dashes)
                    if ap_data['meraki_serial'].startswith("Q") and len(ap_data['meraki_serial']) >= 10:
                        aps.append(ap_data)
        
        self.logger.info(f"Found {len(aps)} APs from WLC.")
        return aps
