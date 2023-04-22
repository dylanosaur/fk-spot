import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import youtube_dl


def initialize_spotify_handle():

    # set up Spotify API credentials
    client_id = os.getenv("SPOTIFY_ID")
    client_secret = os.getenv("SPOTIFY_SECRET")

    client_credentials_manager = SpotifyClientCredentials(client_id, client_secret)
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    return sp


def scrape_song_names_and_artists_from_spotify_url(sp, playlist_url):
    playlist_id = playlist_url.split("/")[-1]

    # get the track IDs from the playlist
    results = sp.playlist_tracks(playlist_id)
    tracks = results["items"]
    while results["next"]:
        results = sp.next(results)
        tracks.extend(results["items"])
    track_ids = [
        track["track"]["id"] for track in tracks if track["track"]["id"] is not None
    ]
    return track_ids


def extract_name_and_artist_from_spotify_track_id(sp, track_id):
    track_info = {}
    try:
        track_info = sp.track(track_id)
    except Exception as ex:
        print("some major problem pulling from spotify", ex)
        return None
    
    track_name = track_info["name"]
    track_artists = [artist["name"] for artist in track_info["artists"]]
    if len(track_artists) < 1:
        return None
    
    filename = f"{track_name} - {track_artists[0]}.mp3"
    character_blocklist = '_()*&^%#'
    stripped_filename = ''
    for char in filename:
        if char not in character_blocklist:
            stripped_filename += char

    track_file = os.path.join('downloads', filename)
    if not os.path.exists:
        os.mkdir(track_file)

    print(f"Downloading {track_file}")
    return {"name": track_name, "artists": track_artists, "filepath": track_file}


def download_file_from_youtube_from_query(query_text, filepath):
    # file path is a lie, youtube just drops the file and its tough to specify the path beforehand
    ydl_opts = {"quiet": True, "format": "bestaudio/best", "noplaylist": True, }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        for i in range(3):
            try:
                result = ydl.extract_info(f"ytsearch1:{query_text}", download=False)["entries"][i]
                ydl.download([result["webpage_url"]])
            except Exception as e:
                print(f"Could not download {filepath} with option '{query_text}': {e}")


def process_multiple_urls(urls):

    sp = initialize_spotify_handle()

    for playlist_url in urls:

        track_ids = scrape_song_names_and_artists_from_spotify_url(sp, playlist_url)

        # download the tracks
        for track_id in track_ids:
            track = extract_name_and_artist_from_spotify_track_id(sp, track_id)

            track_name = track["name"]
            track_artists = track["artists"]
            filepath = track["filepath"]

            # query YouTube for the track and download the first result
            query = f"{track_name} {track_artists[0]}"

            download_file_from_youtube_from_query(query, filepath)

            print(f"Downloaded {filepath}")


if __name__ == "__main__":

    urls = [
        "https://open.spotify.com/playlist/2w04rL93QpCQQAFTWBfzAY",
        "https://open.spotify.com/playlist/5SZvPxjC10hwR4yphkXBet",
    ]
    process_multiple_urls(urls)
