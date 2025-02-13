import logging
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from repository.DBConnector import DBConnector
from repository.MemberRepository import MemberRepository
from repository.StudyRepository import StudyRepository
from service.AlertService import AlertService
from service.StudyService import StudyService

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
APPLICATION_ID = os.getenv('APPLICATION_ID')
TEST_GUILD_ID = os.getenv('TEST_GUILD_ID')
PARTICIPANT_ID = int(os.getenv('PARTICIPANT_ID'))

discord.utils.setup_logging(level=logging.DEBUG)


class MyBot(commands.Bot):
    def __init__(self, alert_service: AlertService):
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

        self.alert_service = alert_service

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
    member_repo = MemberRepository(db_connector)
    study_repo = StudyRepository(db_connector)
    study_service = StudyService(member_repo, study_repo)
    alert_service = AlertService(participant_role_id=PARTICIPANT_ID, study_service=study_service)
    bot = MyBot(alert_service)
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        logging.error(e)
