import logging
import os
from datetime import timedelta, datetime, timezone, time

import discord
from discord import Poll, app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()

POLL_CHANNEL_ID = os.getenv('POLL_CHANNEL_ID')
TEST_CHANNEL_ID = os.getenv('TEST_CHANNEL_ID')
TEST_GUILD_ID = os.getenv('TEST_GUILD_ID')

KST = timezone(timedelta(hours=9))


class Vote(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.channel_id = int(POLL_CHANNEL_ID)
        self.channel = None
        self.poll = None

    @commands.Cog.listener()
    async def on_ready(self):
        self.channel = self.bot.get_channel(self.channel_id)

        if self.channel:
            logging.info(f'Default vote channel set to: {self.channel.name} (ID: {self.channel.id})')
        else:
            logging.warning(f'Channel with ID {self.channel_id} not found.')

        self.create_vote.start()
        logging.info('Vote.py is ready')

    @tasks.loop(time=time(hour=9, minute=0, second=0, tzinfo=KST))
    async def create_vote(self) -> None:
        logging.info('투표 생성')
        if self.channel is None:
            logging.warning('투표 채널이 설정되지 않았습니다.')
            return

        try:
            today = datetime.today()
            question = f"{today.month}월 {today.day}일 참여 투표"
            duration = timedelta(hours=10)
            poll = Poll(question=question, duration=duration)
            poll.add_answer(text="8시 ~ 10시 참가", emoji='✅')
            poll.add_answer(text="10시 ~ 12시 참가", emoji='✅')

            await self.channel.send(poll=poll)
        except Exception as e:
            logging.error(e)

    @app_commands.command(name='votechannel', description='투표를 올릴 채널을 설정합니다')
    async def set_channel(self, interaction: discord.Interaction) -> None:
        self.channel = interaction.channel
        logging.info(f'Vote channel set to: {self.channel}')
        logging.info(f'Vote channel id: {self.channel.id}')
        logging.info(f'Vote channel name: {self.channel.name}')
        await interaction.response.send_message("투표 채널이 설정되었습니다.")


async def setup(bot) -> None:
    await bot.add_cog(Vote(bot))
