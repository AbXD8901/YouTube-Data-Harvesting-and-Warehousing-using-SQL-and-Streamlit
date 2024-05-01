import streamlit as st
from googleapiclient.discovery import build
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, Text, BigInteger, DateTime, Time
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import isodate
import pandas as pd

# Database setup
DATABASE_URL = "mysql+pymysql://user:password@localhost/db_name"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()
metadata = MetaData()

# Define database schema
channels = Table('Channels', metadata,
                 Column('Channel_Id', String(255), primary_key=True),
                 Column('Channel_Name', String(255), nullable=False),
                 Column('Subscription_Count', Integer),
                 Column('Channel_Views', BigInteger),
                 Column('Channel_Description', Text),
                 Column('Playlist_Id', String(255)))

playlists = Table('Playlists', metadata,
                  Column('Playlist_Id', String(255), primary_key=True),
                  Column('Channel_Id', String(255), ForeignKey('Channels.Channel_Id')),
                  Column('Playlist_Name', String(255), nullable=False))

videos = Table('Videos', metadata,
               Column('Video_Id', String(255), primary_key=True),
               Column('Channel_Id', String(255), ForeignKey('Channels.Channel_Id')),
               Column('Video_Name', String(255), nullable=False),
               Column('Video_Description', Text),
               Column('PublishedAt', DateTime),
               Column('View_Count', BigInteger),
               Column('Like_Count', BigInteger),
               Column('Dislike_Count', BigInteger),
               Column('Favorite_Count', BigInteger),
               Column('Comment_Count', Integer),
               Column('Duration', Time),
               Column('Thumbnail', String(255)),
               Column('Caption_Status', String(50)))

comments = Table('Comments', metadata,
                 Column('Comment_Id', String(255), primary_key=True),
                 Column('Video_Id', String(255), ForeignKey('Videos.Video_Id')),
                 Column('Comment_Author', String(255)),
                 Column('Comment_Text', Text),
                 Column('Comment_PublishedAt', DateTime))

metadata.create_all(engine)

# YouTube API setup
API_KEY = 'AIexample'
youtube = build('youtube', 'v3', developerKey=API_KEY)

query_mapping = {
    "Names of all videos and their corresponding channels": """
        SELECT v.Video_Name, c.Channel_Name 
        FROM Videos v
        JOIN Channels c ON v.Channel_Id = c.Channel_Id;
    """,
    "Channels with the most number of videos": """
        SELECT c.Channel_Name, COUNT(v.Video_Id) AS Video_Count
        FROM Channels c
        JOIN Videos v ON c.Channel_Id = v.Channel_Id
        GROUP BY c.Channel_Name
        ORDER BY Video_Count DESC;
    """,
    "Top 10 most viewed videos and their channels": """
        SELECT v.Video_Name, c.Channel_Name, v.View_Count
        FROM Videos v
        JOIN Channels c ON v.Channel_Id = c.Channel_Id
        ORDER BY v.View_Count DESC
        LIMIT 10;
    """,
    "How many comments were made on each video, and what are their corresponding video names": """
        SELECT v.Video_Name, COUNT(co.Comment_Id) AS Comment_Count
        FROM Videos v
        JOIN Comments co ON v.Video_Id = co.Video_Id
        GROUP BY v.Video_Name;
    """,
    "Which videos have the highest number of likes, and what are their corresponding channel names": """
        SELECT v.Video_Name, c.Channel_Name, v.Like_Count
        FROM Videos v
        JOIN Channels c ON v.Channel_Id = c.Channel_Id
        ORDER BY v.Like_Count DESC
        LIMIT 10;
    """,
    "What is the total number of likes and dislikes for each video, and what are their corresponding video names": """
        SELECT v.Video_Name, v.Like_Count, v.Dislike_Count
        FROM Videos v;
    """,
    "What is the total number of views for each channel, and what are their corresponding channel names": """
        SELECT c.Channel_Name, SUM(v.View_Count) AS Total_Views
        FROM Channels c
        JOIN Videos v ON c.Channel_Id = v.Channel_Id
        GROUP BY c.Channel_Name;
    """,
    "What are the names of all the channels that have published videos in the year 2022": """
        SELECT DISTINCT c.Channel_Name
        FROM Channels c
        JOIN Videos v ON c.Channel_Id = v.Channel_Id
        WHERE YEAR(v.PublishedAt) = 2022;
    """,
    "What is the average duration of all videos in each channel, and what are their corresponding channel names": """
        SELECT c.Channel_Name, AVG(TIME_TO_SEC(v.Duration)) AS Average_Duration_Sec
        FROM Videos v
        JOIN Channels c ON v.Channel_Id = c.Channel_Id
        GROUP BY c.Channel_Name;
    """,
    "Which videos have the highest number of comments, and what are their corresponding channel names": """
        SELECT v.Video_Name, c.Channel_Name, COUNT(co.Comment_Id) AS Comment_Count
        FROM Videos v
        JOIN Comments co ON v.Video_Id = co.Video_Id
        JOIN Channels c ON v.Channel_Id = c.Channel_Id
        GROUP BY v.Video_Name, c.Channel_Name
        ORDER BY Comment_Count DESC
        LIMIT 10;
    """
}

