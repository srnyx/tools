# Script used to update Gradle dependencies (Gradle Galaxy and Shadow) in all projects that use them

import os
import re

# Constants
GRADLE_GALAXY_VERSION = "1.3.1"
SHADOW_VERSION = "8.3.1"
GITHUB_FOLDER_PATH = "../../.."
EXCLUDED_CATEGORIES = ["Minecraft Modpacks", "Web Extensions", "Websites"]

# Colors
HEADER = '\033[95m'
BLUE = '\033[94m'
GREEN = '\033[92m'
WARNING = '\033[93m'
RESET = '\033[0m'
BOLD = '\033[1m'

# Iterate over all categories and projects
print(f"{HEADER}Starting to update Gradle plugins for all projects{RESET}")
with os.scandir(GITHUB_FOLDER_PATH) as categories:
    for category in categories:
        # Check if file is a directory
        if not category.is_dir():
            continue

        # Check if category is excluded
        if category.name in EXCLUDED_CATEGORIES:
            print(f"{WARNING}{category.name}{RESET} Skipping category")
            continue

        print(f"{BLUE}{BOLD}{category.name}{RESET} Found category")
        category_path = f"{GITHUB_FOLDER_PATH}/{category.name}"
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

                # Update Gradle Galaxy
                has_gradle_galaxy = 'id("xyz.srnyx.gradle-galaxy")' in content
                if has_gradle_galaxy:
                    print(f"{BLUE}{log_name}{RESET} Updating Gradle Galaxy")
                    content = re.sub(r'id\("xyz\.srnyx\.gradle-galaxy"\) version "\d+\.\d+\.\d+"', f'id("xyz.srnyx.gradle-galaxy") version "{GRADLE_GALAXY_VERSION}"', content)

                # Update Shadow
                has_old_shadow = 'id("com.github.johnrengelman.shadow")' in content
                has_shadow = has_old_shadow or 'id("com.gradleup.shadow")' in content
                if has_shadow:
                    if has_old_shadow:
                        print(f"{BLUE}{log_name}{RESET} Updating Shadow (old)")
                        pattern = r'id\("com\.github\.johnrengelman\.shadow"\) version "\d+\.\d+\.\d+"'
                    else:
                        print(f"{BLUE}{log_name}{RESET} Updating Shadow")
                        pattern = r'id\("com\.gradleup\.shadow"\) version "\d+\.\d+\.\d+"'

                    content = re.sub(pattern, f'id("com.gradleup.shadow") version "{SHADOW_VERSION}"', content)

                # Write
                if has_gradle_galaxy or has_shadow:
                    with open(file_path, "w") as file:
                        file.write(content)

                    print(f"{GREEN}{log_name}{RESET} Successfully updated Gradle plugins")

print(f"{HEADER}Finished updating Gradle plugins for all projects{RESET}")
