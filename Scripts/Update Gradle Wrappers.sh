# Script used to update Gradle Wrapper in all projects that uses it

# Colors used for echo
RESET='\033[0m'
RED='\033[0;31m'
L_RED='\033[1;91m'
YELLOW='\033[0;33m'
L_YELLOW='\033[1;93m'

# Array of excluded directories (just checks the name of the directory, not the full/relative path)
excluded=(".stfolder" "Minecraft Modpacks" "Python" "Web Extensions" "Websites")
is_excluded() {
  for i in "${excluded[@]}"; do
    if [[ "$1" == "$i/" ]]; then
      return 0
    fi
  done
  return 1
}

# Navigate to root GitHub directory (currently in GitHub/Miscellaneous/tools/Scripts
cd ../../..

# Loop through all categories
total_categories=0
total_projects=0
updated_categories=0
updated_projects=0
for category in */; do
  cd "$category" || continue
  total_categories=$((total_categories + 1))

  # Check if the category is in the excluded list
  if is_excluded "$category"; then
    skip=0
  else
    skip=1
    updated_categories=$((updated_categories + 1))
  fi

  # Loop through all projects
  for project in */; do
    total_projects=$((total_projects + 1))

    # Skip if parent was excluded
    if [ "$skip" == 0 ]; then
      echo -e "${RED}Skipping ${L_RED}$project${RED} because the parent category (${L_RED}$category${RED}) is in the excluded list\n${RESET}"
      continue
    fi

    # Check if the directory is in the excluded list
    if is_excluded "$project"; then
      echo -e "${RED}Skipping ${L_RED}$project${RED} because it's in the excluded list\n${RESET}"
      continue
    fi

    # Check if the directory contains a gradle/wrapper directory
    if [ ! -d "$project/gradle/wrapper" ]; then
      echo -e "${RED}Skipping ${L_RED}$project${RED} because it doesn't contain a gradle/wrapper directory\n${RESET}"
      continue
    fi

    # Update the Gradle Wrapper in the directory
    echo -e "${YELLOW}Updating Gradle Wrapper in ${L_YELLOW}$project${YELLOW}...${RESET}"
    cd "$project" || continue
    gradle wrapper
    updated_projects=$((updated_projects + 1))
    echo ""
    cd ..
  done

  cd ..
done

echo -e "${YELLOW}Updated Gradle Wrapper in ${L_YELLOW}${updated_projects}/${total_projects} projects${YELLOW} in ${L_YELLOW}${updated_categories}/${total_categories} categories\n${RED}"

# Keep the terminal window open
read -n 1 -s -r -p "Press any key to exit..."