def fetch_channel_data(channel_id):
    request = youtube.channels().list(
        part="snippet,statistics,contentDetails",
        id=channel_id
    )
    response = request.execute()
    
    if response['items']:
        item = response['items'][0]
        channel_data = {
            'Channel_Id': item['id'],
            'Channel_Name': item['snippet']['title'],
            'Subscription_Count': int(item['statistics'].get('subscriberCount', 0)),
            'Channel_Views': int(item['statistics'].get('viewCount', 0)),
            'Channel_Description': item['snippet'].get('description', ''),
            'Playlist_Id': item['contentDetails'].get('relatedPlaylists', {}).get('uploads', None)
        }
        save_to_database(channel_data, 'Channels')
        return channel_data
    else:
        return None

def fetch_playlists(channel_id):
    request = youtube.playlists().list(
        part="snippet",
        channelId=channel_id,
        maxResults=50
    )
    response = request.execute()
    
    playlists_data = []
    for item in response.get('items', []):
        playlist = {
            'Playlist_Id': item['id'],
            'Channel_Id': channel_id,
            'Playlist_Name': item['snippet']['title'],  
        }
        playlists_data.append(playlist)
        save_to_database(playlist, 'Playlists')
    
    return playlists_data

def fetch_videos(playlist_id):
    request = youtube.playlistItems().list(
        part="snippet,contentDetails",
        playlistId=playlist_id,
        maxResults=50  # Adjust this value as necessary
    )
    response = request.execute()
    
    videos_data = []
    for item in response.get('items', []):
        video_id = item['snippet']['resourceId']['videoId']
        video_details = fetch_video_details(video_id)
        if video_details:
            videos_data.append(video_details)
            save_to_database(video_details, 'Videos')
    
    return videos_data


def fetch_video_details(video_id):
    request = youtube.videos().list(
        part="snippet,statistics,contentDetails",
        id=video_id
    )
    response = request.execute()
    
    if response['items']:
        item = response['items'][0]
        snippet = item['snippet']
        statistics = item['statistics']
        contentDetails = item['contentDetails']

        duration = isodate.parse_duration(contentDetails['duration'])

        video_details = {
            'Video_Id': video_id,
            'Channel_Id': snippet['channelId'],
            'Video_Name': snippet['title'],
            'Video_Description': snippet.get('description', ''),
            'PublishedAt': isodate.parse_datetime(snippet['publishedAt']),
            'View_Count': int(statistics.get('viewCount', 0)),
            'Like_Count': int(statistics.get('likeCount', 0)),
            'Dislike_Count': int(statistics.get('dislikeCount', 0)),
            'Favorite_Count': int(statistics.get('favoriteCount', 0)),
            'Comment_Count': int(statistics.get('commentCount', 0)),
            'Duration': duration,
            'Thumbnail': snippet['thumbnails']['high']['url'],
            'Caption_Status': contentDetails['caption']
        }
        return video_details
    return None


