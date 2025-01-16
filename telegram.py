from telethon import TelegramClient
import csv
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import asyncio

# Constants
BATCH_SIZE = 100
DELAY = 1  # seconds between batches

# Load environment variables
load_dotenv()

api_id = int(os.getenv('TG_API_ID').strip())
api_hash = os.getenv('TG_API_HASH').strip()
phone = os.getenv('phone').strip()

# Function to process a batch of messages
async def process_message_batch(client, messages, writer, media_dir, channel_title, channel_username):
    for message in messages:
        try:
            # Skip if message is empty or None
            if not message.message or message.message.strip() == "":
                continue
                
            media_path = None
            if message.media and hasattr(message.media, 'photo'):
                filename = f"{channel_username}_{message.id}.jpg"
                media_path = os.path.join(media_dir, filename)
                await client.download_media(message.media, media_path)

            writer.writerow([
                channel_title,
                channel_username,
                message.id,
                message.message,
                message.date,
                media_path
            ])
        except Exception as msg_error:
            print(f"Error processing message {message.id} from {channel_username}: {msg_error}")
            continue

# Function to scrape data from a single channel
async def scrape_channel(client, channel_username, writer, media_dir):
    try:
        entity = await client.get_entity(channel_username)
        channel_title = entity.title
        
        messages_batch = []
        async for message in client.iter_messages(
            entity,
            limit=1500,
            reverse=True
        ):
            messages_batch.append(message)
            
            if len(messages_batch) >= BATCH_SIZE:
                await process_message_batch(client, messages_batch, writer, media_dir, 
                                         channel_title, channel_username)
                messages_batch = []
                await asyncio.sleep(DELAY)
        
        # Process remaining messages
        if messages_batch:
            await process_message_batch(client, messages_batch, writer, media_dir, 
                                     channel_title, channel_username)
                
    except Exception as e:
        print(f"Error scraping channel {channel_username}: {e}")
        return

async def main():
    # Start the client and authenticate the user
    client = TelegramClient('scraping_session', api_id, api_hash)
    await client.start(phone=phone)

    # Create a directory for media files
    media_dir = 'photos'
    os.makedirs(media_dir, exist_ok=True)

    # Open the CSV file and prepare the writer
    with open('telegram_data.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([
            'Channel Title', 'Channel Username', 'ID', 'Message', 'Date', 'Media Path'
        ])

        # List of channels to scrape
        channels = [
            '@MerttEka',
            '@qnashcom',
            '@helloomarketethiopia',
            '@AwasMart',
            '@ZemenExpress',
        ]

        # Create tasks for all channels
        tasks = [scrape_channel(client, channel, writer, media_dir) for channel in channels]
        
        # Run all tasks concurrently
        await asyncio.gather(*tasks)
        
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
