#!/usr/bin/env python3

import os
import time
import re
import requests
import tweepy
import facebook
from googleapiclient.discovery import build
import json
import csv

# Environment variables instead of muhKey.json
api_key = os.getenv("YOUTUBE_API_KEY")
channel_id = os.getenv("YOUTUBE_CHANNEL_ID")
fb_access_token = os.getenv("FB_ACCESS_TOKEN")
twitter_bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
twitter_consumer_key = os.getenv("TWITTER_CONSUMER_KEY")
twitter_consumer_secret = os.getenv("TWITTER_CONSUMER_SECRET")
twitter_access_token = os.getenv("TWITTER_ACCESS_TOKEN")
twitter_access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
igdb_client_id = os.getenv("IDGB_CLIENT_ID")
igdb_client_secret = os.getenv("IDGB_CLIENT_SECRET")

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

def get_twitch_access_token():
    """Obtain a Twitch access token."""
    url = "https://id.twitch.tv/oauth2/token"
    payload = {
        'client_id': igdb_client_id,
        'client_secret': igdb_client_secret,
        'grant_type': 'client_credentials'
    }
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        print(f"Error obtaining access token: {response.status_code}")
        return None

def query_igdb(access_token, query):
    """Query the IGDB API with the given query."""
    url = "https://api.igdb.com/v4/games"
    headers = {
        'Client-ID': igdb_client_id,
        'Authorization': f'Bearer {access_token}',
    }
    print(f"now searching for {query}")
    response = requests.post(url, headers=headers, data=query)
    if response.status_code == 200:
        return response.json()
        print(response.json())
    else:
        print(f"Error querying IGDB: {response.status_code}")
        print(response.reason)
        return None

def download_game_art(game_title):
    access_token = get_twitch_access_token()
    if access_token:
        query = f'fields name, cover.url; search "{game_title}"; where version_parent = null; limit 1;'
        gameData = query_igdb(access_token, query)
        if gameData:
            print(gameData)
            cover_url = gameData[0]['cover']['url'].replace('t_thumb', 't_cover_big')
            cover_url = f"https:{cover_url}"
            image_response = requests.get(cover_url)
            
            if image_response.status_code == 200:
                local_filename = f"./images/{game_title}.jpg"
                print(local_filename)
                with open(local_filename, 'wb') as file:
                    file.write(image_response.content)
                return local_filename
    else:
        print("Failed to retrieve data from IGDB or obtain access token.")    

def post_to_facebook(page_id, game_title, broadcast_url, image_path=None):
    graph = facebook.GraphAPI(fb_access_token)
    message = f"Now broadcasting: {game_title}!\nWatch here: {broadcast_url} #{game_title.replace(' ', '')}"
    
    if image_path:
        with open(image_path, 'rb') as file:
            graph.put_photo(image=open(image_path, 'rb'), message=message, album_path=page_id + "/photos")
    else:
        graph.put_object(parent_object=page_id, connection_name='feed', message=message)

def post_to_twitter(game_title, broadcast_url, image_path=None):
    auth = tweepy.OAuthHandler(twitter_consumer_key, twitter_consumer_secret)
    auth.set_access_token(twitter_access_token, twitter_access_token_secret)
    api = tweepy.API(auth)
    
    if image_path is None:
        image_path = "./images/defaulthbom.png"
    media = api.media_upload(image_path)
    
    client = tweepy.Client(twitter_bearer_token, twitter_consumer_key, twitter_consumer_secret, twitter_access_token, twitter_access_token_secret)
    tweet = f"Now Streaming: {game_title}!\nWatch here: {broadcast_url} #{game_title.replace(' ', '')}"
    client.create_tweet(text=tweet, media_ids=[media.media_id_string])

if __name__ == "__main__":
    print("Starting script...")

    broadcast_title, broadcast_url = fetch_youtube_broadcast_details()
    csv_file_path = 'broadcast_history.csv'  # Specify your CSV file name and path

    recent_entries = read_csv(csv_file_path)
    if any(broadcast_url in entry for entry in recent_entries):
        print("This broadcast has already been shared. Exiting.")
    else:
        if broadcast_title:
            game_titles = re.findall(r'\[(.*?)\]', broadcast_title)
            game_title = game_titles[-1] if game_titles else broadcast_title

            image_path = download_game_art(game_title)
            print("Artwork downloaded to", image_path)
            post_to_twitter(game_title, broadcast_url, image_path)
            # post_to_facebook('your_facebook_page_id', game_title, broadcast_url, image_path)
            
            append_to_csv(csv_file_path, [broadcast_title, broadcast_url, game_title, image_path])
            print("Shared on social accounts and recorded in the data store.")
