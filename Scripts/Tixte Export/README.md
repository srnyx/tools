# Tixte Export

Adapted from https://gist.github.com/pythonmcpi/fb447e8907bc985fa47af0486e245417

If you only need to export URLs from Tixte, you can use the `retrieve` function.

If you also want to download the files from the URLs, you can use the `download` function (after all URLs are retrieved).

If you retrieve URLs first, then later decide you want to download the files, disable retrieval and enable download (just make sure the retrieval output file exists). *This is the recommended approach so that you can leave retrieval on in the background then come back and monitor the download process.*

### Downloading files

Downloading files can be a bit iffy sometimes. Tixte might randomly block your connection, even if you aren't making that many requests. So you'll probably want to monitor the downloading process and restart the program if it fails.

It's recommended to keep `unique_subfolder` disabled, so that if you need to restart the program, it won't redownload files that were already downloaded. *It will automatically handle files that weren't fully downloaded if the program is interrupted in a previous run.*

If multiple files on different domains have the same name, only the newest file will be downloaded. It will say in console in red text any file that was skipped and its URL so that you can manually check/download it if you want.

## `config.json`

- `retrieve`:
  - `enabled`: whether to retrieve URLs from Tixte
  - `token`: Tixte API token
  - `output`: path to the output file
  - `amount`: number of URLs to retrieve per request (max 150)
  - `start_page`: page to start retrieving URLs from (0-indexed)
  - `sleep`: time to sleep between requests
- `download`:
  - `enabled`: whether to download the files from the URLs (after all URLs are retrieved)
  - `output_folder`: folder to save the downloaded files to
  - `unique_subfolder`: whether to create a unique subfolder for each download session (based on timestamp)
  - `always_set_time`: whether to always set the file's Modified Time to the uploaded_at timestamp, even if the file already exists (setting this to false will not disable setting the time if the file didn't exist before)
  - `sleep`: time to sleep between downloads

```json
{
  "retrieve": {
    "enabled": true,
    "token": "PUT_YOUR_TIXTE_TOKEN_HERE",
    "output": "output.jsonl",
    "amount": 150,
    "start_page": 0,
    "sleep": 1
  },
  
  "download": {
    "enabled": false,
    "output_folder": "downloads",
    "unique_subfolder": false,
    "always_set_time": true,
    "sleep": 0.2
  }
}
```

### How do I get my Tixte API token?

1. Open your Tixte dashboard
2. Go to browser Dev Tools
3. Open the Network tab
4. Ctrl+F for `https://api.tixte.com/v1/users/@me/uploads`
5. Copy the contents of the `Authorization` header under the request headers section
6. Put it in `token` field in `config.json`

### What is `.jsonl`?

JSONL (or JSON Lines) is a line-delimited JSON format, where each line is a JSON object.

This improves performance as the script can write each URL to the file as it is retrieved, rather than having to wait until all URLs are retrieved before writing to the file.
