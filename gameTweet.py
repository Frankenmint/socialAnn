import time
import re
import requests
import tweepy
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Function to fetch the latest YouTube broadcast title and URL
def fetch_youtube_broadcast_details():
    # Assuming you have set up a service account and downloaded the JSON key file
    credentials = service_account.Credentials.from_service_account_file(
        'path/to/your/service_account_file.json',
        scopes=['https://www.googleapis.com/auth/youtube.readonly'])

    youtube = build('youtube', 'v3', credentials=credentials)

    # Fetch live broadcasts
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

# Function to search for the game in the database and download art
def download_game_art(game_title):
    # Placeholder for game database API call
    # You'll replace this with actual API call logic to your game database
    image_url = "http://example.com/path/to/game/art.jpg"
    
    response = requests.get(image_url)
    if response.status_code == 200:
        with open(f"{game_title}.jpg", 'wb') as file:
            file.write(response.content)
        return True
    return False

# Function to post to Twitter
def post_to_twitter(game_title, broadcast_url, image_path):
    consumer_key = 'your_twitter_consumer_key'
    consumer_secret = 'your_twitter_consumer_secret'
    access_token = 'your_twitter_access_token'
    access_token_secret = 'your_twitter_access_token_secret'
    
    # Authenticate to Twitter
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    
    # Upload image
    media = api.media_upload(image_path)
    
    # Post tweet with image
    tweet = f"Now broadcasting: {game_title}!\n\nWatch here: {broadcast_url} #{game_title}"
    api.update_status(status=tweet, media_ids=[media.media_id_string])

# Main logic
if __name__ == "__main__":
    time.sleep(30)  # Wait for 30 seconds after the broadcast starts

    # Fetch broadcast details
    broadcast_title, broadcast_url = fetch_youtube_broadcast_details()
    if broadcast_title:
        game_title_search = re.search(r'\[(.*?)\]', broadcast_title)
        if game_title_search:
            game_title = game_title_search.group(1)
            if download_game_art(game_title):
                post_to_twitter(game_title, broadcast_url, f"{game_title}.jpg")
