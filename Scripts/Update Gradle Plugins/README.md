# Update Gradle Plugins

A script to update some Gradle plugins (Gradle Galaxy, Shadow, etc...) for all my projects

## Usage

This is intended to be used with a folder structure like this:
```plaintext
Parent Folder
├───Category 1
│   ├───Project 1
│   │   └───build.gradle.kts
│   └───Project 2
│       └───build.gradle.kts
└───Category 2
    └───Project 3
        └───build.gradle.kts
```

If you have a file structure matching the above, create a `config.json` file with the following structure and then run the script:
```json
{
  "parent_folder_path": "../../../..",

  "excluded_categories": [
    "Minecraft Modpacks",
    "Web Extensions",
    "Websites"
  ],
  
  "versions": {
    "gradle_galaxy": "1.3.1",
    "shadow": "8.3.2"
  }
}
```
