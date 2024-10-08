import logging
import os
from datetime import timedelta, timezone, time

import discord
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()

VOTE_CHANNEL_ID = os.getenv('VOTE_CHANNEL_ID')
VOICE_CHANNEL_ID = os.getenv('VOICE_CHANNEL_ID')
ATTENDANCE_CHANNEL_ID = os.getenv('ATTENDANCE_CHANNEL_ID')
TEST_GUILD_ID = os.getenv('TEST_GUILD_ID')

KST = timezone(timedelta(hours=9))


class Alert(commands.Cog):
    """
    알림 관련 타임라인
    18:30 투표 마감 30분 전 알림
    19:20 투표자 취합
    19:30 20시 참가자 30분 전 알림
    20:10 지각자 알림
    21:30 22시 참가자 30분 전 알림
    22:10 지각자 알림
    """
    def __init__(self, bot) -> None:
        self.bot = bot

        self.vote_channel_id = int(VOTE_CHANNEL_ID)
        self.vote_channel = None

        self.voice_channel_id = int(VOICE_CHANNEL_ID)
        self.voice_channel = None

        self.attendance_channel_id = int(ATTENDANCE_CHANNEL_ID)
        self.attendance_channel = None

        self.eight_to_ten_voters = []
        self.ten_to_twelve_voters = []

    @commands.Cog.listener()
    async def on_ready(self):
        self.vote_channel = self.bot.get_channel(self.vote_channel_id)
        self.voice_channel = self.bot.get_channel(self.voice_channel_id)
        self.attendance_channel = self.bot.get_channel(self.attendance_channel_id)

        if self.vote_channel:
            logging.info(f'Default vote channel set to: {self.vote_channel.name} (ID: {self.vote_channel.id})')
        else:
            logging.warning(f'Channel with ID {self.vote_channel_id} not found.')

        if self.voice_channel:
            logging.info(f'Default voice channel set to: {self.voice_channel.name} (ID: {self.voice_channel.id})')
        else:
            logging.warning(f'Channel with ID {self.voice_channel_id} not found.')

        if self.attendance_channel:
            logging.info(f'Default attendance channel set to: '
                         f'{self.attendance_channel.name} (ID: {self.attendance_channel.id})')
        else:
            logging.warning(f'Channel with ID {self.attendance_channel_id} not found.')

        self.alert_vote_end.start()
        self.alert_attendance_eight.start()
        self.alert_eight_to_ten.start()
        self.alert_attendance_ten.start()
        self.alert_ten_to_twelve.start()

        logging.info('Alert.py is ready')

    # 18:30 투표 마감 30분 전 알림
    @tasks.loop(time=time(hour=18, minute=30, second=0, tzinfo=KST))
    async def alert_vote_end(self) -> None:
        try:
            if self.vote_channel is None:
                logging.warning(f'Vote channel not set.')
                return

            await self.vote_channel.send('@everyone 투표 마감 30분 전입니다!')

        except Exception as e:
            logging.error(e)

    # 19:20 투표자 취합
    def update_voters(self, eight_to_ten_voters, ten_to_twelve_voters):
        self.eight_to_ten_voters = eight_to_ten_voters
        self.ten_to_twelve_voters = ten_to_twelve_voters

    # 19:30 20시 참가자 30분 전 알림
    @tasks.loop(time=time(hour=19, minute=30, second=0, tzinfo=KST))
    async def alert_attendance_eight(self) -> None:
        if len(self.eight_to_ten_voters) == 0:
            logging.info('eight_to_ten_voters is empty')
            return

        mentions = ' '.join([f'<@{member.id}>' for member in self.eight_to_ten_voters])
        await self.attendance_channel.send(f'{mentions} 20시 모각코 30분 전입니다!')

    # 20:10 지각자 알림
    @tasks.loop(time=time(hour=20, minute=10, second=0, tzinfo=KST))
    async def alert_eight_to_ten(self) -> None:
        try:
            if self.voice_channel is None or self.attendance_channel is None:
                logging.warning("Voice channel 또는 notification channel이 설정되지 않았습니다.")
                return

            voice_channel_members = self.voice_channel.members
            logging.info(f'Voice channel members: {voice_channel_members}')

            not_in_voice = [member for member in self.eight_to_ten_voters if member not in voice_channel_members]
            logging.info(f'Not in voice channel members: {not_in_voice}')

            mentions = ' '.join([f'<@{member.id}>' for member in not_in_voice])
            if len(not_in_voice) != 0:
                await self.attendance_channel.send(f'{mentions} 20시 10분 입니다. 혹시 깜빡하셨나요?')
        except Exception as e:
            logging.error(e)

    # 21:30 22시 참가자 30분 전 알림
    @tasks.loop(time=time(hour=21, minute=30, second=0, tzinfo=KST))
    async def alert_attendance_ten(self) -> None:
        if len(self.ten_to_twelve_voters) == 0:
            logging.info('ten_to_twelve_voters is empty')
            return

        mentions = ' '.join([f'<@{member.id}>' for member in self.ten_to_twelve_voters])
        await self.attendance_channel.send(f'{mentions} 22시 모각코 30분 전입니다!')

    # 22:10 지각자 알림
    @tasks.loop(time=time(hour=22, minute=10, second=0, tzinfo=KST))
    async def alert_ten_to_twelve(self) -> None:
        try:
            if self.voice_channel is None or self.attendance_channel is None:
                logging.warning("Voice channel 또는 notification channel이 설정되지 않았습니다.")
                return

            voice_channel_members = self.voice_channel.members
            logging.info(f'Voice channel members: {voice_channel_members}')

            not_in_voice = [member for member in self.ten_to_twelve_voters if member not in voice_channel_members]
            logging.info(f'Not in voice channel members: {not_in_voice}')

            mentions = ' '.join([f'<@{member.id}>' for member in not_in_voice])
            if len(not_in_voice) != 0:
                await self.attendance_channel.send(f'{mentions} 22시 10분 입니다. 혹시 깜빡하셨나요?')
        except Exception as e:
            logging.error(e)


async def setup(bot) -> None:
    # await bot.add_cog(Alert(bot), guild=discord.Object(id=TEST_GUILD_ID))
    await bot.add_cog(Alert(bot))
