import json
import time
from datetime import datetime
from pathlib import Path
import requests
from itertools import count
import os


LIST = "https://api.tixte.com/v1/users/@me/uploads"
UPLOAD = "https://us-east-1.tixte.net/uploads"

# Colors
GREEN = "\033[32m"
RED = "\033[31m"
BLUE = "\033[34m"
YELLOW = "\033[33m"
RESET = "\033[0m"

# Read config
with open("config.json") as f:
    config = json.load(f)

# Retrieve config
retrieve = config.get("retrieve", {})
retrieve_enabled = retrieve.get("enabled", False)
retrieve_token = retrieve["token"]
retrieve_output = Path(retrieve.get("output", "output.jsonl"))
retrieve_amount = retrieve.get("amount", 150)
retrieve_start_page = retrieve.get("start_page", 0)
retrieve_sleep = retrieve.get("sleep", 1)

# Download config
download = config.get("download", {})
download_enabled = download.get("enabled", False)
download_folder = Path(download.get("output_folder", "downloads"))
download_unique_subfolder = download.get("unique_subfolder", False)
download_always_set_timestamp = download.get("always_set_timestamp", True)
download_sleep = download.get("sleep", 0.2)


def retrieve_urls():
    # Delete output file if it exists
    if retrieve_output.exists():
        retrieve_output.unlink()

    # Create session with token
    session = requests.Session()
    session.headers.update({"Authorization": retrieve_token})

    received = 0
    progress_digits = 0

    for page in count(0):
        # Print current page
        print(f"{BLUE}\n---------- PAGE {page} ----------{RESET}")

        # Fetch next uploads
        try:
            res = session.get(
                LIST,
                params={"amount": retrieve_amount, "permissions": "[3]", "page": page}
            ).json()["data"]
        except Exception as e:
            print(f"{RED}Failed to fetch uploads: {e}{RESET}")
            break

        total = res["total"]
        results = res["results"]

        # Calculate progress digits
        if progress_digits == 0:
            progress_digits = len(str(total))

        # Reached end of uploads, stop
        if results == 0:
            print(f"{YELLOW}Total expected: {total}\nActual received: {received}{RESET}")
            break

        # Add uploads to output JSON
        with open(retrieve_output, "a") as file:
            for (i, upload) in enumerate(res["uploads"], start=1):
                # Add full name and URL to JSON object
                full_name = upload["name"] + "." + upload["extension"]
                url = f"{UPLOAD}/{upload['domain']}/{full_name}"
                upload["full_name"] = full_name
                upload["url"] = url

                # Write JSON object to file
                json.dump(upload, file)
                file.write("\n")

                # Print URL for progress
                print(f"{GREEN}[{str(received + i).rjust(progress_digits)}/{total}] {url}{RESET}")

        # Update received count
        received += results

        # Reduce load on Tixte
        time.sleep(retrieve_sleep)


def create_download_session():
    session = requests.Session()

    # I have no idea if trust_env and headers are necessary lol
    # It just kept breaking, so I was trying random things, and I'm afraid to change it now...
    session.trust_env = False
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive"
    })

    return session


# Set file's Date Modified to uploaded_at
def set_file_date(progress, upload, final_filepath):
    try:
        uploaded_at_string = upload["uploaded_at"]
        if uploaded_at_string:
            if uploaded_at_string.endswith("Z"):
                uploaded_at_string = uploaded_at_string[:-1] + "+00:00"

            epoch = datetime.fromisoformat(uploaded_at_string).timestamp()
            os.utime(final_filepath, (epoch, epoch))
    except Exception as e:
        print(f"{RED}{progress} Failed to set file timestamp: {e}{' ' * 20}{RESET}")


def download_files():
    # Get name for subfolder
    if download_unique_subfolder:
        subfolder_name = str(int(time.time()))
    else:
        subfolder_name = "downloads"

    # Create download subfolder
    subfolder = download_folder / subfolder_name
    subfolder.mkdir(parents=True, exist_ok=True)

    # Use fresh session exclusively for downloading assets
    session = create_download_session()

    # Read URLs from output file and download
    with open(retrieve_output) as file:
        # Get total files
        total = sum(1 for _ in file)
        file.seek(0)

        progress_digits = len(str(total))
        print(f"{BLUE}---------- DOWNLOADING {total} FILES ----------{RESET}")

        # Download files
        for (i, line) in enumerate(file, start=1):
            upload = json.loads(line)
            url = upload["url"]
            full_name = upload["full_name"]

            part_filepath = subfolder / (full_name + ".part")
            final_filepath = subfolder / full_name

            progress = f"[{str(i).rjust(progress_digits)}/{total}] "

            # Skip if file already exists
            if final_filepath.exists():
                # Set file timestamp to uploaded_at if enabled
                if download_always_set_timestamp:
                    set_file_date(progress, upload, final_filepath)
                    print(f"{RED}{progress}File already exists, setting time and skipping{RESET}")
                    continue

                print(f"{RED}{progress}File already exists, skipping {url}{RESET}")
                continue

            # Download the file (using temporary .part file)
            try:
                # Use browser session to stream data safely
                with session.get(url, stream=True, timeout=15) as res:
                    res.raise_for_status()

                    # Get the total file size in bytes
                    total_size = int(res.headers.get('content-length', 0))
                    downloaded_size = 0

                    with open(part_filepath, "wb") as out_file:
                        for chunk in res.iter_content(chunk_size=8192):
                            out_file.write(chunk)

                            # Print file download progress
                            if total_size > 0:
                                downloaded_size += len(chunk)
                                percentage = int((downloaded_size / total_size) * 100)
                                print(f"{YELLOW}{progress}[{str(percentage).rjust(3)}%] Downloading {url}...{RESET}", end="\r")

                # Rename part file to final name after successful download
                part_filepath.rename(final_filepath)

                # Set file timestamp to uploaded_at
                set_file_date(progress, upload, final_filepath)

                # Print success and sleep to reduce load on Tixte
                print(f"{GREEN}{progress}[100%] Downloaded {url}{' ' * 20}{RESET}")
                time.sleep(download_sleep)

            # 400, 403, 429, 500 etc.
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if e.response else "Unknown"

                # Try to read what the server actually told you (body text or JSON message)
                try:
                    server_msg = e.response.text.strip() if e.response else "No body text"
                    # Truncate if the server returned a massive HTML error page
                    if len(server_msg) > 200:
                        server_msg = server_msg[:200] + "..."
                except Exception as e:
                    server_msg = f"Could not decode server response ({e})"

                print(f"{RED}{progress}✕ HTTP Error {status_code}: {e}{RESET}")
                print(f"{RED}{progress}➔ Server Response: {server_msg}{RESET}")

                if part_filepath.exists():
                    part_filepath.unlink()
                time.sleep(5)  # Give more time for HTTP errors to let server cool down

            except Exception as e:
                print(f"{RED}{progress}✕ {e.__class__.__name__}: {e}{RESET}")

                # ConnectionError: re-initialize session to flush jammed sockets
                if isinstance(e, requests.exceptions.ConnectionError):
                    session.close()
                    session = create_download_session()

                if part_filepath.exists():
                    part_filepath.unlink()
                time.sleep(3)


# Run
if retrieve_enabled:
    retrieve_urls()
if download_enabled:
    download_files()
print(f"{BLUE}\nDone!{RESET}")
