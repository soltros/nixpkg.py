import os

def add_category_import(category_name):
    """Adds a category import to /etc/nixos/configuration.nix"""
    config_file = "/etc/nixos/configuration.nix"
    category_import = f"./categories/{category_name}.nix"

    with open(config_file, 'r') as file:
        lines = file.readlines()

    # Check if the import already exists
    if category_import in [line.strip() for line in lines]:
        print(f"Category import already exists: {category_import}")
        return

    # Add the import statement
    lines.insert(1, f"import {category_import};\n")

    with open(config_file, 'w') as file:
        file.writelines(lines)

    print(f"Added category import: {category_import}")
