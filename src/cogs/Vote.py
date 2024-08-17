import os
from datetime import timedelta, datetime, timezone, time

import discord
from discord import Poll, app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv

from src.main import logger

load_dotenv()

POLL_CHANNEL_ID = os.getenv('POLL_CHANNEL_ID')
TEST_CHANNEL_ID = os.getenv('TEST_CHANNEL_ID')
TEST_GUILD_ID = os.getenv('TEST_GUILD_ID')

KST = timezone(timedelta(hours=9))


class Vote(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.channel = None

    @commands.Cog.listener()
    async def on_ready(self):
        self.create_vote.start()
        logger.info('Vote.py is ready')

    @tasks.loop(time=time(hour=10, minute=0, second=0, tzinfo=KST))
    async def create_vote(self) -> None:
        logger.info('투표 생성')
        if self.channel is None:
            logger.info('투표 채널이 설정되지 않았습니다.')
            return

        try:
            today = datetime.today()
            question = f"{today.month}월 {today.day}일 참여 투표"
            duration = timedelta(hours=10)
            poll = Poll(question=question, duration=duration)
            poll.add_answer(text="참가", emoji='✅')
            poll.add_answer(text="불참", emoji='❌')

            await self.channel.send(poll=poll)
        except Exception as e:
            print(e)

    @app_commands.command(name='votechannel', description='투표를 올릴 채널을 설정합니다')
    async def set_channel(self, interaction: discord.Interaction) -> None:
        self.channel = interaction.channel
        print(f'Vote channel set to: {self.channel}')
        print(f'Vote channel id: {self.channel.id}')
        print(f'Vote channel name: {self.channel.name}')
        await interaction.response.send_message("투표 채널이 설정되었습니다.")


async def setup(bot) -> None:
    await bot.add_cog(Vote(bot))
