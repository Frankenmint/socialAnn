#!/usr/bin/env python3

import time
import re
import requests
import tweepy
import facebook
from googleapiclient.discovery import build
from igdb.wrapper import IGDBWrapper
import json

# Load all credentials at once from a single JSON file
with open('muhKey.json', 'r') as file:
    muh = json.load(file)

# Function to fetch the latest YouTube broadcast title and URL using an API key
def fetch_youtube_broadcast_details(api_key):
    youtube = build('youtube', 'v3', developerKey=api_key)

    request = youtube.liveBroadcasts().list(
        part='snippet,contentDetails',
        broadcastStatus='active'
    )

    response = request.execute()

    if response.get('items'):
        broadcast_title = response['items'][0]['snippet']['title']
        broadcast_id = response['items'][0]['id']  # Use the broadcast ID
        broadcast_url = f"https://www.youtube.com/watch?v={broadcast_id}"
        return broadcast_title, broadcast_url
    else:
        return None, None

def download_game_art(game_title):
    client_id = muh['igdb']['clientId']
    client_secret = muh['igdb']['clientSecret']
    wrapper = IGDBWrapper(client_id, client_secret)

    try:
        game_data = wrapper.api_request(
            'games',
            f'search "{game_title}"; fields name, cover.url; where version_parent = null; limit 1;'
        )
        game_data = json.loads(game_data)
        if game_data:
            cover_url = game_data[0]['cover']['url'].replace('t_thumb', 't_cover_big')
            cover_url = f"https:{cover_url}"
            image_response = requests.get(cover_url)
            
            if image_response.status_code == 200:
                local_filename = f"{game_title}.jpg"
                with open(local_filename, 'wb') as file:
                    file.write(image_response.content)
                return local_filename
    except Exception as e:
        print(f"Error fetching or downloading game art from IGDB: {e}")
    return False

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
    twtr = muh['twitter']
    auth = tweepy.OAuthHandler(twtr['consumerKey'], twtr['consumerSecret'])
    auth.set_access_token(twtr['accessToken'], twtr['accessTokenSec'])
    api = tweepy.API(auth)
    
    tweet = f"Now broadcasting: {game_title}!\n\nWatch here: {broadcast_url} #{game_title.replace(' ', '')}"
    if image_path:
        media = api.media_upload(image_path)
        api.update_status(status=tweet, media_ids=[media.media_id_string])
    else:
        api.update_status(status=tweet)

if __name__ == "__main__":
    api_key = muh['youtube']['apiKey']  # Adjust to your actual YouTube API key path in the JSON
    broadcast_title, broadcast_url = fetch_youtube_broadcast_details(api_key)
    if broadcast_title:
        game_title_search = re.search(r'\[(.*?)\]', broadcast_title)
        if game_title_search:
            game_title = game_title_search.group(1)
            image_path = download_game_art(game_title)
            post_to_twitter(game_title, broadcast_url, image_path)
            # Uncomment and fill in your Facebook page ID to enable posting to Facebook
            # post_to_facebook('your_facebook_page_id', game_title, broadcast_url, image_path)
        else:
            post_to_twitter(broadcast_title, broadcast_url)
            # Uncomment and fill in your Facebook page ID to enable posting to Facebook
            # post_to_facebook('your_facebook_page_id', broadcast_title, broadcast_url)
