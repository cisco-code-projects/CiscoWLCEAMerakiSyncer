# Cisco WLC to Meraki Syncer

This tool synchronizes Access Points from a Cisco 9800 WLC to the Meraki Dashboard.
It is designed to check for APs connected to the WLC and ensure they are claimed in your Meraki Organization and assigned to a specific Network (e.g., for verification/licensing compliance).  This is specifically for EA customers that have both on-premise and Meraki licenses and must manage the claim process in Dashboard.

## Features
*   **WLC Connector**: Connects via SSH (Netmiko) and parses `show ap inventory`.
*   **Meraki Connector**: Checks Organization Inventory using the Meraki Dashboard API.
*   **Sync Logic**: 
    *   Claims new APs to the Organization.
    *   Assigns unassigned APs to the target Network.
    *   Skips APs that are already assigned to other networks to avoid conflicts.
*   **Dry Run**: Supports a Dry Run mode to see what would happen without making changes.

## Prerequisites
*   Docker
*   Cisco 9800 WLC Credentials (SSH)
*   Meraki API Key, Org ID, and Network ID

## Setup

1.  Clone this repository.
2.  Create a `.env` file based on `.env.example`:
    ```bash
    cp .env.example .env
    ```
3.  Edit `.env` with your actual credentials.

## Running with Docker

Build the image:
```bash
docker build -t wlc-meraki-syncer .
```

Run the container:
```bash
docker run --env-file .env wlc-meraki-syncer
```

## Helper Utilities

### Finding Meraki IDs
If you don't know your Organization or Network IDs, you can use the included helper script.

**Using Docker (easiest if configured):**
```bash
# Assumes you have already set MERAKI_API_KEY in .env
docker run --rm --env-file .env --entrypoint python wlc-meraki-syncer get_meraki_ids.py
```

**Using Python locally:**
```bash
export MERAKI_API_KEY=your_key
python get_meraki_ids.py
```

## Running Locally (Python)

```bash
pip install -r requirements.txt
python main.py
```
