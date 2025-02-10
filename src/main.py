import logging
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from repository.DBConnector import DBConnector
from src.repository.MemberRepository import MemberRepository
from src.repository.StudyRepository import StudyRepository

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
APPLICATION_ID = os.getenv('APPLICATION_ID')
TEST_GUILD_ID = os.getenv('TEST_GUILD_ID')

discord.utils.setup_logging(level=logging.DEBUG)


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
        logging.info('Loading extensions...')
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')
                logging.info(f'Loaded {filename}')
        logging.info('Load extensions complete')

    async def setup_hook(self):
        await self.load_extensions()
        logging.info('Syncing command tree...')
        # await bot.tree.sync(guild=discord.Object(id=TEST_GUILD_ID))
        await bot.tree.sync()
        logging.info('Command tree sync complete')

    async def on_ready(self):
        logging.info(f'Logged in as {self.user.name} - {self.user.id}')
        game = discord.Game("공부")
        await self.change_presence(status=discord.Status.online, activity=game)


bot = MyBot()

if __name__ == '__main__':
    db_connector = DBConnector()
    db_member_repo = MemberRepository(db_connector)
    db_study_repo = StudyRepository(db_connector)
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        logging.error(e)
