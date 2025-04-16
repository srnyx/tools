# Script used to update Gradle dependencies (Gradle Galaxy and Shadow) in all projects that use them

import os
import re
import json
import requests

# Colors
HEADER = '\033[95m'
BLUE = '\033[94m'
GREEN = '\033[92m'
WARNING = '\033[93m'
RESET = '\033[0m'
BOLD = '\033[1m'

# Get config values
with open("config.json", "r") as file:
    config = json.load(file)
    parent_folder_path = config["parent_folder_path"]
    excluded_categories = config["excluded_categories"]
    plugins = config["plugins"]

# Iterate over all categories and projects
print(f"{HEADER}Starting to update Gradle plugins for all projects{RESET}")
with os.scandir(parent_folder_path) as categories:
    for category in categories:
        # Check if file is a directory
        if not category.is_dir():
            continue

        # Check if category is excluded
        if category.name in excluded_categories:
            print(f"{WARNING}{category.name}{RESET} Skipping category")
            continue

        print(f"{BLUE}{BOLD}{category.name}{RESET} Found category")
        category_path = f"{parent_folder_path}/{category.name}"
        with os.scandir(category_path) as projects:
            for project in projects:
                # Check if file is a directory
                if not project.is_dir():
                    continue

                log_name = f"{category.name}/{project.name}"
                print(f"{BLUE}{log_name}{RESET} Found project")

                # Check if build.gradle.kts file exists
                file_path = f"{category_path}/{project.name}/build.gradle.kts"
                if not os.path.exists(file_path):
                    continue
                print(f"{BLUE}{log_name}{RESET} Found build.gradle.kts")

                # Read
                with open(file_path, "r") as file:
                    content = file.read()
                original_content = content

                # Store versions
                versions = plugins

                # Update plugins
                for plugin, version in plugins.items():
                    # If shadow, do special handling
                    if plugin == "com.gradleup.shadow":
                        if 'id("com.github.johnrengelman.shadow")' in content:
                            content = content.replace('id("com.github.johnrengelman.shadow")', 'id("com.gradleup.shadow")')
                        elif 'id("io.github.goooler.shadow")' in content:
                            content = content.replace('id("io.github.goooler.shadow")', 'id("com.gradleup.shadow")')

                    # Check if plugin is in content
                    if f'id("{plugin}")' not in content:
                        continue

                    # Get stored version
                    version = versions.get(plugin)

                    # Retrieve latest stable version if auto
                    if version == "auto":
                        print(f"{BLUE}{log_name}{RESET} Retrieving latest version for {plugin}")
                        try:
                            # Get all versions
                            plugin_versions = []
                            print(f"https://plugins.gradle.org/m2/{plugin.replace('.', '/')}")
                            for link in re.findall(r'href="([^"]+)"', requests.get(f"https://plugins.gradle.org/m2/{plugin.replace('.', '/')}").text):
                                if re.match(r'^\d+\.\d+\.\d+/', link):
                                    plugin_versions.append(link[:-1])
                        except requests.RequestException as e:
                            print(f"{WARNING}{log_name}{RESET} Failed to retrieve latest version for {plugin}: {e}")
                            continue

                        # Get latest version
                        print(plugin_versions)
                        version = max(plugin_versions, key=lambda x: list(map(int, x.split('.'))))
                        if version is None:
                            print(f"{WARNING}{log_name}{RESET} No latest version found for {plugin}")
                            continue
                        versions[plugin] = version

                    # Cancel if version is valid
                    if not re.match(r'^\d+\.\d+\.\d+$', version):
                        print(f"{WARNING}{log_name}{RESET} Invalid version '{version}' for {plugin}")
                        continue

                    # Check if version is already up to date
                    if f'id("{plugin}") version "{version}"' in content:
                        print(f"{BLUE}{log_name}{RESET} {plugin} is already up to date")
                        continue

                    # Update version
                    print(f"{BLUE}{log_name}{RESET} Updating {plugin} to version {version}")
                    content = re.sub(r'id\("' + re.escape(plugin) + r'"\) version "\d+\.\d+\.\d+"', f'id("{plugin}") version "{version}"', content)

                # Write
                if content != original_content:
                    with open(file_path, "w") as file:
                        file.write(content)

                    print(f"{GREEN}{log_name}{RESET} Successfully updated Gradle plugins")

print(f"{HEADER}Finished updating Gradle plugins for all projects{RESET}")
