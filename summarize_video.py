from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import sys
import re
from hugchat import hugchat
from hugchat.login import Login
from env import EMAIL, PASSWD, COOKIE_PATH, API_KEY
from youtube_transcript_api import YouTubeTranscriptApi
from datetime import datetime
from copy import deepcopy
import time

def get_answer(transcript, chapter_title):
    PROMPT = f"""Give me all the actionable points of this video transcript. 
    Keep it concise and to the point, focus on the action, and avoid fluff.
    I don't need the introduction or the conclusion, just the actionable points.
    I don't really need to know why, just what to do. I'll find out why later myself.
    Also skip any ads that might be in the transcript. I really do not care about those.

    TRANSCRIPT: {transcript}"""

    sign = Login(EMAIL, PASSWD)
    cookies = sign.login(cookie_dir_path=COOKIE_PATH, save_cookies=True)

    # Create your ChatBot
    chatbot = hugchat.ChatBot(cookies=cookies.get_dict())  # or cookie_path="usercookies/<email>.json"

    # Switch to the 4th model (assuming models are zero-indexed)
    chatbot.switch_llm(3)  # Switch to the fourth model

    full_response = ""

    #print("--------")
    #print("CHAPTER: ", chapter_title)
    #print("-------------------------------------")
    #print("Response: ", end="", flush=True)

    # Stream response
    for resp in chatbot.query(
        PROMPT,
        stream=True
    ):
        try:
            full_response += resp["token"]
            #print(resp["token"], end="", flush=True)
        except TypeError:
            #print(".", end="", flush=True)
            break
    #print("--------")

    return full_response

# Function to fetch video description from YouTube using API
def get_video_description(api_key, video_id):
    youtube = build('youtube', 'v3', developerKey=api_key)

    try:
        # Get video details including description
        response = youtube.videos().list(
            part='snippet',
            id=video_id
        ).execute()

        # Extract video description
        description = response['items'][0]['snippet']['description']
        title = response['items'][0]['snippet']['title']
        return description, title

    except HttpError as e:
        print(f'An HTTP error {e.resp.status} occurred:\n{e.content}')
        return None

# Function to extract timestamps (chapters) from video description
def extract_timestamps(text):
    # Regular expression pattern to match timestamps and chapter titles
    pattern = r'(?P<timestamp>\d{1,2}:\d{2}(?::\d{2})?)\s+(?P<title>.+?)(?=\n\d{1,2}:\d{2}|$)'

    # Extract timestamps and chapter titles using regex
    matches = re.finditer(pattern, text)

    # List to store tuples of timestamps and chapter titles
    chapter_titles_timestamps = []

    # Iterate over matches and extract timestamps and chapter titles
    for match in matches:
        timestamp = match.group('timestamp')
        title = match.group('title')
        chapter_titles_timestamps.append((timestamp, title))
    
    return chapter_titles_timestamps

# Function to extract transcript from YouTube video
def get_transcript(video_id, timestamps=None):
    if timestamps:
        pass
    else:
        timestamped_transcript = YouTubeTranscriptApi.get_transcript(video_id)
        time_duration_sec = max([line['start'] for line in timestamped_transcript])
        if timestamped_transcript:
            transcript = ' '.join([line['text'] for line in timestamped_transcript])
            return transcript, time_duration_sec, timestamped_transcript

def convert_timestamp_to_seconds(timestamp):
    # Parse the timestamp string
    if timestamp.count(':') == 2:
        time_obj = datetime.strptime(timestamp, "%H:%M:%S")
    else:
        time_obj = datetime.strptime(timestamp, "%M:%S")

    # Calculate the total number of seconds
    total_seconds = (time_obj.hour * 3600) + (time_obj.minute * 60) + time_obj.second
    return total_seconds

def combine_transcript_with_chapters(transcript, chapters):
    combined_chapters = []
    current_chapter_index = 0
    current_chapter_text = []

    for entry in transcript:
        start_time = entry['start']

        while current_chapter_index < len(chapters) - 1 and start_time >= convert_timestamp_to_seconds(chapters[current_chapter_index + 1][0]):
            combined_chapters.append((chapters[current_chapter_index][1], current_chapter_text))
            current_chapter_index += 1
            current_chapter_text = []

        current_chapter_text.append(entry['text'])

    if current_chapter_index < len(chapters):
        combined_chapters.append((chapters[current_chapter_index][1], current_chapter_text))

    return combined_chapters


def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py <YouTube_URL1> <YouTube_URL2> ...")
        sys.exit(1)

    urls = deepcopy(sys.argv[1:])

    for url in urls:
        # Extract video ID from URL
        video_id = url.split('=')[-1].split('&')[0]

        description, title = get_video_description(API_KEY, video_id)
        if description:
            timestamps = extract_timestamps(description)

        transcript, time_duration_sec, raw = get_transcript(video_id)
        
        if transcript:
            #print(f"Transcript for video {url}:\n{transcript}\n")
            if time_duration_sec < 900:
                fulltext = get_answer(transcript, "all").replace('*', '-')
                with open(f"./summaries/${title}.txt", 'w') as file:
                    file.write(fulltext)
            else:
                combined_chapters = combine_transcript_with_chapters(raw, timestamps)
                fulltext = """Here are the actionable points from the video:"""
                #
                for chapter_title, chapter_text in combined_chapters:
                    time.sleep(60)
                    fulltext += f"""
                    -------------------------------------
                    CHAPTER: {chapter_title}
                    -------------------------------------
                    {get_answer(' '.join(chapter_text), chapter_title).replace('*', '-')}
                    -------------------------------------
                    """
                #print(fulltext)
                with open(f"./summaries/${title}.txt", 'w') as file:
                    file.write(fulltext)

if __name__ == "__main__":
    main()
                
