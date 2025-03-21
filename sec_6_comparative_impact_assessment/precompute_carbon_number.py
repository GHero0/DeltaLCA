import json

# Unit: gram CO2 eq. / piece
resistor_carbon_database = {
    "0201"  : 0.01,
    "0402"  : 0.04,
    "0603"  : 0.12,
    "0805"  : 0.36,
    "1206"  : 0.6,
}

capacitor_carbon_database = {
    "0201"  : 0.03589,
    "0402"  : 0.1455,
    "0603"  : 0.6111,
    "0805"  : 1.067,
}

inductor_carbon_database = {
    "0201"  : 0.02231,
    "0402"  : 0.0776,
    "0603"  : 0.3298,
    "0805"  : 1.358,
}

# Unit: gram CO2 eq. / mm^2 / layer / 1mm thickness
fr4_carbon_database = 0.006125

def get_nonIC_carbon_footprint(data):
    # Calculate total carbon emissions for components
    total_carbon_emission = 0.0

    for part, sizes in data.items():
        if part in ["resistor", "capacitor", "inductor"]:
            for size, count in sizes.items():
                if size in eval(f"{part}_carbon_database"):
                    part_carbon_emission = eval(f"{part}_carbon_database[size]") * count
                    total_carbon_emission += part_carbon_emission
                    print(f"{part} {size} {count}: {part_carbon_emission} gram CO2 eq.")
            print(f"total carbon emission after {part}: {total_carbon_emission} gram CO2 eq.")

    # Calculate carbon emissions for the board
    board_size = data["board"]["Size"]
    board_area = board_size["Length"] * board_size["Width"]
    board_layers = data["board"]["Number_of_Layers"]
    print(f"board area: {board_area} mm^2, board layers: {board_layers}")
    board_carbon_emission = fr4_carbon_database * board_area * board_layers
    total_carbon_emission += board_carbon_emission

    print(f"Total Carbon Emission: {total_carbon_emission} gram CO2 eq.")
    return board_carbon_emission, total_carbon_emission - board_carbon_emission

if __name__ == "__main__":
    # Read the input JSON file
    with open("PCB_summary_Leonardo_Rev3d.json", "r") as json_file:
        data = json.load(json_file)
    get_nonIC_carbon_footprint(data)