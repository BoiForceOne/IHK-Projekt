import sys
import segno
import os

def generate_multiplier_qr(output_dir="multiplier_qrcodes"):
    multipliers = {
        "mult1": "01-mult1x.png",
        "mult10": "02-mult10x.png",
        "mult100": "03-mult100x.png"
    }
    
    # Create output directory if needed
    os.makedirs(output_dir, exist_ok=True)
    
    for code, filename in multipliers.items():
        qr = segno.make(code, micro=False)
        full_path = os.path.join(output_dir, filename)
        qr.save(
            full_path,
            scale=10,
            border=2,
            dark="black",
            light="white"
        )
    print(f"Generated multiplier QR codes in {output_dir}")

def generate_mode_qr(output_dir="mode_qrcodes"):
    """Generate all mode QR codes"""
    modes = {
        "addmode": "addmode.png",
        "removemode": "removemode.png",
        "exitmode": "exitmode.png"
    }
    
    # Create output directory if needed
    os.makedirs(output_dir, exist_ok=True)
    
    for mode, filename in modes.items():
        qr = segno.make(mode, micro=False)
        full_path = os.path.join(output_dir, filename)
        qr.save(
            full_path,
            scale=10,
            border=2,
            light="white",
            dark="black",
        )
    print(f"Generated mode QR codes in {output_dir}")

def generate_data_matrix(data: str):
    """
    Generates a Data Matrix code

    param data: string to be encoded
    return: Data Matrix code
    """
    data_matrix = segno.make(data, micro=True)
    # code for saving: data_matrix.save(filename, scale=10)
    return data_matrix

if __name__ == "__main__":
    generate_multiplier_qr()
    generate_mode_qr()


"""    name = input("Namen des QR-Codes eingeben: ")
    match len(sys.argv):
        case 1:
            data = input("Zu entcodenden Text eingeben: ")
            filehandle = generate_data_matrix(data)
            filehandle.save(name, scale=10)
            print(f"QR-Code für '{data}' gespeichert als {name}")
        case 2:
            filehandle = generate_data_matrix(sys.argv[1])
            filehandle.save(name, scale=10)
            print(f"QR-Code für '{sys.argv[1]}' gespeichert als {name}")
        case _:
            print("Ungültige Anzahl an Argumenten")
"""