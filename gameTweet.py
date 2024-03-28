import time
import re
import requests
import tweepy
import facebook
from google.oauth2 import service_account
from googleapiclient.discovery import build
import json

# Function to fetch the latest YouTube broadcast title and URL
def fetch_youtube_broadcast_details():
    credentials = service_account.Credentials.from_service_account_file(
        'muhKey.json',
        scopes=['https://www.googleapis.com/auth/youtube.readonly'])

    youtube = build('youtube', 'v3', credentials=credentials)

    request = youtube.liveBroadcasts().list(
        part='snippet,contentDetails',
        broadcastStatus='active'
    )

    response = request.execute()

    if response['items']:
        broadcast_title = response['items'][0]['snippet']['title']
        broadcast_url = f"https://www.youtube.com/watch?v={response['items'][0]['contentDetails']['boundStreamId']}"
        return broadcast_title, broadcast_url
    else:
        return None, None

# Modified to return False when the game art is not found
def download_game_art(game_title):
    image_url = "http://example.com/path/to/game/art.jpg"  # Placeholder URL
    
    try:
        response = requests.get(image_url)
        if response.status_code == 200:
            with open(f"{game_title}.jpg", 'wb') as file:
                file.write(response.content)
            return f"{game_title}.jpg"
    except Exception as e:
        print(f"Error downloading game art: {e}")
    return False


def post_to_facebook(page_id, game_title, broadcast_url, image_path=None):
    with open('facebookCreds.json', 'r') as file:
        fb_creds = json.load(file)
    access_token = fb_creds['access_token']
    
    graph = facebook.GraphAPI(access_token)
    message = f"Now broadcasting: {game_title}!\n\nWatch here: {broadcast_url} #{game_title.replace(' ', '')}"
    
    if image_path:
        # Post with image
        with open(image_path, 'rb') as file:
            graph.put_photo(image=open(image_path, 'rb'), message=message, album_path=page_id + "/photos")
    else:
        # Post without image
        graph.put_object(parent_object=page_id, connection_name='feed', message=message)


# Modified to use a default image if game art is not found
def post_to_twitter(game_title, broadcast_url, image_path=None):
    with open('twitterCreds.json', 'r') as file:
        twtr = json.load(file)
    consumer_key = twtr['twitter_consumer_key']
    consumer_secret = twtr['twitter_consumer_secret']
    access_token = twtr['twitter_access_token']
    access_token_secret = twtr['twitter_access_token_secret']
    
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    
    # Use the default 'bubble.png' if no image path is provided
    image_path = image_path if image_path else "bubble.png"
    media = api.media_upload(image_path)
    
    tweet = f"Now broadcasting: {game_title}!\n\nWatch here: {broadcast_url} #{game_title.replace(' ', '')}"
    api.update_status(status=tweet, media_ids=[media.media_id_string])

# Main logic
if __name__ == "__main__":
    time.sleep(30)  # Delay to ensure the broadcast is live

    broadcast_title, broadcast_url = fetch_youtube_broadcast_details()
    if broadcast_title:
        game_title_search = re.search(r'\[(.*?)\]', broadcast_title)
        if game_title_search:
            game_title = game_title_search.group(1)
            image_path = download_game_art(game_title)
            # Post to Twitter
            post_to_twitter(game_title, broadcast_url, image_path)
            # Post to Facebook
            post_to_facebook('your_facebook_page_id', game_title, broadcast_url, image_path)
        else:
            # If game title is not found within brackets, use the broadcast title directly and post
            post_to_twitter(broadcast_title, broadcast_url)
            post_to_facebook('your_facebook_page_id', broadcast_title, broadcast_url)
