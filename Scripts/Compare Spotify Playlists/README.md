# Compare Spotify Playlists

This script compares two Spotify playlists and returns the tracks that are different between them

## Usage

1. First, create a Spotify application and get your `client_id` and `client_secret` from the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/applications)
2. Next, create a `config.json` file with the following structure:

    ```json
    {
      "api": {
        "client_id": "YOUR_CLIENT_ID",
        "client_secret": "YOUR_CLIENT_SECRET"
      },
    
      "playlists": {
        "1": "PLAYLIST_ID_1",
        "2": "PLAYLIST_ID_2"
      }
    }
    ```
3. Now just run the script and click the link that appears in the console
4. Once it's done, it will display an HTML table and save the differences in a `different_songs.csv` file
