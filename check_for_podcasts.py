from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime
from env import API_KEY

# Set up YouTube API key
CHANNEL_IDS = ['UChfo46ZNOV-vtehDc25A1Ug', 'UCIaH-gZIVC432YRjNVvnyCA']  # Add more channel IDs as needed

# Function to retrieve videos uploaded to a channel
def get_channel_videos(api_key, channel_id):
    youtube = build('youtube', 'v3', developerKey=api_key)

    try:
        # Get the uploads playlist ID for the channel
        response = youtube.channels().list(
            part='contentDetails',
            id=channel_id
        ).execute()

        playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

        # Get the videos in the uploads playlist
        playlist_items = []
        next_page_token = None

        while True:
            playlist_request = youtube.playlistItems().list(
                part='contentDetails',
                playlistId=playlist_id,
                maxResults=50,  # Maximum allowed by the API
                pageToken=next_page_token
            )
            playlist_response = playlist_request.execute()

            playlist_items.extend(playlist_response['items'])
            next_page_token = playlist_response.get('nextPageToken')

            if not next_page_token:
                break

        return playlist_items

    except HttpError as e:
        print(f'An HTTP error {e.resp.status} occurred:\n{e.content}')
        return None

# Function to check if any videos were uploaded today
def check_new_videos(channel_id, videos):
    if not videos:
        print(f"No videos found for channel ID: {channel_id}")
        return

    today = datetime.utcnow().date()
    new_videos_today = []

    for video in videos:
        video_date = datetime.strptime(video['contentDetails']['videoPublishedAt'], '%Y-%m-%dT%H:%M:%SZ').date()
        if video_date == today:
            new_videos_today.append(video)
    if new_videos_today:
        print(f"{len(new_videos_today)} new videos uploaded today for channel ID: {channel_id}")
        for video in new_videos_today:
            print(f"- TIME: {video['contentDetails']['videoPublishedAt']}, ID:{video['contentDetails']['videoId']}")
    else:
        print(f"No new videos uploaded today for channel ID: {channel_id}")

# Main function
def main():
    for channel_id in CHANNEL_IDS:
        print(f"Checking channel ID: {channel_id}")
        videos = get_channel_videos(API_KEY, channel_id)
        if videos:
            check_new_videos(channel_id, videos)
        print()

if __name__ == "__main__":
    main()
