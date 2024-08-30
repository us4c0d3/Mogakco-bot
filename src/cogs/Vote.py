import logging
import os
from datetime import timedelta, datetime, timezone, time

import discord
from discord import Poll, app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()

POLL_CHANNEL_ID = os.getenv('POLL_CHANNEL_ID')
VOICE_CHANNEL_ID = os.getenv('VOICE_CHANNEL_ID')
NOTIFICATION_CHANNEL_ID = os.getenv('NOTIFICATION_CHANNEL_ID')
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
        self.vote_channel_id = int(POLL_CHANNEL_ID)
        self.vote_channel = None

        # self.voice_channel_id = int(TEST_VOICE_CHANNEL_ID)
        self.voice_channel_id = int(VOICE_CHANNEL_ID)
        self.voice_channel = None

        self.notification_channel_id = int(NOTIFICATION_CHANNEL_ID)
        self.notification_channel = None

        self.poll_message = None
        self.eight_to_ten_voters = []
        self.ten_to_twelve_voters = []

    @commands.Cog.listener()
    async def on_ready(self):
        self.vote_channel = self.bot.get_channel(self.vote_channel_id)
        self.voice_channel = self.bot.get_channel(self.voice_channel_id)
        self.notification_channel = self.bot.get_channel(self.notification_channel_id)

        if self.vote_channel:
            logging.info(f'Default vote channel set to: {self.vote_channel.name} (ID: {self.vote_channel.id})')
        else:
            logging.warning(f'Channel with ID {self.vote_channel_id} not found.')

        if self.voice_channel:
            logging.info(f'Default voice channel set to: {self.voice_channel.name} (ID: {self.voice_channel.id})')
        else:
            logging.warning(f'Channel with ID {self.voice_channel_id} not found.')

        if self.notification_channel:
            logging.info(f'Default notification channel set to: '
                         f'{self.notification_channel.name} (ID: {self.notification_channel.id})')
        else:
            logging.warning(f'Channel with ID {self.notification_channel_id} not found.')

        self.create_vote.start()
        self.get_voters.start()
        self.alert_eight_to_ten.start()
        self.alert_ten_to_twelve.start()
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
            poll.add_answer(text="20시 ~ 22시 참가", emoji='✅')
            poll.add_answer(text="22시 ~ 24시 참가", emoji='✅')

            # await interaction.response.send_message(poll=poll)
            self.poll_message = await self.vote_channel.send(poll=poll)
            logging.info(f'poll message: {self.poll_message}')
        except Exception as e:
            logging.error(e)

    # 19:30 투표자 취합
    @tasks.loop(time=time(hour=19, minute=30, second=0, tzinfo=KST))
    # @app_commands.command(name='getvoters')
    async def get_voters(self) -> None:
        try:
            message = await self.vote_channel.fetch_message(self.poll_message.id)
            poll = message.poll
            logging.info(f'poll answers: {poll.answers}')

            self.eight_to_ten_voters = [voter async for voter in poll.get_answer(id=1).voters()]
            self.ten_to_twelve_voters = [voter async for voter in poll.get_answer(id=2).voters()]
            logging.info(f'8 ~ 10 투표자: {self.eight_to_ten_voters}')
            logging.info(f'10 ~ 12 투표자: {self.ten_to_twelve_voters}')

            # await interaction.response.send_message(f'8 ~ 10 투표자: {self.eight_to_ten_voters}\n'
            #                                         f'10 ~ 12 투표자: {self.ten_to_twelve_voters}',
            #                                         ephemeral=True)

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

    # @app_commands.command(name='alert_eight')
    @tasks.loop(time=time(hour=20, minute=10, second=0, tzinfo=KST))
    async def alert_eight_to_ten(self) -> None:
        try:
            if self.voice_channel is None or self.notification_channel is None:
                logging.warning("Voice channel 또는 notification channel이 설정되지 않았습니다.")
                return

            voice_channel_members = self.voice_channel.members
            logging.info(f'Voice channel members: {voice_channel_members}')

            not_in_voice = [member for member in self.eight_to_ten_voters if member not in voice_channel_members]
            logging.info(f'Not in voice channel members: {not_in_voice}')

            mentions = ' '.join([f'<@{member.id}>' for member in not_in_voice])
            if len(not_in_voice) != 0:
                await self.notification_channel.send(f'{mentions} 20시 10분 입니다. 혹시 깜빡하셨나요?')
        except Exception as e:
            logging.error(e)

    @tasks.loop(time=time(hour=22, minute=10, second=0, tzinfo=KST))
    async def alert_ten_to_twelve(self) -> None:
        try:
            if self.voice_channel is None or self.notification_channel is None:
                logging.warning("Voice channel 또는 notification channel이 설정되지 않았습니다.")
                return

            voice_channel_members = self.voice_channel.members
            logging.info(f'Voice channel members: {voice_channel_members}')

            not_in_voice = [member for member in self.ten_to_twelve_voters if member not in voice_channel_members]
            logging.info(f'Not in voice channel members: {not_in_voice}')

            mentions = ' '.join([f'<@{member.id}>' for member in not_in_voice])
            if len(not_in_voice) != 0:
                await self.notification_channel.send(f'{mentions} 22시 10분 입니다. 혹시 깜빡하셨나요?')
        except Exception as e:
            logging.error(e)


async def setup(bot) -> None:
    # await bot.add_cog(Vote(bot), guild=discord.Object(id=TEST_GUILD_ID))
    await bot.add_cog(Vote(bot))
