import os
import logging
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder
from bot_runner import BotRunner

# Import config functions from each bot
from bots.asha.config import get_asha_config
from bots.priya.config import get_priya_config
from bots.zara.config import get_zara_config
from bots.ritika.config import get_ritika_config

load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Get bot configurations from their respective config files
BOT_CONFIGS = {
    'asha': get_asha_config(),
    'priya': get_priya_config(),
    'zara': get_zara_config(),
    'ritika': get_ritika_config()
}

async def post_init(application):
    """Called after the application is initialized"""
    logging.info(f"Bot {application.bot.username} is ready!")

if __name__ == '__main__':
    # Create bot runners
    bot_runners = []
    applications = []
    
    for bot_key, config in BOT_CONFIGS.items():
        if not config['token']:
            logging.warning(f"⚠️  Token not found for {config['name']} bot - skipping")
            continue
        
        logging.info(f"🚀 Initializing {config['name']} bot...")
        runner = BotRunner(config)
        application = runner.run()
        
        if application:
            bot_runners.append(runner)
            applications.append(application)
            logging.info(f"✅ {config['name']} bot initialized successfully")
    
    if not applications:
        logging.error("❌ No bots were initialized. Check your .env file!")
        exit(1)
    
    # Run all bots together
    logging.info(f"\n🎉 Starting {len(applications)} bot(s)...\n")
    
    # Use the first application to run polling for all
    import asyncio
    from telegram.ext import ApplicationBuilder
    
    async def run_all_bots():
        """Initialize and run all bots concurrently"""
        # Initialize all applications
        await asyncio.gather(*[app.initialize() for app in applications])
        
        # Start all applications
        await asyncio.gather(*[app.start() for app in applications])
        
        # Start polling for all applications
        await asyncio.gather(*[app.updater.start_polling() for app in applications])
        
        logging.info("✅ All bots are now running!")
        
        # Keep running until interrupted
        try:
            await asyncio.Event().wait()
        finally:
            # Cleanup
            await asyncio.gather(*[app.updater.stop() for app in applications])
            await asyncio.gather(*[app.stop() for app in applications])
            await asyncio.gather(*[app.shutdown() for app in applications])
    
    # Run the async function
    asyncio.run(run_all_bots())