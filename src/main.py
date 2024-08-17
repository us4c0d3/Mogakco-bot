import logging
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

logger = logging.getLogger('MogakcoBot')
logger.setLevel(logging.INFO)

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
APPLICATION_ID = os.getenv('APPLICATION_ID')
TEST_GUILD_ID = os.getenv('TEST_GUILD_ID')


class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        intents.polls = True

        super().__init__(
            command_prefix="!",
            intents=intents,
            sync_command=True,
            application_id=APPLICATION_ID
        )

    async def load_extensions(self):
        logger.info('Loading extensions...')
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')
                logger.info(f'Loaded {filename}')
        logger.info('Load extensions complete')

    async def setup_hook(self):
        await self.load_extensions()
        logger.info('Syncing command tree...')
        await bot.tree.sync(guild=discord.Object(id=TEST_GUILD_ID))
        # await bot.tree.sync()
        logger.info('Command tree sync complete')

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}, ID: {self.user.id}')
        game = discord.Game("...")
        await self.change_presence(status=discord.Status.online, activity=game)


bot = MyBot()

if __name__ == '__main__':
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        logger.error(e)
