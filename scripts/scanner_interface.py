import os
import sys

# --- Add the project root to the Python path ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from scripts.inventory_management import update_tool_status, get_tool_details

def simulate_qr_scan(qr_data):
    """
    Simulates the process of scanning a QR code and updating the inventory.

    Args:
        qr_data (str): The data obtained from the QR code (e.g., "Tool_ID: T001").
    """
    try:
        # Extract Tool_ID from the QR data
        if "Tool_ID: " in qr_data:
            tool_id = qr_data.split("Tool_ID: ")[1]
        else:
            print("Invalid QR code format.")
            return

        # Get current tool details
        tool_details = get_tool_details(tool_id)
        if not tool_details:
            print(f"Tool {tool_id} not found in inventory.")
            return

        # --- Simulate Check-in/Check-out ---
        is_checked_out = tool_details.get('Checked_Out_By', 'None') != 'None'

        if is_checked_out:
            # Tool is currently checked out, so check it in
            print(f"Tool {tool_id} is currently checked out by {tool_details['Checked_Out_By']}.")
            user_input = input("Do you want to check it in? (y/n): ").lower()
            if user_input == 'y':
                update_tool_status(tool_id, 'None')
                print(f"Tool {tool_id} has been successfully checked in.")
        else:
            # Tool is currently checked in, so check it out
            print(f"Tool {tool_id} is currently available.")
            engineer_name = input("Enter the name of the engineer checking it out: ")
            if engineer_name:
                update_tool_status(tool_id, engineer_name)
                print(f"Tool {tool_id} has been successfully checked out to {engineer_name}.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    # --- Example Usage ---
    print("--- QR Code Scanner Simulation ---")

    # Simulate scanning a QR code for Tool T003 (currently checked out)
    print("\n--- Simulating scan for a checked-out tool (T003) ---")
    simulate_qr_scan("Tool_ID: T003")

    # Simulate scanning a QR code for Tool T001 (currently available)
    print("\n--- Simulating scan for an available tool (T001) ---")
    simulate_qr_scan("Tool_ID: T001")
