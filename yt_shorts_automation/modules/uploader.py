import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from googleapiclient.http import MediaFileUpload
from dotenv import load_dotenv

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def upload_video(file_path: str, title: str, description: str, tags: list = None, privacy_status: str = "private"):
    """
    Uploads a video to YouTube.
    """
    client_secrets_file = os.getenv("YOUTUBE_CLIENT_SECRETS_FILE", "client_secrets.json")
    
    if not os.path.exists(client_secrets_file):
        print(f"Client secrets file not found at {client_secrets_file}. Cannot upload.")
        return None

    try:
        # Get credentials
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, SCOPES)
        credentials = flow.run_local_server(port=0)
        
        youtube = googleapiclient.discovery.build(
            "youtube", "v3", credentials=credentials)

        print(f"Uploading {file_path}...")
        
        body = {
            "snippet": {
                "title": title[:100], # Max 100 chars
                "description": description[:5000],
                "tags": tags if tags else ["shorts", "curiosities"],
                "categoryId": "22" # People & Blogs, or 28 (Science & Tech)
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False
            }
        }

        media = MediaFileUpload(file_path, chunksize=-1, resumable=True)

        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Uploaded {int(status.progress() * 100)}%")

        print(f"Upload Complete! Video ID: {response['id']}")
        return response['id']

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

if __name__ == "__main__":
    # Test
    pass
