import pandas as pd
import os
import sys

# Add the project root to the Python path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from logs.audit import log_action

# --- Configuration ---
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
INVENTORY_FILE = os.path.join(DATA_DIR, 'inventory.csv')

# --- Ensure Data Directory Exists ---
os.makedirs(DATA_DIR, exist_ok=True)

def read_inventory():
    """
    Reads the inventory data from the CSV file.

    Returns:
        pandas.DataFrame: The inventory data.
    """
    if not os.path.exists(INVENTORY_FILE):
        # Create a default empty dataframe if the file doesn't exist
        df = pd.DataFrame(columns=[
            'Tool_ID', 'Box_Name', 'Location', 'Checked_Out_By',
            'Last_Calibration', 'Next_Maintenance', 'Usage_Frequency'
        ])
        df.to_csv(INVENTORY_FILE, index=False)
    return pd.read_csv(INVENTORY_FILE)

def save_inventory(df):
    """
    Saves the inventory data to the CSV file.

    Args:
        df (pandas.DataFrame): The inventory data to save.
    """
    df.to_csv(INVENTORY_FILE, index=False)

def update_tool_status(tool_id, checked_out_by, user):
    """
    Updates the check-in/check-out status of a tool.

    Args:
        tool_id (str): The ID of the tool to update.
        checked_out_by (str): The name of the engineer checking out the tool,
                              or 'None' if checking in.
        user (str): The user performing the action.

    Returns:
        bool: True if the tool was updated successfully, False otherwise.
    """
    df = read_inventory()
    if tool_id in df['Tool_ID'].values:
        old_status = df.loc[df['Tool_ID'] == tool_id, 'Checked_Out_By'].iloc[0]
        df.loc[df['Tool_ID'] == tool_id, 'Checked_Out_By'] = checked_out_by
        save_inventory(df)

        action_type = "tool_checkin" if checked_out_by == 'None' else "tool_checkout"
        details = {"old_status": old_status, "new_status": checked_out_by}
        log_action(action_type, user, tool_id, details)
        return True
    return False

def get_tool_details(tool_id):
    """
    Retrieves the details of a specific tool.

    Args:
        tool_id (str): The ID of the tool.

    Returns:
        dict: A dictionary containing the tool's details, or None if not found.
    """
    df = read_inventory()
    tool_details = df[df['Tool_ID'] == tool_id]
    if not tool_details.empty:
        return tool_details.to_dict('records')[0]
    return None

if __name__ == '__main__':
    # --- Example Usage ---
    print("--- Initial Inventory ---")
    inventory_df = read_inventory()
    print(inventory_df)

    # Example: Check out a tool
    print("\n--- Checking out Tool T001 ---")
    update_tool_status('T001', 'Glenn Bundy', 'test_user')
    inventory_df = read_inventory()
    print(inventory_df)

    # Example: Check in a tool
    print("\n--- Checking in Tool T001 ---")
    update_tool_status('T001', 'None', 'test_user')
    inventory_df = read_inventory()
    print(inventory_df)

    # Example: Get tool details
    print("\n--- Details for Tool T003 ---")
    tool_info = get_tool_details('T003')
    if tool_info:
        print(tool_info)