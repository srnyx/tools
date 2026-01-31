import json
import requests


# URLs
modrinth_version_url = "https://api.modrinth.com/v2/project/{project_id}/version?include_changelog=false"
modrinth_update_url = "https://api.modrinth.com/v2/version/{version_id}"

hangar_jwt_url = "https://hangar.papermc.io/api/v1/authenticate?apiKey={api_key}"
hangar_latest_url = "https://hangar.papermc.io/api/v1/projects/{project_id}/latestrelease"
hangar_version_url = "https://hangar.papermc.io/api/v1/projects/{project_id}/versions/{latest_version_name}"
hangar_project_url = "https://hangar.papermc.io/api/v1/projects/{project_id}"
hangar_update_url = "https://hangar.papermc.io/api/internal/versions/version/{project_id}/{version_id}/savePlatformVersions"

bukkit_versions_url = "https://minecraft.curseforge.com/api/game/versions"
bukkit_files_url = "https://api.curseforge.com/v1/mods/{project_id}/files"
bukkit_update_url = "https://minecraft.curseforge.com/api/projects/{project_id}/update-file"
bukkit_slug_url = "https://api.curseforge.com/v1/mods/{project_id}"

# Misc
hangar_jwt = None
invalid_hangar_versions = ["1.8.9", "1.7.x", "1.6.x", "1.5.x", "1.4.x", "1.3.x", "1.2.x", "1.1.x", "1.0.x"]
bukkit_versions = None
bukkit_major_only = ['1.8', '1.9', '1.10', '1.11', '1.12', '1.13', '1.14', '1.15', '1.16', '1.17']

# Colors
red = "\033[31m"
green = "\033[32m"
yellow = "\033[33m"
blue = "\033[34m"
reset = "\033[0m"


# Get config values
with open("config.json", "r") as file:
    config = json.load(file)
    user_agent = config["user-agent"]
    tokens = config["tokens"]
    tokens_modrinth = tokens["modrinth"]
    tokens_hangar = tokens["hangar"]
    tokens_bukkit = tokens["bukkit"]
    tokens_bukkit_upload = tokens_bukkit["upload-api"]
    tokens_bukkit_new = tokens_bukkit["new-api"]
    only_projects = config["only-projects"]
    ignored_projects = config["ignored-projects"]


def modrinth(name, project):
    platforms = project['platforms']
    if 'modrinth' not in platforms:
        print(f"{yellow}{name} | MODRINTH | No Modrinth platform defined, skipping{reset}")
        return
    modrinth_id = platforms['modrinth']

    # Get latest version
    latest_version_response = requests.request(
        "GET",
        modrinth_version_url.format(project_id=modrinth_id),
        headers={
            "User-Agent": user_agent,
            "Authorization": tokens_modrinth,
            "Content-Type": "application/json"
        })
    if latest_version_response.status_code != 200:
        print(f"{red}{name} | MODRINTH | Failed to fetch versions: {latest_version_response.status_code} {latest_version_response.text}")
        return
    latest_version_json = latest_version_response.json()
    if len(latest_version_json) == 0:
        print(f"{red}{name} | MODRINTH | No versions found")
        return
    latest_version = latest_version_json[0]
    latest_version_id = latest_version['id']
    link = "https://modrinth.com/plugin/{modrinth_id}/version/{latest_version_id}".format(
        modrinth_id=modrinth_id,
        latest_version_id=latest_version_id)

    # Check if Minecraft versions already match
    different = False
    game_versions = latest_version['game_versions']
    for version in project["minecraft-versions"]:
        if version not in game_versions:
            different = True
            break
    if not different:
        print(f"{yellow}{name} | MODRINTH | Minecraft versions already match, skipping update for {link}{reset}")
        return

    # Update version
    update = requests.request(
        "PATCH",
        modrinth_update_url.format(version_id=latest_version_id),
        headers={
            "User-Agent": user_agent,
            "Authorization": tokens_modrinth,
            "Content-Type": "application/json"
        },
        json={
            "loaders": project['loaders'],
            "game_versions": project["minecraft-versions"]
        })
    if update.status_code != 204:
        print(f"{red}{name} | MODRINTH | Failed to update supported versions: {update.status_code} {update.text}")
        return

    print(f"{green}{name} | MODRINTH | Successfully updated supported versions for {link}{reset}")


