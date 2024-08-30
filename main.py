#!/usr/bin/env python3

import re
import sys
import os
import subprocess
import logging

#modules
from read_config_file import read_config_file
from write_config_file import write_config_file
from add_package import add_package
from remove_package import remove_package
from search_packages import search_packages
from list_packages import list_packages
from rebuild_nixos import rebuild_nixos
from update_nixos import update_nixos
from create_snapshot import create_snapshot
from restore_config import restore_config
from create_backup import create_backup
from print_help import print_help
from add_category_package import add_package_to_category
from remove_category_package import remove_package_from_category
from category_imports import add_category_import

def execute_bash_script(script_path, file_name):
    try:
        # Execute the bash command and capture the output
        result = subprocess.run(["bash", script_path, file_name], capture_output=True, text=True, check=True)
        # Return the output
        return result.stdout
    except subprocess.CalledProcessError as e:
        # If the command fails, return the error
        return f"An error occurred: {e.stderr}"

def list_categories():
    if len(sys.argv) < 3:
        print("Usage: main.py list-categories <category-file>")
        return
    
    file_name = sys.argv[2]

    # Construct the full path to the script
    script_path = os.path.expanduser("~/scripts/resources/category-finder")

    if not os.path.exists(script_path):
        print(f"Script not found: {script_path}")
        return

    # Execute the bash script with the given arguments
    output = execute_bash_script(script_path, file_name)

    # Display the output to the user
    print(output)

def main():
    if "--help" in sys.argv:
        print_help()
        exit(0)

    if len(sys.argv) < 2:
        print("Usage: nixpkg.py <action> [<package/query>]")
        exit(1)

    action = sys.argv[1]
    
    # Handle category-based actions
    if "--category" in sys.argv:
        category_index = sys.argv.index("--category")
        category_name = sys.argv[category_index + 1]
        packages = sys.argv[category_index + 2:]

        if action == "install":
            add_package_to_category(category_name, packages)
            print(f"Packages installed in category '{category_name}': {', '.join(packages)}")
            rebuild_nixos()
        elif action == "remove":
            removed_packages = remove_package_from_category(category_name, packages)
            if removed_packages:
                print(f"Packages removed from category '{category_name}': {', '.join(removed_packages)}")
                rebuild_nixos()
            else:
                print(f"No packages removed from category '{category_name}'")
        else:
            print(f"Unknown action with category: {action}")
            print_help()
            exit(1)

    # Handle non-category-based actions
    else:
        config_file_path = "/etc/nixos/apps.nix"
        config_contents = read_config_file(config_file_path)

        package_list_match = re.search(r'environment\.systemPackages\s*=\s*with\s+pkgs;\s*\[(.*?)\];', config_contents, re.DOTALL)
        if package_list_match:
            package_list = package_list_match.group(1).strip()
            packages = package_list.split()
        else:
            logging.error("Package list not found in the apps.nix configuration file.")
            exit(1)

        if action == "install":
            if len(sys.argv) < 3:
                print("Usage: nixpkg.py install <package name(s)>")
                exit(1)
            packages_to_install = sys.argv[2:]
            for package in packages_to_install:
                print(add_package(packages, package))
            print(f"Packages installed: {', '.join(packages_to_install)}")
            rebuild_nixos()
        elif action == "remove":
            if len(sys.argv) < 3:
                print("Usage: nixpkg.py remove <package name(s)>")
                exit(1)
            packages_to_remove = sys.argv[2:]
            for package in packages_to_remove:
                print(remove_package(packages, package))
            print(f"Packages removed: {', '.join(packages_to_remove)}")
            rebuild_nixos()
        elif action == "search":
            if len(sys.argv) != 3:
                print("Usage: nixpkg.py search <query>")
                exit(1)
            search_packages(sys.argv[2])
        elif action == "list":
            list_packages()
            return
        elif action == "list-categories":
            # Call the list_categories function
            list_categories()
            return
        elif action == "update":
            create_backup(config_file_path)
            update_nixos()
        elif action == "snapshot":
            snapshot_path = create_snapshot(config_contents)
            print(f"Snapshot created: {snapshot_path}")
        elif action == "restore":
            if len(sys.argv) != 3:
                print("Usage: nixpkg.py restore <path>")
                exit(1)
            restore_config(sys.argv[2])
        elif action == "add-category":
            if len(sys.argv) != 3:
                print("Usage: nixpkg.py add-category <category-name>")
                exit(1)
            category_name = sys.argv[2]
            add_category_import(category_name)
            rebuild_nixos()
        else:
            print(f"Unknown action: {action}")
            print_help()
            exit(1)

        new_package_list = "\n  ".join(packages)
        new_config_contents = re.sub(r'environment\.systemPackages\s*=\s*with\s+pkgs;\s*\[.*?\];', f'environment.systemPackages = with pkgs; [\n  {new_package_list}\n];', config_contents, flags=re.DOTALL)
        write_config_file(config_file_path, new_config_contents)

if __name__ == "__main__":
    main()
