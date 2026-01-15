import logging
import sys
from config import settings
from wlc_connector import WLCConnector
from meraki_connector import MerakiConnector

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("WLC-Meraki-Syncer")

import argparse
import time

def run_sync():
    logger.info("Starting WLC to Meraki Syncer...")
    if settings.dry_run:
        logger.warning("DRY RUN MODE ENABLED - No changes will be made to Meraki.")

    # 1. Fetch WLC APs
    try:
        wlc = WLCConnector(
            host=settings.wlc_host,
            username=settings.wlc_username,
            password=settings.wlc_password,
            port=settings.wlc_port
        )
        wlc_aps = wlc.get_aps()
        
        # Deduplicate just in case (based on Meraki Serial)
        # Using a dict to keep the last seen full object for a given serial
        unique_aps = {ap['meraki_serial']: ap for ap in wlc_aps}
        wlc_aps = list(unique_aps.values())
        
        logger.info(f"Retrieved {len(wlc_aps)} unique APs from WLC.")
        
    except Exception as e:
        logger.fatal(f"Failed to get data from WLC: {e}")
        # If running in loop, we might not want to exit the whole process, but for now strict failure is safer?
        # Re-raising to be caught by main loop if needed
        raise e

    # 2. Fetch Meraki Inventory
    try:
        meraki_conn = MerakiConnector(
            api_key=settings.meraki_api_key,
            org_id=settings.meraki_org_id,
            dry_run=settings.dry_run
        )
        inventory = meraki_conn.get_org_inventory()
        logger.info(f"Retrieved {len(inventory)} devices from Meraki Org Inventory.")
    
    except Exception as e:
        logger.fatal(f"Failed to get data from Meraki: {e}")
        raise e

    # 3. Calculate Deltas
    to_claim_to_org = []
    to_assign_to_network = []
    
    for ap in wlc_aps:
        serial = ap['meraki_serial']
        name = ap['name']
        model = ap['model']
        ap_serial = ap['serial']
        eth_mac = ap['eth_mac']
        
        # Check if exists in Org
        if serial not in inventory:
            logger.info(f"AP {name} ({model}, {serial}) [AP Serial: {ap_serial}, MAC: {eth_mac}] is MISSING from Meraki Org. Queuing for claim.")
            to_claim_to_org.append(serial)
            # If we claim it to Org, we also want to assign it to Network immediately
            to_assign_to_network.append(serial)
        else:
            # Exists in Org, check Network Status
            device_status = inventory[serial]
            current_network = device_status.get('networkId')
            
            if current_network is None:
                logger.info(f"AP {name} ({model}, {serial}) [AP Serial: {ap_serial}, MAC: {eth_mac}] is in Org but UNASSIGNED. Queuing for Network {settings.meraki_network_id}.")
                to_assign_to_network.append(serial)
            elif current_network != settings.meraki_network_id:
                logger.warning(f"AP {name} ({model}, {serial}) [AP Serial: {ap_serial}, MAC: {eth_mac}] is already assigned to DIFFERENT Network {current_network}. Skipping.")
            else:
                logger.debug(f"AP {name} ({model}, {serial}) [AP Serial: {ap_serial}, MAC: {eth_mac}] is already correctly assigned.")

    # 4. Execute Actions
    if to_claim_to_org:
        try:
            meraki_conn.claim_to_org(to_claim_to_org)
        except Exception as e:
            logger.error("Stopping due to error in Claim to Org.")
            raise e
    else:
        logger.info("No new devices to claim into Organization.")

    if to_assign_to_network:
        try:
            meraki_conn.assign_to_network(settings.meraki_network_id, to_assign_to_network)
        except Exception as e:
            logger.error("Error during Network Assignment. See logs.")
            # raises to be caught
            raise e
    else:
        logger.info("No devices to assign to Network.")

    logger.info("Sync Job Completed.")

def main():
    parser = argparse.ArgumentParser(description="Cisco WLC to Meraki Syncer")
    parser.add_argument('--loop', action='store_true', help="Run in a loop")
    parser.add_argument('--interval', type=int, default=86400, help="Interval in seconds for loop (default: 86400s / 24h)")
    
    args = parser.parse_args()
    
    if args.loop:
        logger.info(f"Running in LOOP mode. Interval: {args.interval} seconds.")
        while True:
            try:
                run_sync()
            except Exception as e:
                logger.error(f"An error occurred during sync: {e}")
            
            logger.info(f"Sleeping for {args.interval} seconds...")
            time.sleep(args.interval)
    else:
        # Run once
        try:
            run_sync()
        except Exception as e:
            sys.exit(1)

if __name__ == "__main__":
    main()
