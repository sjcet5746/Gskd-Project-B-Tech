#Multimodal Query Processing and Knowledge Retrieval System -- by G.Srikrishnadevarayulu

import os
import streamlit as st
from googleapiclient.discovery import build
import speech_recognition as sr
import wikipediaapi
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import tempfile
from gtts import gTTS
import requests
import json
import pandas as pd
import altair as alt
from datetime import date
import pickle
import re  
from io import BytesIO
import zipfile
import io
from PIL import Image  # Required for image processing

# Set up YouTube API
API_KEY_YOUTUBE = os.getenv("YT")  # Replace with your YouTube Data API v3 key
youtube = build('youtube', 'v3', developerKey=API_KEY_YOUTUBE)

# Hugging Face Setup
HF_API_KEY = os.getenv("HF_API")
HF_MISTRAL_URL = os.getenv("MISTRAL")

AI_IMAGE_API_KEY = os.getenv("IMG_API")# Hugging Face or RapidAPI key
LOGO_API_KEY = os.getenv("LOGO_API")  # API key for logo generation

def chat_with_mistral_hf(prompt):
    if not HF_API_KEY:
        return "Error: API key not found."
    
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {"inputs": prompt, "parameters": {"max_length": 200, "temperature": 0.7}}
    
    response = requests.post(HF_MISTRAL_URL, json=payload, headers=headers)
    
    if response.status_code == 200:
        return response.json()[0]["generated_text"]
    else:
        return f"Error: {response.json()}"

# Function to search YouTube videos
def search_youtube(query, max_results=5):
    try:
        request = youtube.search().list(
            q=query,
            part='id,snippet',
            maxResults=max_results,
            type='video'
        )
        response = request.execute()
        
        videos = []
        for item in response['items']:
            video_id = item['id']['videoId']
            title = item['snippet']['title']
            thumbnail = item['snippet']['thumbnails']['default']['url']
            url = f'https://www.youtube.com/watch?v={video_id}'
            videos.append({'title': title, 'url': url, 'video_id': video_id, 'thumbnail': thumbnail})
        return videos
    except Exception as e:
        st.write(f"Error fetching videos: {e}")
        return []

# # Function for voice recognition
# # This feature is available only , when running locally 
# def voice_search():
#     recognizer = sr.Recognizer()
#     with sr.Microphone() as source:
#         st.write("Listening...")
#         audio = recognizer.listen(source)
#         try:
#             query = recognizer.recognize_google(audio)
#             st.success(f"You said: {query}")
#             return query
#         except sr.UnknownValueError:
#             st.error("Could not understand audio")
#             return ""
#         except sr.RequestError as e:
#             st.error(f"Could not request results from Google Speech Recognition service; {e}")
#             return ""

# Wikipedia summary function with character limit and summary levels
def get_wikipedia_summary(query, lang_code, char_limit, summary_level):
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
    wiki = wikipediaapi.Wikipedia(language=lang_code, extract_format=wikipediaapi.ExtractFormat.WIKI, user_agent=user_agent)
    page = wiki.page(query)
    if not page.exists():
        return "Page not found."
    if summary_level == "Brief":
        return page.summary[:char_limit]
    elif summary_level == "Detailed":
        return page.summary  # Full summary
    elif summary_level == "Bullet Points":
        points = page.summary.split('. ')
        return '\n'.join(f"- {p.strip()}" for p in points if p)[:char_limit]

# Text-to-speech using gTTS
def text_to_speech(text, filename, lang="en"):
    tts = gTTS(text=text, lang=lang)
    tts.save(filename)
    return filename

# Function to perform Google Search
def google_search(api_key, cse_id, query, num_results=10):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {'key': api_key, 'cx': cse_id, 'q': query, 'num': num_results}
    response = requests.get(url, params=params)
    return response.json()

# Display Google Search Results
def display_google_results(results):
    if "items" in results:
        for item in results['items']:
            st.write(f"**{item['title']}**")
            st.write(item['snippet'])
            st.write(f"[Read more]({item['link']})")
            st.write("---")
    else:
        st.error("No results found.")

# # News Search Function
# def search_news(query, from_date=None, to_date=None):
#     api_key = os.getenv("NEWS_API")  # Replace with your News API key
#     url = f"https://newsapi.org/v2/everything?q={query}&apiKey={api_key}"
#     if from_date and to_date:
#         url += f"&from={from_date}&to={to_date}"
#     response = requests.get(url)
#     return response.json()

# # Display News Results
# def display_news(articles):
#     if "articles" in articles:
#         for article in articles['articles']:
#             st.write(f"**{article['title']}**")
#             st.write(article['description'])
#             st.write(f"[Read more]({article['url']})")
#             st.write("---")
#     else:
#         st.error("No news articles found.")

