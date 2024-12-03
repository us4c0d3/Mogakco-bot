import logging
import os
from datetime import timedelta, timezone, time, datetime

from discord.ext import commands, tasks
from dotenv import load_dotenv

from src.service.AlertService import AlertService

load_dotenv()

try:
    VOICE_CHANNEL_ID = int(os.getenv('VOICE_CHANNEL_ID'))
    ATTENDANCE_CHANNEL_ID = int(os.getenv('ATTENDANCE_CHANNEL_ID'))
    TEST_GUILD_ID = int(os.getenv('TEST_GUILD_ID'))
    PARTICIPANT_ID = int(os.getenv('PARTICIPANT_ID'))
except (TypeError, ValueError):
    raise RuntimeError("Environment variables are not properly set.")

KST = timezone(timedelta(hours=9))


class Alert(commands.Cog):
    """
    알림 관련 타임라인
    19:30 참가자 30분 전 알림
    24:30 참가자 및 불참자 알림
    """

    def __init__(self, bot) -> None:
        self.bot = bot

        self.voice_channel = None
        self.attendance_channel = None

        self.alertService = AlertService(participant_role_id=PARTICIPANT_ID, tz=KST)

    @commands.Cog.listener()
    async def on_ready(self):
        self.voice_channel = self.bot.get_channel(VOICE_CHANNEL_ID)
        self.attendance_channel = self.bot.get_channel(ATTENDANCE_CHANNEL_ID)

        if self.voice_channel:
            logging.info(f'Default voice channel set to: {self.voice_channel.name} (ID: {self.voice_channel.id})')
        else:
            logging.warning(f'Channel with ID {VOICE_CHANNEL_ID} not found.')

        if self.attendance_channel:
            logging.info(f'Default attendance channel set to: '
                         f'{self.attendance_channel.name} (ID: {self.attendance_channel.id})')
        else:
            logging.warning(f'Channel with ID {ATTENDANCE_CHANNEL_ID} not found.')

        self.alert_attendance.start()
        self.alert_final_attendance.start()

        logging.info('Alert.py is ready')

    # 19:30 20시 참가자 30분 전 알림
    @tasks.loop(time=time(hour=19, minute=30, second=0, tzinfo=KST))
    async def alert_attendance(self) -> None:
        await self.attendance_channel.send(f'<@&{self.participant_role_id}> 20시 모각코 30분 전입니다!')

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        now = datetime.now(tz=KST)

        if (before.channel is None and after.channel is not None
                and time(19, 31, 0) <= now.time() <= time(23, 59, 59)):
            self.alertService.track_join(member, now)
            logging.info(f'{member.display_name} 님이 {now}에 통화방에 참가했습니다')

        if after.channel is None and before.channel is not None:
            elapsed_time = self.alertService.track_leave(member, now)
            if elapsed_time:
                formatted_time = self.alertService.format_time(elapsed_time)
                logging.info(f'{member.display_name} 님이 통화방에서 퇴장했습니다. 누적 접속 시간: {formatted_time}')
                await self.attendance_channel.send(
                    f'<@{member.id}> 님의 오늘 통화방 누적 접속 시간: {formatted_time}'
                )
            else:
                logging.info(f'join_time에서 {member.display_name}를 찾을 수 없습니다; 19:31~23:59에 통화방에 접속하지 않았습니다.')

    # 24:30 1시간 이상 참가자 알림
    @tasks.loop(time=time(hour=0, minute=30, second=0, tzinfo=KST))
    async def alert_final_attendees(self) -> None:
        if self.attendance_channel is None:
            logging.warning("Attendance channel not set.")
            return
        now = datetime.now(tz=KST)
        voice_channel_members = self.voice_channel.members if self.voice_channel else []
        complete_members = self.alertService.get_final_attendees(now, voice_channel_members)

        if complete_members:
            mentions = ' '.join([f'<@{member.id}>' for member, _ in complete_members])
            await self.attendance_channel.send(f"20시부터 24시까지 1시간 이상 음성 채널에 참여한 사람들: {mentions}")

        self.alertService.reset_daily_data()


async def setup(bot) -> None:
    # await bot.add_cog(Alert(bot), guild=discord.Object(id=TEST_GUILD_ID))
    await bot.add_cog(Alert(bot))
