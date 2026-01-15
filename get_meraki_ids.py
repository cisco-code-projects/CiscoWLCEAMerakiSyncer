import meraki
import os
import sys

# Try to load env but don't crash if missing, as user might pass via env var directly
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def main():
    api_key = os.getenv("MERAKI_API_KEY")
    if not api_key:
        print("Error: MERAKI_API_KEY environment variable is not set.")
        print("Please set it in your .env file or pass it directly.")
        sys.exit(1)

    dashboard = meraki.DashboardAPI(api_key=api_key, suppress_logging=True, print_console=False)

    print("\nfetching Organizations...")
    try:
        orgs = dashboard.organizations.getOrganizations()
    except Exception as e:
        print(f"Failed to fetch organizations: {e}")
        return

    if not orgs:
        print("No Organizations found for this API Key.")
        return

    print(f"\nFound {len(orgs)} Organization(s):")
    print("-" * 60)
    print(f"{'ID':<20} | {'Name'}")
    print("-" * 60)
    for org in orgs:
        print(f"{org['id']:<20} | {org['name']}")
    print("-" * 60)

    for org in orgs:
        org_id = org['id']
        org_name = org['name']
        print(f"\nFetching Networks for Org: {org_name} ({org_id})...")
        
        try:
            networks = dashboard.organizations.getOrganizationNetworks(org_id, total_pages='all')
        except Exception as e:
            print(f"  Failed to fetch networks: {e}")
            continue

        if not networks:
            print("  No networks found.")
        else:
            print(f"  Found {len(networks)} Network(s):")
            print(f"  {'-'*56}")
            print(f"  {'ID':<20} | {'Name'}")
            print(f"  {'-'*56}")
            for net in networks:
                print(f"  {net['id']:<20} | {net['name']}")
            print(f"  {'-'*56}")

    print("\nDone. Copy the relevant IDs to your .env file.")

if __name__ == "__main__":
    main()