# News Search Function
# News Search Function
def search_news(query, from_date=None, to_date=None):
    api_key = os.getenv("NEWS_API")  # Replace with your News API key
    url = f"https://newsapi.org/v2/everything?q={query}&apiKey={api_key}"
    if from_date and to_date:
        url += f"&from={from_date}&to={to_date}"
    response = requests.get(url)
    return response.json()

# Display News Results & Collect Images
def display_news(articles):
    image_data = []  # Store image bytes for zip download
    
    if "articles" in articles:
        for index, article in enumerate(articles['articles']):
            st.write(f"**{article['title']}**")
            st.write(article['description'])
            
            if article.get("urlToImage"):
                # Display Image
                st.image(article["urlToImage"], caption="News Image", use_container_width=True)
                
                # Download Individual Image
                img_response = requests.get(article["urlToImage"])
                img_bytes = io.BytesIO(img_response.content)

                st.download_button(
                    label="Download Image 📥",
                    data=img_bytes,
                    file_name=f"news_image_{index + 1}.jpg",
                    mime="image/jpeg",
                    key=f"download_{index}"  # Unique key for each button
                )
                
                # Save Image to List for ZIP Download
                image_data.append((f"news_image_{index + 1}.jpg", img_bytes.getvalue()))
            
            st.write(f"[Read more]({article['url']})")
            st.write("---")
    
    else:
        st.error("No news articles found.")
        return

    # Generate ZIP File if Images Exist
    if image_data:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            for filename, img in image_data:
                zip_file.writestr(filename, img)
        
        zip_buffer.seek(0)

        # Download Button for ZIP File
        st.download_button(
            label="Download All Images as ZIP 📦",
            data=zip_buffer,
            file_name="news_images.zip",
            mime="application/zip"
        )



def convert_youtube_to_mp3(youtube_url):
    API_KEY = os.getenv("YT_API")  # API key from environment variables
    API_URL = "https://youtube-mp310.p.rapidapi.com/download/mp3"
    
    HEADERS = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "youtube-mp310.p.rapidapi.com"
    }
    
    try:
        response = requests.get(API_URL, headers=HEADERS, params={"url": youtube_url})
        
        if response.status_code == 200:
            data = response.json()
            return data.get("downloadUrl", None)
        else:
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error: {e}")
        return None

def extract_urls(data):
    """Recursively extracts all URLs from JSON data."""
    urls = []
    if isinstance(data, dict):
        for key, value in data.items():
            urls.extend(extract_urls(value))
    elif isinstance(data, list):
        for item in data:
            urls.extend(extract_urls(item))
    elif isinstance(data, str):
        if re.search(r"https?://", data):  # Extract any URL
            urls.append(data)
    return urls

def extract_links(obj):
    """Recursively extracts all HTTP links from JSON data"""
    links = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, str) and value.startswith("http"):
                links.append(value)
            elif isinstance(value, (dict, list)):
                links.extend(extract_links(value))
    elif isinstance(obj, list):
        for item in obj:
            links.extend(extract_links(item))
    return links

# File to store shortcut data
DATA_FILE = "shortcuts_data.pkl"

def load_shortcuts():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "rb") as f:
            return pickle.load(f)
    return []

def save_shortcuts(shortcuts):
    with open(DATA_FILE, "wb") as f:
        pickle.dump(shortcuts, f)

if "shortcuts" not in st.session_state:
    st.session_state["shortcuts"] = load_shortcuts()

