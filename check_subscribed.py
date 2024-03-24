from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Set up OAuth 2.0 authentication
SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

def authenticate():
    flow = InstalledAppFlow.from_client_secrets_file(
        'client_secret.json', SCOPES)
    credentials = flow.run_console()
    return credentials

def get_subscribed_channels(credentials):
    youtube = build(API_SERVICE_NAME, API_VERSION, credentials=credentials)

    channels = []
    next_page_token = None

    while True:
        subscriptions_response = youtube.subscriptions().list(
            part='snippet',
            mine=True,
            maxResults=50,  # Maximum allowed by the API
            pageToken=next_page_token
        ).execute()

        for subscription in subscriptions_response['items']:
            channel_id = subscription['snippet']['resourceId']['channelId']
            channel_title = subscription['snippet']['title']
            channels.append({'id': channel_id, 'title': channel_title})

        next_page_token = subscriptions_response.get('nextPageToken')

        if not next_page_token:
            break

    return channels

def main():
    credentials = authenticate()
    subscribed_channels = get_subscribed_channels(credentials)

    print("Subscribed Channels:")
    for channel in subscribed_channels:
        print(f"- {channel['title']} (ID: {channel['id']})")

if __name__ == "__main__":
    main()
