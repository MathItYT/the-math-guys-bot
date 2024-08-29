from pyyoutube import Client
from dotenv import load_dotenv
import os
import json


load_dotenv()
YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY")


client = Client(api_key=YOUTUBE_API_KEY)


def retrieve_new_youtube_videos(channels_json: str) -> list[dict]:
    with open(channels_json, "r") as fp:
        channels: list[dict] = json.load(fp)
    new_videos = []
    for data in channels:
        channel_id = data["youtube_id"]
        response = client.search.list(parts="snippet", channel_id=channel_id, max_results=1, order="date")
        video_id = response.items[0].id.videoId
        title = response.items[0].snippet.title
        if data["latest_video_id"] != video_id:
            data["latest_video_id"] = video_id
            data["video_title"] = title
            new_videos.append(data)
    if not new_videos:
        return []
    with open(channels_json, "w") as fp:
        json.dump(channels, fp, indent=4)
    return new_videos