def fetch_comments(video_id):
    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=5,
    )
    response = request.execute()
    
    comments_data = []
    for item in response.get('items', []):
        comment = item['snippet']['topLevelComment']['snippet']
        comment_data = {
            'Comment_Id': item['id'],
            'Video_Id': video_id,
            'Comment_Author': comment['authorDisplayName'],
            'Comment_Text': comment['textDisplay'],
            'Comment_PublishedAt': isodate.parse_datetime(comment['publishedAt'])
        }
        comments_data.append(comment_data)
        save_to_database(comment_data, 'Comments')
    
    return comments_data

def save_to_database(data, table_name):
    session = Session()
    table = metadata.tables[table_name]
    try:
        session.execute(table.insert(), data)
        session.commit()
        st.success(f"Data saved successfully to {table_name}!")
    except SQLAlchemyError as e:
        session.rollback()
        st.error(f"Failed to save data to {table_name} due to: {str(e)}")
    finally:
        session.close()

def query_database(query):
    with engine.connect() as conn:
        result = pd.read_sql(query, conn)
    return result

def fetch_data(channel_id):
    # Fetch channel data and store in the database
    channel_data = fetch_channel_data(channel_id)
    if channel_data:
        save_to_database(channel_data, 'Channels')
        # Fetch playlists related to the channel
        playlists_data = fetch_playlists(channel_id)
        for playlist in playlists_data:
            save_to_database(playlist, 'Playlists')
            # Fetch videos from each playlist
            videos_data = fetch_videos(playlist['Playlist_Id'])
            for video in videos_data:
                save_to_database(video, 'Videos')
                # Fetch comments for each video
                comments_data = fetch_comments(video['Video_Id'])
                for comment in comments_data:
                    save_to_database(comment, 'Comments')
        return True
    return False

def data_loading_page():
    st.header("Data Loading Section")
    st.title("YouTube Channel Data Fetcher and Loader")
    st.text('1.IMAX - UCLOi9fGe5EdPfquSe1RS5aA')
    st.text('2.GreatIndianAsmr - UCovfq4h24UvKIju6kqqNu4A')
    st.text('3.carryminati - UCj22tfcQrWG7EMEKS0qLeEg')
    st.text('4.logos made flesh - UCnctGVeyGLmGeT_6SOQ8cAw')
    st.text('5.Abhi&Niyu - UCsDTy8jvHcwMvSZf_JGi-FA')
    st.text('6.POS - UCE5wDMNEZElnuRDk6TDPOYg')
    st.text('7.CodewithHarry - UCeVMnSShP_Iviwkknt83cww')
    st.text('8.3blue1brown - UCYO_jab_esuFRV4b17AJtAw')
    st.text('9.Varitasium - UCHnyfMqiRRG1u-2MsSQLbXA')
    st.text('10.M Vazquez - UCIaYsNtvYB9cxbUX8Ay3sfQ')
    channel_id = st.text_input("Enter YouTube Channel ID")

    if st.button("Fetch and Load Data"):
        fetch_data(channel_id)  # Assumes fetch_data handles fetching and loading
        st.success("Data successfully fetched and loaded!")

def query_section():
    st.header("Query Section")
    question = st.selectbox("Choose a question:", list(query_mapping.keys()))
    if st.button("Get Answer"):
        result = query_database(query_mapping[question])
        if result.empty:
            st.write("No results found.")
        else:
            st.dataframe(result)

def main():
    st.sidebar.title("Navigation")
    app_mode = st.sidebar.selectbox("Choose the section:",
                                    ["Data Loading", "Query Section"])

    if app_mode == "Data Loading":
        data_loading_page()
    elif app_mode == "Query Section":
        query_section()

if __name__ == "__main__":
    st.set_page_config(page_title="YouTube Data Insights", layout='wide')
    main()
