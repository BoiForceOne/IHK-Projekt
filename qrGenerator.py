import sys
import segno

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
    name = input("Namen des QR-Codes eingeben: ")
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
