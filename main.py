import os
import tempfile
import requests
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from torrentool.api import Torrent
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from google.oauth2 import service_account
import json
import shutil
import re

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Get Telegram Bot Token from .env file
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Google Drive API credentials
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# Get the service account info from environment variable
SERVICE_ACCOUNT_INFO = os.getenv('GOOGLE_SERVICE_ACCOUNT_INFO')
if not SERVICE_ACCOUNT_INFO:
    raise ValueError("GOOGLE_SERVICE_ACCOUNT_INFO environment variable is not set")

try:
    SERVICE_ACCOUNT_INFO = json.loads(SERVICE_ACCOUNT_INFO)
except json.JSONDecodeError:
    raise ValueError("GOOGLE_SERVICE_ACCOUNT_INFO is not valid JSON")

# Create a temporary directory in the project folder
TEMP_DIR = os.path.join(os.path.dirname(__file__), 'temp_downloads')
os.makedirs(TEMP_DIR, exist_ok=True)

def download_from_gdrive(service, file_id, output_path):
    request = service.files().get_media(fileId=file_id)
    with open(output_path, 'wb') as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            logger.debug(f"Download {int(status.progress() * 100)}% complete")
    logger.info(f"File downloaded from Google Drive to {output_path}")

def process_gdrive_item(service, item_id, output_dir):
    try:
        item = service.files().get(fileId=item_id, fields="id, name, mimeType").execute()
    except Exception as e:
        logger.error(f"Error getting file/folder info: {str(e)}")
        raise

    if item['mimeType'] == 'application/vnd.google-apps.folder':
        folder_path = os.path.join(output_dir, item['name'])
        os.makedirs(folder_path, exist_ok=True)
        
        page_token = None
        while True:
            try:
                results = service.files().list(
                    q=f"'{item_id}' in parents",
                    fields="nextPageToken, files(id, name, mimeType)",
                    pageToken=page_token
                ).execute()
                
                for file in results.get('files', []):
                    process_gdrive_item(service, file['id'], folder_path)
                
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
            except Exception as e:
                logger.error(f"Error listing files in folder: {str(e)}")
                raise
    else:
        file_path = os.path.join(output_dir, item['name'])
        download_from_gdrive(service, item_id, file_path)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"User {update.effective_user.id} started the bot")
    await update.message.reply_text('Welcome! Send me a file, Google Drive link, or .nzb file to convert to .torrent.')

async def convert_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"User {update.effective_user.id} requested file conversion")
    file = await update.message.document.get_file()
    conversion_dir = tempfile.mkdtemp(dir=TEMP_DIR)
    file_path = os.path.join(conversion_dir, update.message.document.file_name)
    await file.download_to_drive(file_path)
    logger.debug(f"File downloaded to {file_path}")
    torrent = Torrent.create_from(file_path)
    torrent_path = f"{file_path}.torrent"
    torrent.to_file(torrent_path)
    logger.debug(f"Torrent file created at {torrent_path}")
    
    with open(torrent_path, 'rb') as torrent_file:
        await update.message.reply_document(torrent_file)
    
    await update.message.reply_text(f"Torrent created and original file saved in: {conversion_dir}")

async def convert_gdrive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"User {update.effective_user.id} requested Google Drive conversion")
    gdrive_link = update.message.text
    conversion_dir = tempfile.mkdtemp(dir=TEMP_DIR)
    
    try:
        credentials = service_account.Credentials.from_service_account_info(
            SERVICE_ACCOUNT_INFO, scopes=SCOPES)
        service = build('drive', 'v3', credentials=credentials)
        
        # Extract file/folder ID from the Google Drive link
        match = re.search(r'(/d/|/folders/)([a-zA-Z0-9-_]+)', gdrive_link)
        if not match:
            raise ValueError("Invalid Google Drive link")
        item_id = match.group(2)
        
        process_gdrive_item(service, item_id, conversion_dir)
        
        torrent = Torrent.create_from(conversion_dir)
        torrent_path = os.path.join(conversion_dir, "output.torrent")
        torrent.to_file(torrent_path)
        
        with open(torrent_path, 'rb') as torrent_file:
            await update.message.reply_document(torrent_file)
        
        logging.info(f"Torrent created and files saved in: {conversion_dir}")
    
    except Exception as e:
        logger.error(f"Error processing Google Drive link: {str(e)}")
        shutil.rmtree(conversion_dir, ignore_errors=True)

def main() -> None:
    logger.info("Starting the bot")
    application = Application.builder().token(TOKEN).build()
    logger.info("Application built")

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, convert_file))
    application.add_handler(MessageHandler(filters.Regex(r'https?://drive\.google\.com/\S+'), convert_gdrive))
    logger.info("Handlers added")

    logger.info("Bot is ready to handle requests")
    application.run_polling()
    logger.info("Bot has stopped")

if __name__ == '__main__':
    logger.info("Script is running")
    main()
