def parse_position_data(filename):
    """
    Parses a text file to extract numerical values from lines containing
    'Ypos', 'Zpos', and 'Xpos' and stores them in separate lists.

    Args:
        filename (str): The name of the text file to parse.

    Returns:
        tuple: A tuple containing three lists:
            - y_positions (list of int): List of Ypos values.
            - z_positions (list of int): List of Zpos values.
            - x_positions (list of int): List of Xpos values.
            Returns empty lists if file not found or lines not found
    """
    y_positions = []
    z_positions = []
    x_positions = []

    try:
        with open(filename, 'r') as file:
            for line in file:
                line = line.strip()  # Remove leading/trailing whitespace
                nline = line.replace("#","").split()
                if "Ypos" in line:
                    try:
                        y_positions.append(float(nline[1]))
                    except IndexError:
                         print(f"Skipping line due to formatting issue: {line}")
                    except ValueError:
                         print(f"Skipping line due to non-numeric value: {line}")
                elif "Zpos" in line:
                    try:
                        z_positions.append(float(nline[1]))
                    except IndexError:
                         print(f"Skipping line due to formatting issue: {line}")
                    except ValueError:
                         print(f"Skipping line due to non-numeric value: {line}")
                elif "Xpos" in line:
                    try:
                        x_positions.append(float(nline[1]))
                    except IndexError:
                         print(f"Skipping line due to formatting issue: {line}")
                    except ValueError:
                         print(f"Skipping line due to non-numeric value: {line}")
    except FileNotFoundError:
        print(f"Error: File not found - {filename}")
        return [], [], []  # Return empty lists in case of error
    y_pos = set(y_positions)
    z_pos = set(z_positions)
    x_pos = set(x_positions)
    minx, maxx =min(x_pos), max(x_pos)
    miny, maxy =min(y_pos), max(y_pos)
    minz, maxz =min(z_pos), max(z_pos)
    return (minx, maxx), (miny, maxy),  (minz, maxz)

if __name__ == "__main__":
    # Example usage:
    filename = "out.txt"  # Replace with your actual file name
    x_pos, y_pos, z_pos = parse_position_data(filename)

    print("X Positions:", x_pos)
    print("Y Positions:", y_pos)
    print("Z Positions:", z_pos)
