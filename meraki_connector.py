import meraki
import logging
from typing import List, Dict, Set

class MerakiConnector:
    def __init__(self, api_key: str, org_id: str, dry_run: bool = False):
        self.dashboard = meraki.DashboardAPI(
            api_key=api_key,
            suppress_logging=True,
            print_console=False
        )
        self.org_id = org_id
        self.dry_run = dry_run
        self.logger = logging.getLogger(__name__)

    def get_org_inventory(self) -> Dict[str, dict]:
        """
        Returns a dictionary of all devices in the organization, keyed by Serial Number.
        """
        self.logger.info(f"Fetching inventory for Org {self.org_id}...")
        devices = self.dashboard.organizations.getOrganizationInventoryDevices(self.org_id, total_pages='all')
        inventory = {d['serial']: d for d in devices}
        return inventory

    def claim_to_org(self, serials: List[str]):
        """
        Claims a list of serials into the Organization Inventory.
        """
        if not serials:
            return

        self.logger.info(f"Claiming {len(serials)} serials to Organization {self.org_id}: {serials}")
        
        if self.dry_run:
            self.logger.info("[DRY RUN] Skipping actual claim call.")
            return

        try:
            self.dashboard.organizations.claimIntoOrganizationInventory(
                self.org_id, 
                serials=serials
            )
            self.logger.info("Claim to Org successful.")
        except meraki.APIError as e:
            self.logger.error(f"Error claiming serials to Org: {e}")
            # Continue execution to try network assignment for valid ones? 
            # Usually strict fail is better, but maybe partial success is possible?
            raise

    def assign_to_network(self, network_id: str, serials: List[str]):
        """
        Assigns (claims) devices from Org Inventory into a specific Network.
        """
        if not serials:
            return

        self.logger.info(f"Assigning {len(serials)} serials to Network {network_id}: {serials}")

        if self.dry_run:
            self.logger.info("[DRY RUN] Skipping actual network assignment.")
            return

        try:
            self.dashboard.networks.claimNetworkDevices(
                network_id, 
                serials=serials
            )
            self.logger.info("Assignment to Network successful.")
        except meraki.APIError as e:
            self.logger.error(f"Error assigning serials to network: {e}")
            raise