def main():
    st.set_page_config(page_title="MMQPKRS", layout="wide")

    st.header("Multimodal Query Processing & Knowledge Retrieval System")
    with st.expander("Click to View Shortcuts"):
        if st.session_state.shortcuts:
            num_columns = 4
            cols = st.columns(num_columns)
            DEFAULT_ADMIN_PASSWORD = os.getenv("PASSWORD")
        
            for i, (name, link, icon_data, user_password) in enumerate(st.session_state.shortcuts):
                col = cols[i % num_columns]
                with col:
                    st.image(icon_data, width=100)
                    st.markdown(f"[{name}]({link})", unsafe_allow_html=True)
                
                    password_input_delete = st.text_input("Enter Password to Delete", type="password", key=f"delete_password_{i}")
                    
                    if password_input_delete in [user_password, DEFAULT_ADMIN_PASSWORD]:  
                        if st.button(f"Delete {name}", key=f"delete_{i}"):
                            st.session_state.shortcuts.pop(i)
                            save_shortcuts(st.session_state.shortcuts)
                            st.experimental_rerun()
                    elif password_input_delete:
                        st.warning("Incorrect password. You cannot delete this shortcut.")
        else:
            st.write("No shortcuts added yet.")
    
    st.markdown("Note: Add best web links for student education purposes.")

    if "query" not in st.session_state:
        st.session_state.query = ""

    # Initialize chat history if not present
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # if st.sidebar.button("Voice Search"):
    #     query = voice_search()
    #     if query:
    #         st.session_state.query = query
    # else:
    #     st.session_state.query = ""
    
    # Sidebar options
    st.sidebar.title("Options")
    search_type = st.sidebar.radio("Select Search Type", (
        "Wikipedia", "Google", "YouTube", "News", "Chat",
        "Image Generation", "Logo Generation", "YT MP3", 
        "LinkedIn Details", "Instagram Details", "IMDb Movie Search",
        "Real-Time Image Search" , "NASA Space Data Explorer" , 
        "AI Image Generator" , # Added new option
    ))
    
    # **Add this block after st.sidebar.title("Options")**
    st.sidebar.header("Only Add Best Web Links")
    name = st.sidebar.text_input("Shortcut Name")
    link = st.sidebar.text_input("Website Link (https://...)")
    icon_file = st.sidebar.file_uploader("Upload an Icon", type=["png", "jpg", "jpeg"])
    password_input_add = st.sidebar.text_input("Enter Password to Add Shortcut", type="password")

    if st.sidebar.button("Add Shortcut"):
        if password_input_add: 
            if name and link and icon_file:
                existing_links = [shortcut[1] for shortcut in st.session_state.shortcuts]
                if link in existing_links:
                    st.sidebar.warning("This website already exists.")
                else:
                    st.session_state.shortcuts.append((name, link, icon_file.getvalue(), password_input_add))
                    save_shortcuts(st.session_state.shortcuts)
                    st.sidebar.success(f"Shortcut '{name}' added!")
            else:
                st.sidebar.warning("Please enter all details including an icon.")
        else:
            st.sidebar.warning("Please enter a password to add the shortcut.")

    # Chat-specific sidebar settings
    chat_title = "Temporary Chat"
    if search_type == "Chat":
        chat_title = st.sidebar.text_input("Rename Chat:", "Temporary Chat")

    # Last seen timestamp
    st.sidebar.write(f"Last seen: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if search_type == "Wikipedia":
        lang_map = {"English": "en", "Spanish": "es", "Chinese": "zh", "Hindi": "hi", "Telugu": "te"}
        selected_lang = st.sidebar.selectbox("Wikipedia Language", list(lang_map.keys()))
        summary_levels = ["Brief", "Detailed", "Bullet Points"]
        summary_level = st.sidebar.selectbox("Summarization Level", summary_levels)
        char_limit = st.sidebar.slider("Character Limit", min_value=100, max_value=2000, value=500, step=100)

        st.title("Wikipedia Summary & Text-to-Speech")
        query = st.text_input("Enter a topic to search on Wikipedia:", value=st.session_state.query)

        if query:
            lang_code = lang_map[selected_lang]
            summary = get_wikipedia_summary(query, lang_code, char_limit, summary_level)
            st.markdown(f"### Summary for: {query}")
            st.write(summary)

            tts_filename = f"{query}_speech.mp3"
            if st.button("Play Text-to-Speech"):
                text_to_speech(summary, tts_filename, lang=lang_code)
                st.audio(tts_filename, format="audio/mp3")

        st.write("---")
        st.write("### Footer")
        st.write("This is a Wikipedia search section.")

    elif search_type == "Google":
        st.title("Google Search")
        query = st.text_input("Enter a search query for Google:", value=st.session_state.query)
    
        api_key = os.getenv("G_API")
        cse_id = os.getenv("G_ID")

        if query and st.button("Search"):
            results = google_search(api_key, cse_id, query)
            display_google_results(results)

        st.write("---")
        st.write("### Footer")
        st.write("This is a Google search section.")
    
    elif search_type == "YouTube":
        st.title("YouTube Search")
        query = st.text_input("Enter a topic to search on YouTube:", value=st.session_state.query)
        if query and st.button("Search"):
            videos = search_youtube(query)
            if videos:
                for video in videos:
                    st.write(f"[{video['title']}]({video['url']})")
                    st.image(video['thumbnail'])
                    st.video(video['url'])
                    st.write("---")

        st.write("---")
        st.write("### Footer")
        st.write("This is a YouTube search section.")

    # elif search_type == "News":
    #     st.subheader("Select Date Range")
    #     start_date = st.date_input("From", datetime.date.today() - datetime.timedelta(days=7))
    #     end_date = st.date_input("To", datetime.date.today())
        
    #     st.title("News Search")
    #     query = st.text_input("Enter a news topic to search:", value=st.session_state.query)
    #     if query and st.button("Search"):
    #         articles = search_news(query, start_date, end_date)
    #         display_news(articles)

    #     st.write("---")
    #     st.write("### Footer")
    #     st.write("This is a news search section.")

    elif search_type == "News":
        st.subheader("Select Date Range")
        start_date = st.date_input("From", datetime.date.today() - datetime.timedelta(days=7))
        end_date = st.date_input("To", datetime.date.today())
    
        st.title("News Search")
        query = st.text_input("Enter a news topic to search:", value=st.session_state.query)
        
        if query and st.button("Search"):
            articles = search_news(query, start_date, end_date)
            display_news(articles)
    
        st.write("---")
        st.write("### Footer")
        st.write("This is a news search section.")

    elif search_type == "Chat":
        st.title(chat_title)
        
        for chat in st.session_state.chat_history:
            with st.chat_message(chat["role"]):
                st.write(chat["content"])

        user_input = st.text_input("Ask AI:")
        st.session_state.query = user_input  # Explicitly store the input

        if st.button("Generate Response"):
            if st.session_state.query and st.session_state.query.strip():
                with st.spinner("Generating response..."):
                    response = chat_with_mistral_hf(user_input)
                    
                    st.session_state.chat_history.append({"role": "user", "content": user_input})
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                    st.rerun()
            else:
                st.warning("Please enter a prompt before clicking Generate Response.")

        st.write("---")
        st.write("### Footer")
        st.write("This is a Chat section.")

    elif search_type == "Image Generation":
        st.title("AI Image Generator")
        st.write("Generate AI-powered images using text prompts.")

        prompt = st.text_area("Enter your image description:")
        output_type = st.selectbox("Select output format:", ["png", "jpg"])

        def generate_image():
            url = "https://ai-image-generator14.p.rapidapi.com/"
            headers = {
                "x-rapidapi-key": AI_IMAGE_API_KEY,
                "x-rapidapi-host": "ai-image-generator14.p.rapidapi.com",
                "Content-Type": "application/json"
            }
            payload = {
                "jsonBody": {
                    "function_name": "image_generator",
                    "type": "image_generation",
                    "query": prompt,
                    "output_type": output_type
                }
            }
            response = requests.post(url, json=payload, headers=headers)
            return response.json()

        if st.button("Generate Image"):
            if prompt:
                with st.spinner("Generating image..."):
                    result = generate_image()
                
                    image_url = result.get("message", {}).get("output_png")
                    if image_url:
                        st.image(image_url, caption="Generated Image", use_container_width=True)
                    
                        # Provide download button
                        st.download_button(
                            label="Download Image",
                            data=requests.get(image_url).content,
                            file_name=f"generated_image.{output_type}",
                            mime=f"image/{output_type}"
                        )
                    else:
                        st.error("Failed to generate image. No image URL found in response.")
                        st.write("Response Data:", result)  # Debugging: Show response data
            else:
                st.warning("Please enter an image description.")

        st.write("---")
        st.write("### Footer")
        st.write("This is Image Generation section.")

    elif search_type == "Logo Generation":
        st.title("AI Logo Generator 🎨")
        st.write("Generate a unique logo for your business using AI!")

        # User Inputs
        prompt = st.text_input("Enter a description for the logo:", "Make a logo with the name Gskd")
        style = st.selectbox("Select a Logo Style:", [28, 29, 30], index=0)  # Customize styles if needed
        size = st.radio("Select Image Size:", ["1-1", "2-3", "3-4"], index=0)

        def generate_logo(prompt, style, size):
            api_url = "https://ai-logo-generator.p.rapidapi.com/aaaaaaaaaaaaaaaaaiimagegenerator/quick.php"
            headers = {
                "x-rapidapi-key": LOGO_API_KEY,
                "x-rapidapi-host": "ai-logo-generator.p.rapidapi.com",
                "Content-Type": "application/json"
            }
            payload = {
                "prompt": prompt,
                "style_id": style,
                "size": size
            }
        
            response = requests.post(api_url, json=payload, headers=headers)
            return response.json()

        # Generate button
        if st.button("Generate Logo"):
            with st.spinner("Generating logo... Please wait!"):
                result = generate_logo(prompt, style, size)
            
                # Extracting image URLs from the JSON response
                image_data = result.get("final_result", [])
            
                if image_data:
                    st.subheader("Generated Logo Designs")
                
                    for index, image in enumerate(image_data):
                        image_url = image.get("origin")  # Extracting the logo link
                    
                        if image_url:
                            st.image(image_url, caption=f"Logo Design {index+1}", use_container_width=True)
                        
                            # Download button with a unique key
                            st.download_button(
                                label="Download Logo",
                                data=requests.get(image_url).content,
                                file_name=f"logo_design_{index+1}.webp",
                                mime="image/webp",
                                key=f"download_{index}"  # Unique key to prevent duplicate errors
                            )
                else:
                    st.error("Failed to generate logo. No image URL found.")
                    st.write("Response Data:", result)  # Debugging: Show full response data
        
        st.write("---")
        st.write("### Footer")
        st.write("This is Logo Generation section.")
    
    elif search_type == "YT MP3":
        st.title("🎵 YouTube to MP3 Downloader")
    
        youtube_url = st.text_input("Enter YouTube Video URL:", "https://youtu.be/05TA9jNnCdU?si=1bUk6EHOmwcsKC3H")
    
        if st.button("Convert to MP3"):
            with st.spinner("Processing... Please wait"):
                mp3_url = convert_youtube_to_mp3(youtube_url)
            
                if mp3_url:
                    st.subheader("🔗 MP3 Download Link:")
                    st.markdown(f"[🎶 Click Here to Download MP3]({mp3_url})")
                else:
                    st.warning("⚠️ Failed to retrieve the MP3 file. Please check the YouTube link and try again.")
    
        st.markdown("---")
        st.caption("Powered by Streamlit")

        st.write("---")
        st.write("### Footer")
        st.write("This is YT MP3 section.")

    elif search_type == "LinkedIn Details":
        st.title("🔗 LinkedIn Image Extractor")

        # User input for LinkedIn username
        username = st.text_input("Enter LinkedIn Username", "gskdsrikrishna")

        # Securely fetch API key from Hugging Face Secrets
        api_key = st.secrets["LI_KEY"]

        # API details
        url = "https://linkedin-api8.p.rapidapi.com/"
        headers = {
            "x-rapidapi-key": api_key,  # Secure API key
            "x-rapidapi-host": "linkedin-api8.p.rapidapi.com"
        }

        if st.button("Fetch Data"):
            querystring = {"username": username}
            response = requests.get(url, headers=headers, params=querystring)

            if response.status_code == 200:
                data = response.json()
                st.subheader("Extracted JSON Data")
                st.json(data)  # Display JSON data

                # Extract all URLs from JSON response
                urls = extract_urls(data)
    
                if urls:
                    st.subheader("🔗 Extracted URLs")
                    for url in urls:
                        st.write(url)
    
                    # Download images and create a ZIP file
                    image_files = []
                    zip_buffer = BytesIO()
    
                    with zipfile.ZipFile(zip_buffer, "w") as zipf:
                        for idx, img_url in enumerate(urls):
                            try:
                                img_response = requests.get(img_url, stream=True)
                                if img_response.status_code == 200 and "image" in img_response.headers["Content-Type"]:
                                    img_name = f"image_{idx+1}.jpg"
                                    img_data = img_response.content
                                    with open(img_name, "wb") as img_file:
                                        img_file.write(img_data)
                                    zipf.write(img_name, os.path.basename(img_name))
                                    image_files.append(img_name)
                            except Exception as e:
                                st.error(f"Error downloading {img_url}: {e}")

                    # Provide ZIP download button if images were found
                    if image_files:
                        zip_buffer.seek(0)
                        st.download_button(
                            label="📥 Download All Images as ZIP",
                            data=zip_buffer,
                            file_name="linkedin_images.zip",
                            mime="application/zip"
                        )
                    else:
                        st.warning("No images found in extracted URLs.")
                else:
                    st.warning("No URLs found in the response.")
            else:
                st.error("❌ Failed to fetch data. Check API key or username.")

        st.write("---")
        st.write("### Footer")
        st.write("This is Linkedin Details section.")

    elif search_type == "Instagram Details":
        st.title("📸 Instagram Scraper")
    
        # User Input
        username = st.text_input("Enter Instagram Username:", "gskdsrikrishna")
        
        # Load API Key from Hugging Face Secrets
        API_KEY = os.getenv("INSTA_API")
        HEADERS = {
            "x-rapidapi-key": API_KEY,
            "x-rapidapi-host": "instagram-scraper-api2.p.rapidapi.com"
        }
    
        if st.button("Fetch Details"):
            with st.spinner("Fetching data..."):
                response = requests.get(
                    "https://instagram-scraper-api2.p.rapidapi.com/v1/info",
                    headers=HEADERS,
                    params={"username_or_id_or_url": username}
                )
            
                if response.status_code == 200:
                    data = response.json()
                    st.success("✅ Data Retrieved Successfully!")
                
                    # Display JSON Response
                    st.subheader("📜 JSON Response")
                    st.json(data)
                
                    # Extract links
                    links = extract_links(data)
                
                    # Separate image links
                    image_links = [link for link in links if any(ext in link for ext in [".jpg", ".jpeg", ".png", ".webp"])]
                    other_links = [link for link in links if link not in image_links]
                    
                    # Display Images
                    if image_links:
                        st.subheader("🖼️ Extracted Images:")
                        img_bytes_list = []
                        img_filenames = []
                    
                        for idx, img_url in enumerate(image_links):
                            st.markdown(f"🖼️ [Image {idx + 1}]({img_url})")
                            img_bytes = requests.get(img_url).content
                            img_bytes_list.append(img_bytes)
                            img_filenames.append(f"{username}_image_{idx+1}.jpg")
                    
                    # ZIP Download
                        if img_bytes_list:
                            with io.BytesIO() as zip_buffer:
                                with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                                    for filename, img_data in zip(img_filenames, img_bytes_list):
                                        zip_file.writestr(filename, img_data)
                                zip_buffer.seek(0)
                                st.download_button(
                                    "📥 Download All Images",
                                    data=zip_buffer,
                                    file_name=f"{username}_images.zip",
                                    mime="application/zip"
                                )
                
                    # Display Other Links
                    if other_links:
                        st.subheader("🔗 Other Links:")
                        for link in other_links:
                            st.markdown(f"[🔗 {link}]({link})")
                
                    # Data Downloads
                    st.subheader("⬇️ Download Data")
                    json_data = json.dumps(data, indent=4)
                    text_data = "\n".join(f"{key}: {value}" for key, value in data.items())
                
                    st.download_button(
                        label="Download JSON",
                        data=json_data,
                        file_name=f"{username}_data.json",
                        mime="application/json"
                    )
                
                    st.download_button(
                        label="Download Text",
                        data=text_data,
                        file_name=f"{username}_details.txt",
                        mime="text/plain"
                    )
                
                else:
                    st.error("❌ Failed to retrieve data. Please check the username.")

        st.write("---")
        st.write("### Footer")
        st.write("This is Instagram Details section.")
    
    elif search_type == "IMDb Movie Search":
        st.title("🎬 IMDb Movie Search")

        # User input for movie search
        search_term = st.text_input("Enter Movie Name", "Avengers")

        # Securely fetch API key from Hugging Face Secrets
        api_key = st.secrets["IMDB_KEY"]

        # API details
        url = "https://imdb-com.p.rapidapi.com/search"
        headers = {
            "x-rapidapi-key": api_key,  # Secure API key
            "x-rapidapi-host": "imdb-com.p.rapidapi.com"
        }

        if st.button("🔍 Search"):
            querystring = {"searchTerm": search_term}
            response = requests.get(url, headers=headers, params=querystring)

            if response.status_code == 200:
                data = response.json()
                st.subheader("📜 Extracted JSON Data")
                st.json(data)  # Display JSON data

                # Extract movie details
                if "d" in data:
                    st.subheader("🎥 Search Results")
                    for movie in data["d"]:
                        title = movie.get("l", "Unknown Title")
                        year = movie.get("y", "Unknown Year")
                        imdb_id = movie.get("id", "N/A")
                        poster = movie.get("i", {}).get("imageUrl", "")

                        st.markdown(f"### 🎬 {title} ({year})")
                        st.write(f"**IMDb ID:** `{imdb_id}`")
    
                        if poster:
                            st.image(poster, caption=title, use_column_width=True)

                # Extract all URLs from JSON response
                urls = extract_urls(data)

                if urls:
                    st.subheader("🔗 Extracted URLs")
                    for url in urls:
                        st.write(url)

                    # Download images and create a ZIP file
                    image_files = []
                    zip_buffer = BytesIO()

                    with zipfile.ZipFile(zip_buffer, "w") as zipf:
                        for idx, img_url in enumerate(urls):
                            try:
                                img_response = requests.get(img_url, stream=True)
                                if img_response.status_code == 200 and "image" in img_response.headers["Content-Type"]:
                                    img_name = f"image_{idx+1}.jpg"
                                    img_data = img_response.content
                                    with open(img_name, "wb") as img_file:
                                        img_file.write(img_data)
                                    zipf.write(img_name, os.path.basename(img_name))
                                    image_files.append(img_name)
                            except Exception as e:
                                st.error(f"Error downloading {img_url}: {e}")

                    # Provide ZIP download button if images were found
                    if image_files:
                        zip_buffer.seek(0)
                        st.download_button(
                            label="📥 Download All Images as ZIP",
                            data=zip_buffer,
                            file_name="imdb_images.zip",
                            mime="application/zip"
                        )
                    else:
                        st.warning("No images found in extracted URLs.")
                else:
                    st.warning("No URLs found in the response.")
            else:
                st.error("❌ Failed to fetch data. Check API key or search term.")
                
        st.write("---")
        st.write("### Footer")
        st.write("This is IMDB Movie Search section.")
        
    elif search_type == "Real-Time Image Search":
        st.title("🔎 Real-Time Image Search")

        # User input for image search term
        search_query = st.text_input("Enter Image Search Term", "India")

        # Securely fetch API key from Hugging Face Secrets
        api_key = st.secrets["IMG_KEY"]

        # API details
        url = "https://real-time-image-search.p.rapidapi.com/search"
        headers = {
            "x-rapidapi-key": api_key,  # Secure API key
            "x-rapidapi-host": "real-time-image-search.p.rapidapi.com"
        }

        if st.button("🔍 Search Images"):
            querystring = {
                "query": search_query,
                "limit": "25",
                "size": "any",
                "color": "any",
                "type": "any",
                "time": "any",
                "usage_rights": "any",
                "file_type": "any",
                "aspect_ratio": "any",
                "safe_search": "off",
                "region": ""
            }

            response = requests.get(url, headers=headers, params=querystring)

            if response.status_code == 200:
                data = response.json()
                st.subheader("📜 Extracted JSON Data")
                st.json(data)  # Display JSON data

                # Extract image URLs
                image_urls = extract_urls(data)

                if image_urls:
                    st.subheader("📸 Extracted Image Links")
                    cols = st.columns(3)  # Display images in a 3-column grid

                    for idx, img_url in enumerate(image_urls):
                        cols[idx % 3].image(img_url, width=200, caption=f"Image {idx+1}")

                    # Download images and create a ZIP file
                    image_files = []
                    zip_buffer = BytesIO()

                    with zipfile.ZipFile(zip_buffer, "w") as zipf:
                        for idx, img_url in enumerate(image_urls):
                            try:
                                img_response = requests.get(img_url, stream=True)
                                if img_response.status_code == 200 and "image" in img_response.headers["Content-Type"]:
                                    img_name = f"image_{idx+1}.jpg"
                                    img_data = img_response.content
                                    with open(img_name, "wb") as img_file:
                                        img_file.write(img_data)
                                    zipf.write(img_name, os.path.basename(img_name))
                                    image_files.append(img_name)
                            except Exception as e:
                                st.error(f"Error downloading {img_url}: {e}")

                    # Provide ZIP download button if images were found
                    if image_files:
                        zip_buffer.seek(0)
                        st.download_button(
                            label="📥 Download All Images as ZIP",
                            data=zip_buffer,
                            file_name="searched_images.zip",
                            mime="application/zip"
                        )
                    else:
                        st.warning("No downloadable images found.")
                else:
                    st.warning("No image URLs found in the response.")
            else:
                st.error("❌ Failed to fetch data. Check API key or search term.")

        st.write("---")
        st.write("### Footer")
        st.write("This is Real Time Image Search section.")
    
    elif search_type == "NASA Space Data Explorer":
        st.title("🚀 NASA Space Data Explorer")
    
        # NASA API Key
        NASA_API_KEY = os.getenv("NASA")  # Ensure this is set in your environment
    
        # API Endpoints
        APOD_URL = "https://api.nasa.gov/planetary/apod"
        MARS_ROVER_URL = "https://api.nasa.gov/mars-photos/api/v1/rovers/{}/photos"
        NEO_URL = "https://api.nasa.gov/neo/rest/v1/feed"
        EARTH_IMG_URL = "https://api.nasa.gov/planetary/earth/imagery"
        EPIC_URL = "https://api.nasa.gov/EPIC/api/natural"
        DONKI_URL = "https://api.nasa.gov/DONKI/CME"
        IMAGE_LIBRARY_URL = "https://images-api.nasa.gov/search"
    
        # Helper functions
        def fetch_json(url, params=None):
            """Fetch JSON data from a URL, handling errors."""
            try:
                if params is None:
                    params = {"api_key": NASA_API_KEY}
                response = requests.get(url, params=params)
                response.raise_for_status()  # Raises an error for bad responses (4xx, 5xx)
                return response.json()
            except requests.exceptions.RequestException as e:
                st.error(f"Failed to fetch data: {e}")
                return None
    
        def download_image(image_url, filename):
            """Download image button."""
            response = requests.get(image_url)
            if response.status_code == 200:
                st.download_button(
                    label="Download Image",
                    data=BytesIO(response.content),
                    file_name=filename,
                    mime="image/jpeg"
                )
    
        # Sidebar options for NASA features
        nasa_option = st.sidebar.radio("Select NASA Feature", [
            "Astronomy Picture of the Day",
            "Mars Rover Photos",
            "Near-Earth Object Data",
            "Earth Imagery",
            "EPIC Earth Images",
            "DONKI - Space Weather",
            "NASA Image and Video Library"
        ])
    
        if nasa_option == "Astronomy Picture of the Day":
            st.subheader("📷 Astronomy Picture of the Day")
            response = fetch_json(APOD_URL)
            if response:
                st.image(response['url'], caption=response['title'])
                st.write(response['explanation'])
                download_image(response['url'], "apod.jpg")
    
        elif nasa_option == "Mars Rover Photos":
            st.subheader("🚜 Mars Rover Photos")
            rover = st.selectbox("Choose a rover", ["curiosity", "opportunity", "spirit"])
            sol = st.number_input("Enter Sol (Mars day)", min_value=0, value=1000)
            response = fetch_json(MARS_ROVER_URL.format(rover), params={"sol": sol, "api_key": NASA_API_KEY})
            if response and "photos" in response:
                for idx, photo in enumerate(response["photos"][:5]):
                    st.image(photo['img_src'], caption=f"Taken on {photo['earth_date']}")
                    download_image(photo['img_src'], f"mars_photo_{idx}.jpg")
    
        elif nasa_option == "Near-Earth Object Data":
            st.subheader("☄️ Near-Earth Objects")
            response = fetch_json(NEO_URL, params={"start_date": date.today(), "api_key": NASA_API_KEY})
            if response and "near_earth_objects" in response:
                for neo in response["near_earth_objects"].get(str(date.today()), []):
                    st.write(f"**{neo['name']}** - Diameter: {neo['estimated_diameter']['meters']['estimated_diameter_max']}m")
    
        elif nasa_option == "Earth Imagery":
            st.subheader("🌍 Earth Imagery")
            lat = st.number_input("Enter Latitude", value=37.7749)
            lon = st.number_input("Enter Longitude", value=-122.4194)
            response = fetch_json(EARTH_IMG_URL, params={"lon": lon, "lat": lat, "dim": 0.1, "api_key": NASA_API_KEY})
            if response and 'url' in response:
                st.image(response['url'], caption=f"Satellite Image for ({lat}, {lon})")
                download_image(response['url'], "earth_image.jpg")
    
        elif nasa_option == "EPIC Earth Images":
            st.subheader("🌎 EPIC Earth Images")
            response = fetch_json(EPIC_URL, params={"api_key": NASA_API_KEY})
            if response:
                for img in response[:5]:  # Limit to 5 images
                    year, month, day = img['date'].split()[0].split('-')
                    img_url = f"https://epic.gsfc.nasa.gov/archive/natural/{year}/{month}/{day}/png/{img['image']}.png"
                    st.image(img_url, caption=f"Captured on {img['date']}")
                    download_image(img_url, f"epic_{img['date']}.png")
    
        elif nasa_option == "DONKI - Space Weather":
            st.subheader("🌞 Space Weather Data")
            response = fetch_json(DONKI_URL, params={"api_key": NASA_API_KEY})
            if response:
                for event in response[:5]:  # Limit to 5 events
                    st.write(f"Event: {event.get('note', 'No description available')}")
    
        elif nasa_option == "NASA Image and Video Library":
            st.subheader("📷 NASA Image and Video Library")
            query = st.text_input("Search for images/videos", value="moon")
            response = fetch_json(IMAGE_LIBRARY_URL, params={"q": query, "media_type": "image"})
            if response and "collection" in response:
                for idx, item in enumerate(response["collection"]["items"][:5]):  # Limit to 5 items
                    st.image(item["links"][0]["href"], caption=item["data"][0]["title"])
                    download_image(item["links"][0]["href"], f"nasa_image_{idx}.jpg")

        st.write("---")
        st.write("### Footer")
        st.write("This is NASA section.")

    elif search_type == "AI Image Generator":
        st.title("AI Image Generator 🎨🚀")
        st.write("Enter a prompt below and generate an AI-generated image using Hugging Face!")
    
        # User Input
        prompt = st.text_input("Enter your prompt:", "Astronaut riding a horse")
    
        if st.button("Generate Image"):
            if prompt:
                st.write("Generating image... Please wait ⏳")
                
                # Query Hugging Face API
                API_URL = os.getenv("FLUX")
                headers = {"Authorization": f"Bearer {os.getenv('HF_API')}"}
                
                def query(payload):
                    response = requests.post(API_URL, headers=headers, json=payload)
                    return response.content
    
                image_bytes = query({"inputs": prompt})
    
                # Display Image
                image = Image.open(io.BytesIO(image_bytes))  # Now works because Image is imported
                st.image(image, caption="Generated Image", use_container_width=True)
    
                # Convert Image to Bytes for Download
                img_buffer = io.BytesIO()
                image.save(img_buffer, format="PNG")
                img_buffer.seek(0)

                # Download Button
                st.download_button(
                    label="Download Image 📥",
                    data=img_buffer,
                    file_name="generated_image.png",
                    mime="image/png"
                )
            else:
                st.warning("Please enter a prompt before generating an image.")
    
        # Footer
        st.write("---")
        st.write("Powered by [Hugging Face](https://huggingface.co/) 🚀")
    
if __name__ == "__main__":
    main()

#This project was developed in 2025 by @gskdsrikrishna