def hangar(name, project):
    platforms = project['platforms']
    if 'hangar' not in platforms:
        print(f"{yellow}{name} | HANGAR | No Hangar platform defined, skipping{reset}")
        return
    hangar_data = platforms['hangar']
    if 'name' not in hangar_data:
        print(f"{yellow}{name} | HANGAR | No Hangar name defined, skipping{reset}")
        return
    hangar_id = hangar_data['name']

    # Get latest version
    latest_version_name = requests.request(
        "GET",
        hangar_latest_url.format(project_id=hangar_id),
        headers={
            "User-Agent": user_agent,
            "Authorization": "HangarAuth " + get_hangar_jwt(),
            "Content-Type": "text/plain"
        })
    if latest_version_name.status_code != 200:
        print(f"{red}{name} | HANGAR | Failed to fetch latest version: {latest_version_name.status_code} {latest_version_name.text}")
        return

    # Get full version data to obtain version ID
    latest_version_response = requests.request(
        "GET",
        hangar_version_url.format(project_id=hangar_id, latest_version_name=latest_version_name.text),
        headers={
            "User-Agent": user_agent,
            "Authorization": "HangarAuth " + get_hangar_jwt(),
            "Content-Type": "application/json"
        })
    if latest_version_response.status_code != 200:
        print(f"{red}{name} | HANGAR | Failed to fetch version data: {latest_version_response.status_code} {latest_version_response.text}")
        return
    latest_version = latest_version_response.json()
    latest_version_id = latest_version['id']
    link = "https://hangar.papermc.io/{author}/{project_id}/versions/{version_id}".format(
        author=hangar_data['author'],
        project_id=hangar_id,
        version_id=latest_version_id)

    # Remove invalid Minecraft versions
    minecraft_versions = project["minecraft-versions"].copy()
    for invalid_version in invalid_hangar_versions:
        # Catch-all version (example: "1.21.x")
        if 'x' in invalid_version:
            match = invalid_version[:-1]  # Example: "1.21."
            zero = match[:-1]  # Example: "1.21"
            if zero in minecraft_versions:
                minecraft_versions.remove(zero)  # Example: remove "1.21"
            minecraft_versions = [v for v in minecraft_versions if not v.startswith(match)]  # Example: remove all versions starting with "1.21."

        # Specific version
        if invalid_version in minecraft_versions:
            minecraft_versions.remove(invalid_version)

    # Check if Minecraft versions already match
    different = False
    versions = latest_version['platformDependencies']['PAPER']
    for version in minecraft_versions:
        if version not in versions:
            different = True
            break
    if not different:
        print(f"{yellow}{name} | HANGAR | Minecraft versions already match, skipping update for {link}{reset}")
        return

    # Get internal project ID
    project_response = requests.request(
        "GET",
        hangar_project_url.format(project_id=hangar_id),
        headers={
            "User-Agent": user_agent,
            "Authorization": "HangarAuth " + get_hangar_jwt(),
            "Content-Type": "application/json"
        })
    if project_response.status_code != 200:
        print(f"{red}{name} | HANGAR | Failed to fetch project data: {project_response.status_code} {project_response.text}")
        return
    internal_id = project_response.json()['id']

    # Update version
    update_response = requests.request(
        "POST",
        hangar_update_url.format(project_id=internal_id, version_id=latest_version_id),
        headers={
            "User-Agent": user_agent,
            "Authorization": "HangarAuth " + get_hangar_jwt(),
            "Content-Type": "application/json"
        },
        json={
            "platform": "PAPER",
            "versions": minecraft_versions
        })
    if update_response.status_code != 200:
        print(f"{red}{name} | HANGAR | Failed to update supported versions: {update_response.status_code} {update_response.text}")
        return

    print(f"{green}{name} | HANGAR | Successfully updated supported versions for {link}{reset}")


