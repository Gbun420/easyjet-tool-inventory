import pandas as pd
import qrcode
import os
from PIL import Image

# --- Configuration ---
# Get the absolute path to the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QR_CODE_DIR = os.path.join(PROJECT_ROOT, 'qr_codes')
INVENTORY_FILE = os.path.join(PROJECT_ROOT, 'data', 'inventory.csv')

# --- Ensure QR Code Directory Exists ---
os.makedirs(QR_CODE_DIR, exist_ok=True)

def generate_qr_codes():
    """
    Generates QR codes for each tool in the inventory and saves them as PNG files.
    The QR code will contain the Tool_ID.
    """
    try:
        # Read inventory data
        inventory_df = pd.read_csv(INVENTORY_FILE)

        # Generate a QR code for each tool
        for index, row in inventory_df.iterrows():
            tool_id = row['Tool_ID']
            qr_data = f"Tool_ID: {tool_id}"

            # Create QR code instance
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)

            # Create an image from the QR Code instance
            img = qr.make_image(fill_color="black", back_color="white")

            # Save the image
            qr_image_path = os.path.join(QR_CODE_DIR, f"{tool_id}.png")
            img.save(qr_image_path)
            print(f"Successfully generated QR code for {tool_id} at {qr_image_path}")

    except FileNotFoundError:
        print(f"Error: The inventory file was not found at {INVENTORY_FILE}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    print("--- Starting QR Code Generation ---")
    generate_qr_codes()
    print("--- QR Code Generation Complete ---")
