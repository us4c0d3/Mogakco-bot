import logging
import os
from datetime import timedelta, datetime, timezone, time

import discord
from discord import Poll, app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()

VOTE_CHANNEL_ID = os.getenv('VOTE_CHANNEL_ID')
VOICE_CHANNEL_ID = os.getenv('VOICE_CHANNEL_ID')
ATTENDANCE_CHANNEL_ID = os.getenv('ATTENDANCE_CHANNEL_ID')
TEST_POLL_CHANNEL_ID = os.getenv('TEST_POLL_CHANNEL_ID')
TEST_VOICE_CHANNEL_ID = os.getenv('TEST_VOICE_CHANNEL_ID')
TEST_GUILD_ID = os.getenv('TEST_GUILD_ID')

KST = timezone(timedelta(hours=9))


def is_channel_admin(interaction: discord.Interaction) -> bool:
    return interaction.user.guild_permissions.administrator


class Vote(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

        # self.vote_channel_id = int(TEST_POLL_CHANNEL_ID)
        self.vote_channel_id = int(VOTE_CHANNEL_ID)
        self.vote_channel = None

        self.poll_message = None

    @commands.Cog.listener()
    async def on_ready(self):
        self.vote_channel = self.bot.get_channel(self.vote_channel_id)

        if self.vote_channel:
            logging.info(f'Default vote channel set to: {self.vote_channel.name} (ID: {self.vote_channel.id})')
        else:
            logging.warning(f'Channel with ID {self.vote_channel_id} not found.')

        self.create_vote.start()
        self.get_voters.start()

        logging.info('Vote.py is ready')

    @tasks.loop(time=time(hour=9, minute=0, second=0, tzinfo=KST))
    # @app_commands.command(name='vote')
    async def create_vote(self) -> None:
        logging.info('투표 생성')
        if self.vote_channel is None:
            logging.warning('투표 채널이 설정되지 않았습니다.')
            return

        try:
            today = datetime.today()
            question = f"{today.month}월 {today.day}일 참여 투표"
            duration = timedelta(hours=10)
            poll = Poll(question=question, duration=duration, multiple=True)
            poll.add_answer(text="참가", emoji='✅')
            poll.add_answer(text="불참", emoji='❌')

            # await interaction.response.send_message(poll=poll)
            # self.poll_message = await interaction.original_response()
            self.poll_message = await self.vote_channel.send(poll=poll)
            logging.info(f'poll message: {self.poll_message}')

        except Exception as e:
            logging.error(e)

    # 19:20 투표자 취합
    @tasks.loop(time=time(hour=19, minute=20, second=0, tzinfo=KST))
    # @app_commands.command(name='getvoters', description='투표자 취합')
    async def get_voters(self) -> None:
        try:
            message = await self.vote_channel.fetch_message(self.poll_message.id)
            poll = message.poll
            logging.info(f'poll answers: {poll.answers}')

            attend_voters = [voter async for voter in poll.get_answer(id=1).voters()]
            logging.info(f'참가 투표자: {attend_voters}')

            alert_cog = self.bot.get_cog('Alert')
            if alert_cog:
                alert_cog.update_voters(attend_voters)

        except Exception as e:
            logging.error(e)

    # 테스트용 투표 강제 종료
    @app_commands.command(name='endvote')
    @app_commands.check(is_channel_admin)
    async def end_vote(self, interaction: discord.Interaction) -> None:
        try:
            message = await interaction.channel.fetch_message(self.poll_message.id)
            await message.end_poll()
            logging.info('투표를 종료시켰습니다.')
            await interaction.response.send_message('투표를 종료시켰습니다.', ephemeral=True)
        except Exception as e:
            logging.error(e)


async def setup(bot) -> None:
    # await bot.add_cog(Vote(bot), guild=discord.Object(id=TEST_GUILD_ID))
    await bot.add_cog(Vote(bot))
