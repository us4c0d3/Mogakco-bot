import os
from datetime import timedelta, datetime, time

import discord
from discord import Poll, app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

POLL_CHANNEL_ID = os.getenv('POLL_CHANNEL_ID')
TEST_CHANNEL_ID = os.getenv('TEST_CHANNEL_ID')
TEST_GUILD_ID = os.getenv('TEST_GUILD_ID')


class Vote(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @app_commands.command(name='vote', description='Poll a question')
    async def create_vote(self, interaction: discord.Interaction) -> None:
        try:
            today = datetime.today()
            creation_time = datetime.combine(today, time(hour=10))
            question = f"{today.month}월 {today.day}일 참여 투표"
            duration = timedelta(hours=10)
            poll = Poll(question=question, duration=duration)
            poll.add_answer(text="참가", emoji='✅')
            poll.add_answer(text="불참", emoji='❌')
            # poll.created_at = creation_time

            await interaction.response.send_message(poll=poll)
        except Exception as e:
            print(e)


async def setup(bot) -> None:
    await bot.add_cog(Vote(bot))