def bukkit(name, project):
    platforms = project['platforms']
    if 'bukkit' not in platforms:
        print(f"{yellow}{name} | BUKKIT | No Bukkit platform defined, skipping{reset}")
        return
    bukkit_id = platforms['bukkit']

    # Process major-only versions
    new_versions = project["minecraft-versions"].copy()
    for version in project["minecraft-versions"]:
        for major in bukkit_major_only:
            if version.startswith(major + "."):
                if major not in new_versions:
                    new_versions.append(major)
                new_versions.remove(version)

    # Map versions to IDs
    got_bukkit_versions = get_bukkit_versions()
    if got_bukkit_versions is None or len(got_bukkit_versions) == 0:
        print(f"{red}{name} | BUKKIT | Failed to fetch Bukkit versions")
        return
    version_ids = []
    for version in new_versions:
        if version in got_bukkit_versions:
            version_ids.append(got_bukkit_versions[version])
        else:
            print(f"{yellow}{name} | BUKKIT | Version {version} not found in Bukkit versions, skipping it")
    if len(version_ids) == 0:
        print(f"{yellow}{name} | BUKKIT | No valid versions found, skipping")
        return

    # Get latest version ID
    latest_version_response = requests.request(
        "GET",
        bukkit_files_url.format(project_id=bukkit_id),
        headers={
            "User-Agent": user_agent,
            "x-api-key": tokens_bukkit_new,
            "Content-Type": "application/json"
        })
    if latest_version_response.status_code != 200:
        print(f"{red}{name} | BUKKIT | Failed to fetch latest version: {latest_version_response.status_code} {latest_version_response.text}")
        return
    latest_version_data = latest_version_response.json()["data"]
    if len(latest_version_data) == 0:
        print(f"{red}{name} | BUKKIT | No versions found")
        return
    latest_version = latest_version_data[0]
    latest_version_id = latest_version['id']

    # Get mod slug
    slug = name
    slug_response = requests.request(
        "GET",
        bukkit_slug_url.format(project_id=bukkit_id),
        headers={
            "User-Agent": user_agent,
            "x-api-key": tokens_bukkit_new,
            "Content-Type": "application/json"
        })
    if slug_response.status_code == 200:
        slug = slug_response.json()["data"]["slug"]

    link = "https://curseforge.com/minecraft/bukkit-plugins/{slug}/files/{latest_version_id}".format(
        slug=slug,
        latest_version_id=latest_version_id)

    # Check if Minecraft versions already match
    different = False
    game_versions = latest_version['gameVersions']
    for version in new_versions:
        if version not in game_versions:
            different = True
            break
    if not different:
        print(f"{yellow}{name} | BUKKIT | Minecraft versions already match, skipping update for {link}{reset}")
        return

    # Update version
    update_response = requests.request(
        "POST",
        bukkit_update_url.format(project_id=bukkit_id),
        headers={
            "User-Agent": user_agent,
            "X-Api-Token": tokens_bukkit_upload,
        },
        files={
            "metadata": (None, json.dumps({
                "fileID": latest_version_id,
                "gameVersions": version_ids
            }), "application/json")
        })
    if update_response.status_code != 200:
        print(f"{red}{name} | BUKKIT | Failed to update supported versions: {update_response.status_code} {update_response.text}")
        return

    print(f"{green}{name} | BUKKIT | Successfully updated supported versions for https://www.curseforge.com/minecraft/bukkit-plugins/{slug}/files/{latest_version_id}")


def get_hangar_jwt():
    global hangar_jwt
    if hangar_jwt is not None:
        return hangar_jwt

    jwt_response = requests.request(
        "POST",
        hangar_jwt_url.format(api_key=tokens_hangar),
        headers={
            "User-Agent": user_agent,
            "Content-Type": "application/json"
        })
    if jwt_response.status_code != 200:
        print(f"{red}Failed to fetch Hangar JWT: {jwt_response.status_code} {jwt_response.text}{reset}")
        return None

    hangar_jwt = jwt_response.json()["token"]
    return hangar_jwt


def get_bukkit_versions():
    global bukkit_versions
    if bukkit_versions is not None:
        return bukkit_versions

    version_response = requests.request(
        "GET",
        bukkit_versions_url,
        headers={
            "User-Agent": user_agent,
            "X-Api-Token": tokens_bukkit_upload,
            "Content-Type": "application/json"
        })
    if version_response.status_code != 200:
        print(f"{red}Failed to fetch Bukkit version IDs: {version_response.status_code} {version_response.text}{reset}")
        return None

    bukkit_versions = {}
    for version in version_response.json():
        if version["gameVersionTypeID"] == 1:
            bukkit_versions[version["name"]] = version["id"]
    return bukkit_versions


# Fetch projects data
response = requests.request(
    "GET",
    "https://srnyx.com/projects/data",
    headers={
        "User-Agent": user_agent,
        "Content-Type": "application/json"
    }).json()
if response["status"] != "done":
    print("Failed to fetch projects data: " + response)
    exit(1)

# Update projects
projects = response["projects"]
has_modrinth = tokens_modrinth is not None and len(tokens_modrinth) > 0
has_hangar = tokens_hangar is not None and len(tokens_hangar) > 0
has_bukkit = tokens_bukkit_upload is not None and len(tokens_bukkit_upload) > 0 and tokens_bukkit_new is not None and len(tokens_bukkit_new) > 0
only_projects_defined = only_projects is not None and len(only_projects) > 0
for project_name in projects:
    if only_projects_defined and project_name not in only_projects:
        print(f"{yellow}{project_name} | Not in only-projects, skipping{reset}")
        continue

    if project_name in ignored_projects:
        print(f"{yellow}{project_name} | Ignored{reset}")
        continue

    project_loop = projects[project_name]
    if project_loop["platforms"] is None:
        print(f"{yellow}{project_name} | No platforms defined, skipping{reset}")
        continue

    print(f"{blue}{project_name} | Updating...{reset}")
    if has_modrinth:
        modrinth(project_name, project_loop)
    if has_hangar:
        hangar(project_name, project_loop)
    if has_bukkit:
        bukkit(project_name, project_loop)
