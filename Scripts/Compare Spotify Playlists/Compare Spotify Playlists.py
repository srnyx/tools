# Script to get the different songs between two Spotify playlists

import http.server
import socketserver
import requests
import spotipy
import pandas as pd
import json
import base64

# Load config.json
with open('config.json') as json_file:
    config = json.load(json_file)

# Check if 2 playlists are provided
playlists = config['playlists']
if '1' not in playlists or '2' not in playlists:
    raise ValueError('Please provide 2 playlists in the config.json file')
api = config['api']


# Get the songs of a playlist
def get_playlist_songs(spotify, playlist_i):
    # Get playlist ID
    playlist_id = playlists.get(playlist_i)
    print(f'Getting songs of playlist #{playlist_i} ({playlist_id})...')

    # Get songs
    songs = []
    offset = 0
    while True:
        response = spotify.playlist_tracks(playlist_id, offset=offset, limit=100, fields='next,items(track(name,artists))')
        items = response['items']
        for item in items:
            song = item['track']
            songs.append({
                'playlist': playlist_i,
                'song_name': song['name'],
                'artist': song['artists'][0]['name']
            })
        if not response['next']:
            break
        offset += len(items)

    # Sort by artist then song_name
    songs = sorted(songs, key=lambda x: (x['artist'], x['song_name']))

    print(f'Got {len(songs)} songs of playlist #{playlist_i} ({playlist_id})')
    return pd.DataFrame(songs)


class Server(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Get code from URL
        split = self.path.split('code=')
        if len(split) < 2:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<html><head><title>Compare Spotify Playlists</title></head><body><h1>Compare Spotify Playlists</h1><p>Code not found</p></body></html>')
            return

        # Get access token
        data = {
            'code': split[1],
            'redirect_uri': 'http://localhost:34784',
            'grant_type': 'authorization_code'
        }
        headers = {
            'content-type': 'application/x-www-form-urlencoded',
            'Authorization': 'Basic ' + base64.b64encode(f"{api['client_id']}:{api['client_secret']}".encode()).decode()
        }
        response = requests.post('https://accounts.spotify.com/api/token', data=data, headers=headers).json()
        if 'access_token' not in response:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<html><head><title>Compare Spotify Playlists</title></head><body><h1>Compare Spotify Playlists</h1><p>Access token not found</p></body></html>')
            return

        # Get songs of playlists
        spotify = spotipy.Spotify(auth=response['access_token'])
        songs1 = get_playlist_songs(spotify, "1")
        songs2 = get_playlist_songs(spotify, "2")

        # Get different songs (compare song_name and artist but keep playlist column)
        print('Comparing songs...')
        diff_songs = pd.concat([songs1, songs2]).drop_duplicates(subset=['song_name', 'artist'], keep=False)
        diff_songs.columns = ['Playlist', 'Song', 'Artist']
        print(f'Found {len(diff_songs)} different songs')

        # Display different songs in browser
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'<html><head><title>Compare Spotify Playlists</title></head><body><h1>Compare Spotify Playlists</h1><p>Different songs between the two playlists:</p>')
        self.wfile.write(diff_songs.to_html(index=False).replace('<th>', '<th style="text-align: center;">').encode())
        self.wfile.write(b'</body></html>')

        # CSV
        diff_songs.to_csv('different_songs.csv', index=False)
        print('Different songs saved in different_songs.csv')


# Start web server
with socketserver.TCPServer(("", 34784), Server) as httpd:
    print(f'Launch the comparer here: https://accounts.spotify.com/authorize?response_type=code&scope=playlist-read-private&redirect_uri=http://localhost:34784&client_id={api["client_id"]}')
    httpd.serve_forever()
