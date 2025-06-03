import pandas as pd
import os
import segno
import json
from consts import *

def generate_test_database(output_file="test_db.xlsx"):
    """
    Generates a test Excel database matching the provided test_db.xlsx for the Logistic.01 application.
    """
    # --- Data Sheet ---
    data_columns = [
        ID_COLUMN,
        CODE_COLUMN,
        TYPE_COLUMN,
        DESC_COLUMN,
        IDENT_COLUMN,
        LOCATION_COLUMN,
        URL_DATASHEET_COLUMN,
        URL_ORDER_COLUMN,
        STORED_AMOUNT_COLUMN,
    ]
    
    data_rows = [
        [1, "1234567890", "Widerstand", "220Ω", "RES-220-05", "6351eeee-81eb-44d4-9132-b739adbba2bb", "https://example.com/datasheet1", "https://example.com/order1", 30],
        [2, "0987654321", "Kondensator", "100µF", "CAP-100-25V", "6351eeee-81eb-44d4-9132-b739adbba2bb", "https://example.com/datasheet2", "https://example.com/order2", 20],
        [3, "1122334455", "LED", "Rot 5mm", "LED-R5-2.1V", "6351eeee-81eb-44d4-9132-b739adbba2bb", "https://example.com/datasheet3", "https://example.com/order3", 30],
        [4, "6119490246", "Schraube", "M4 x 20", "test1", "6351eeee-81eb-44d4-9132-b739adbba2bb", "https://example.com/datasheet4", "https://example.com/order4", 10],
    ]
    
    data_df = pd.DataFrame(data_rows, columns=data_columns)
    
    # --- Locations Sheet ---
    locations = [
        {"Name": "Area.01", "UUID": "f7428ce1-7916-4771-bad9-9d9efa5e27da", "Parent": None},
        {"Name": "S1", "UUID": "3bcf7e40-c5e5-4a15-8ef2-77a750bb084e", "Parent": "f7428ce1-7916-4771-bad9-9d9efa5e27da"},
        {"Name": "Schublade 1", "UUID": "d32c8f6c-9c58-40d6-97b7-94659dc9f921", "Parent": "3bcf7e40-c5e5-4a15-8ef2-77a750bb084e"},
        {"Name": "Regal 1", "UUID": "6351eeee-81eb-44d4-9132-b739adbba2bb", "Parent": "f7428ce1-7916-4771-bad9-9d9efa5e27da"},
        {"Name": "Schublade 2", "UUID": "61847694-85ec-4457-b1d3-350d60655136", "Parent": "6351eeee-81eb-44d4-9132-b739adbba2bb"},
    ]
    
    locations_df = pd.DataFrame(locations, columns=[LOCATION_NAME_COLUMN, LOCATION_ID_COLUMN, LOCATION_PARENT_COLUMN])
    
    # --- Info Sheet ---
    info_df = pd.DataFrame([[INFO_VERSION_KEY, REQUIRED_DB_VERSION]], columns=[INFO_KEY_COLUMN, INFO_VALUE_COLUMN])
    
    # --- Save to Excel ---
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        data_df.to_excel(writer, sheet_name=DATA_SHEET, index=False)
        locations_df.to_excel(writer, sheet_name=LOCATION_SHEET, index=False)
        info_df.to_excel(writer, sheet_name=INFO_SHEET, index=False)
    
    print(f"Test database generated: {output_file}")

def generate_test_qr_codes(output_dir="test_qrcodes"):
    """
    Generates QR codes for item codes and mode/multiplier codes.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Item codes from Data Sheet
    item_codes = ["1234567890", "0987654321", "1122334455", "6119490246"]
    for code in item_codes:
        qr = segno.make(code, micro=False)
        qr.save(
            os.path.join(output_dir, f"{code}.png"),
            scale=10,
            border=2,
            dark="black",
            light="white"
        )
    
    # Mode and multiplier codes
    multipliers = {
        "mult1": "mult1.png",
        "mult10": "mult10.png",
        "mult100": "mult100.png"
    }
    modes = {
        "addmode": "addmode.png",
        "removemode": "removemode.png",
        "exitmode": "exitmode.png"
    }
    
    for code, filename in multipliers.items():
        qr = segno.make(code, micro=False)
        qr.save(
            os.path.join(output_dir, filename),
            scale=10,
            border=2,
            dark="black",
            light="white"
        )
    
    for mode, filename in modes.items():
        qr = segno.make(mode, micro=False)
        qr.save(
            os.path.join(output_dir, filename),
            scale=10,
            border=2,
            dark="black",
            light="white"
        )
    
    print(f"Test QR codes generated in {output_dir}")

def generate_test_settings(output_file="settings.json"):
    """
    Generates a settings.json file pointing to the test database.
    """
    settings = {
        "filePath": "test_db.xlsx",
        "language": "German",
        "unitSystem": "Metrisch",
        "persistScannedIDs": True
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)
    
    print(f"Test settings file generated: {output_file}")

if __name__ == "__main__":
    generate_test_database()
    generate_test_qr_codes()
    generate_test_settings()