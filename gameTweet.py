#!/usr/bin/env python3

import time
import re
import requests
import tweepy
import facebook
from google.oauth2 import service_account
from googleapiclient.discovery import build
import json
import csv


# Load all credentials at once from a single JSON file
with open('muhKey.json', 'r') as file:
    muh = json.load(file)

def read_csv(file_path):
    """Reads the last five entries from the CSV file and returns them."""
    try:
        with open(file_path, 'r', newline='') as file:
            reader = csv.reader(file, delimiter='~')
            return list(reader)[-5:]  # Return the last 5 entries
    except FileNotFoundError:
        return []  # Return an empty list if the file does not exist

def append_to_csv(file_path, row_data):
    """Appends a row of data to the CSV file."""
    with open(file_path, 'a', newline='') as file:
        writer = csv.writer(file, delimiter='~')
        writer.writerow(row_data)

def fetch_youtube_broadcast_details():
    api_key = muh['youtube']['apiKey']
    channel_id = muh['youtube']['channelId']
    youtube = build('youtube', 'v3', developerKey=api_key)

    request = youtube.search().list(
        part="snippet",
        channelId=channel_id,
        eventType="live",
        type="video",
        order="date",  # Ensures the latest videos come first.
        maxResults=1  # Adjust if you need more results.
    )
    response = request.execute()

    if response['items']:
        broadcast_title = response['items'][0]['snippet']['title']
        broadcast_url = f"https://www.youtube.com/watch?v={response['items'][0]['id']['videoId']}"
        return broadcast_title, broadcast_url
    else:
        return None, None


def get_twitch_access_token(client_id, client_secret):
    """Obtain a Twitch access token."""
    url = "https://id.twitch.tv/oauth2/token"
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        print(f"Error obtaining access token: {response.status_code}")
        return None

def query_igdb(client_id, access_token, query):
    """Query the IGDB API with the given query."""
    url = "https://api.igdb.com/v4/games"
    headers = {
        'Client-ID': client_id,
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.post(url, headers=headers, data=query)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error querying IGDB: {response.status_code}")
        print(response.reason)
        return None

def download_game_art(game_title):
    
    access_token = get_twitch_access_token(muh["igdb"]["clientId"], muh["igdb"]["clientSecret"])
    if access_token:
        print("game title is", game_title)
        query = 'fields name, cover.url; search "' + game_title + '"; where version_parent = null; limit 1;'
        print("our query is" , query)
        gameData = query_igdb(muh["igdb"]["clientId"], access_token, query)
        if gameData:
            # print(gameData)
            # exit()
            cover_url = gameData[0]['cover']['url'].replace('t_thumb', 't_cover_big')
            cover_url = f"https:{cover_url}"
            image_response = requests.get(cover_url)
            
            if image_response.status_code == 200:
                local_filename = f"./images/{game_title}.jpg"
                with open(local_filename, 'wb') as file:
                    file.write(image_response.content)
                return local_filename
        else:
            print("Failed to retrieve data from IGDB.")
    else:
        print("Failed to obtain access token.")    


def post_to_facebook(page_id, game_title, broadcast_url, image_path=None):
    access_token = muh['fb']['accessToken']
    
    graph = facebook.GraphAPI(access_token)
    message = f"Now broadcasting: {game_title}!\n\nWatch here: {broadcast_url} #{game_title.replace(' ', '')}"
    
    if image_path:
        with open(image_path, 'rb') as file:
            graph.put_photo(image=open(image_path, 'rb'), message=message, album_path=page_id + "/photos")
    else:
        graph.put_object(parent_object=page_id, connection_name='feed', message=message)

def post_to_twitter(game_title, broadcast_url, image_path=None):
    auth = tweepy.OAuthHandler(muh['twitter']['consumerKey'], muh['twitter']['consumerSecret'])
    auth.set_access_token(muh['twitter']['accessToken'], muh['twitter']['accessTokenSecret'])
    api = tweepy.API(auth)
    
    image_path = image_path if image_path else "./images/defaulthbom.png"
    media = api.media_upload(image_path)
    
    client = tweepy.Client( muh['twitter']['bearerToken'], muh['twitter']['consumerKey'], muh['twitter']['consumerSecret'], muh['twitter']['accessToken'], muh['twitter']['accessTokenSecret'])
    tweet = f"Now Streaming: {game_title}!\n\nWatch here: {broadcast_url} #{game_title.replace(' ', '')}"
    client.create_tweet(text=tweet, media_ids=[media.media_id_string])





if __name__ == "__main__":
    print("I am le-tired, taking a 5 second nap... then FIRING ZE MISSLES")
    time.sleep(5)

    print("We're fetching the most recent current LIVE video")
    broadcast_title, broadcast_url = fetch_youtube_broadcast_details()
    csv_file_path = 'broadcast_history.csv'  # Specify your CSV file name and path

    # Check if the broadcast has already been shared
    recent_entries = read_csv(csv_file_path)
    if any(broadcast_url in entry for entry in recent_entries):
        print("This broadcast has already been shared. Exiting.")
        exit()

    if broadcast_title:
        game_titles = re.findall(r'\[(.*?)\]', broadcast_title)
        # If one or more matches are found, use the last one; otherwise, use the broadcast_title
        if game_titles:
            print("We found", game_titles[-1])
            game_title = game_titles[-1]  # This selects the last item from the list
        else:
            print("No game titles found, just sharing", broadcast_title)
            game_title = broadcast_title  # Use the whole title if no brackets are found

        image_path = download_game_art(game_title)
        print("artwork downloaded to", image_path)
        post_to_twitter(game_title, broadcast_url, image_path)
        #post_to_facebook('your_facebook_page_id', game_title, broadcast_url, image_path)
        
        # Append a new entry to the CSV file
        append_to_csv(csv_file_path, [broadcast_title, broadcast_url, game_title, image_path])
        print("Shared on social accounts and recorded in the data store.")