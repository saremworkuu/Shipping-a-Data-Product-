"""
Telegram Scraper for Medical Channels

This script scrapes messages and images from public Telegram channels
related to Ethiopian medical businesses and stores them in a data lake.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import asyncio

from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_ID = int(os.getenv("TELEGRAM_API_ID", ""))
API_HASH = os.getenv("TELEGRAM_API_HASH", "")
PHONE_NUMBER = os.getenv("TELEGRAM_PHONE_NUMBER", "")

# Channels to scrape
CHANNELS = [
    "CheMed123",  # CheMed Telegram Channel
    "lobelia4cosmetics",  # Lobelia Cosmetics
    "TikvahPharma",  # Tikvah Pharma
]

# Data lake paths
BASE_DIR = Path(__file__).parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
IMAGES_DIR = RAW_DATA_DIR / "images"
LOGS_DIR = BASE_DIR / "logs"

# Setup logging
LOGS_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / f"scraper_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TelegramScraper:
    """Scrapes Telegram channels for medical product data."""
    
    def __init__(self, api_id: int, api_hash: str, phone_number: str):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        self.client = None
        
    async def connect(self):
        """Connect to Telegram API."""
        try:
            self.client = TelegramClient('session_name', self.api_id, self.api_hash)
            await self.client.start(self.phone_number)
            logger.info("Successfully connected to Telegram")
        except Exception as e:
            logger.error(f"Failed to connect to Telegram: {e}")
            raise
    
    async def scrape_channel(self, channel_name: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Scrape messages from a specific Telegram channel.
        
        Args:
            channel_name: Name of the Telegram channel
            limit: Maximum number of messages to scrape
            
        Returns:
            List of message dictionaries
        """
        messages_data = []
        logger.info(f"Starting to scrape channel: {channel_name}")
        
        try:
            # Get channel entity
            entity = await self.client.get_entity(channel_name)
            
            # Iterate through messages
            async for message in self.client.iter_messages(entity, limit=limit):
                if message is None or message.text is None:
                    continue
                
                message_data = {
                    "message_id": message.id,
                    "channel_name": channel_name,
                    "message_date": message.date.isoformat() if message.date else None,
                    "message_text": message.text,
                    "has_media": message.media is not None,
                    "views": message.views if message.views else 0,
                    "forwards": message.forwards if message.forwards else 0,
                }
                
                # Download image if present
                if message.media and isinstance(message.media, MessageMediaPhoto):
                    image_path = await self.download_image(message, channel_name)
                    message_data["image_path"] = image_path
                else:
                    message_data["image_path"] = None
                
                messages_data.append(message_data)
                
            logger.info(f"Scraped {len(messages_data)} messages from {channel_name}")
            return messages_data
            
        except Exception as e:
            logger.error(f"Error scraping channel {channel_name}: {e}")
            return []
    
    async def download_image(self, message, channel_name: str) -> str:
        """
        Download image from a message.
        
        Args:
            message: Telegram message object
            channel_name: Name of the channel
            
        Returns:
            Path to downloaded image
        """
        try:
            # Create channel-specific image directory
            channel_image_dir = IMAGES_DIR / channel_name
            channel_image_dir.mkdir(parents=True, exist_ok=True)
            
            # Download image
            image_path = channel_image_dir / f"{message.id}.jpg"
            await message.download_media(file=str(image_path))
            
            logger.debug(f"Downloaded image: {image_path}")
            return str(image_path)
            
        except Exception as e:
            logger.error(f"Error downloading image for message {message.id}: {e}")
            return None
    
    def save_to_data_lake(self, messages_data: List[Dict[str, Any]], channel_name: str):
        """
        Save scraped messages to data lake as JSON.
        
        Args:
            messages_data: List of message dictionaries
            channel_name: Name of the channel
        """
        try:
            # Create date-specific directory
            date_str = datetime.now().strftime("%Y-%m-%d")
            date_dir = RAW_DATA_DIR / "telegram_messages" / date_str
            date_dir.mkdir(parents=True, exist_ok=True)
            
            # Save to JSON file
            output_file = date_dir / f"{channel_name}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(messages_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved {len(messages_data)} messages to {output_file}")
            
        except Exception as e:
            logger.error(f"Error saving to data lake: {e}")
            raise
    
    async def scrape_all_channels(self, channels: List[str], limit: int = 1000):
        """
        Scrape all specified channels.
        
        Args:
            channels: List of channel names to scrape
            limit: Maximum messages per channel
        """
        # Create necessary directories
        RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
        IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        
        await self.connect()
        
        for channel in channels:
            try:
                messages = await self.scrape_channel(channel, limit)
                if messages:
                    self.save_to_data_lake(messages, channel)
            except Exception as e:
                logger.error(f"Failed to scrape {channel}: {e}")
                continue
        
        await self.client.disconnect()
        logger.info("Scraping completed for all channels")


async def main():
    """Main entry point for the scraper."""
    if not API_ID or not API_HASH:
        logger.error("TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in .env file")
        return
    
    scraper = TelegramScraper(API_ID, API_HASH, PHONE_NUMBER)
    await scraper.scrape_all_channels(CHANNELS, limit=1000)


if __name__ == "__main__":
    asyncio.run(main())
