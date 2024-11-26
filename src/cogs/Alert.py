import logging
import os
from datetime import timedelta, timezone, time, datetime

from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()

VOTE_CHANNEL_ID = os.getenv('VOTE_CHANNEL_ID')
VOICE_CHANNEL_ID = os.getenv('VOICE_CHANNEL_ID')
ATTENDANCE_CHANNEL_ID = os.getenv('ATTENDANCE_CHANNEL_ID')
TEST_GUILD_ID = os.getenv('TEST_GUILD_ID')
PARTICIPANT_ID = os.getenv('PARTICIPANT_ID')

KST = timezone(timedelta(hours=9))


class Alert(commands.Cog):
    """
    알림 관련 타임라인
    19:30 참가자 30분 전 알림
    24:30 참가자 및 불참자 알림
    """

    def __init__(self, bot) -> None:
        self.bot = bot

        self.vote_channel_id = int(VOTE_CHANNEL_ID)
        self.vote_channel = None

        self.voice_channel_id = int(VOICE_CHANNEL_ID)
        self.voice_channel = None

        self.attendance_channel_id = int(ATTENDANCE_CHANNEL_ID)
        self.attendance_channel = None

        self.join_time = {}
        self.voice_times = {}
        self.today_members = []
        self.two_hours_members = []

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

        self.alert_attendance.start()
        self.alert_final_attendance.start()

        logging.info('Alert.py is ready')

    # 19:30 20시 참가자 30분 전 알림
    @tasks.loop(time=time(hour=19, minute=30, second=0, tzinfo=KST))
    async def alert_attendance(self) -> None:
        await self.attendance_channel.send(f'<@&{PARTICIPANT_ID}> 20시 모각코 30분 전입니다!')

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        now = datetime.now(tz=KST)

        if time(19, 31, 0) <= now.time() <= time(23, 59, 59):
            if before.channel is None and after.channel is not None:
                self.join_time[member]: datetime = now
                logging.info(f'{member.display_name} 님이 {now}에 통화방에 참가했습니다')
                if member not in self.today_members:
                    self.today_members.append(member)

        if after.channel is None and before.channel is not None:
            if member not in self.voice_times:
                self.voice_times[member] = timedelta(0)
            self.voice_times[member] += now - self.join_time[member]
            formatted_time = self.format_time(self.voice_times[member])
            logging.info(f'{member.display_name} 님이 통화방에서 퇴장했습니다. 누적 접속 시간: {formatted_time}')
            await self.attendance_channel.send(f'<@{member.id}> 님의 오늘 통화방 누적 접속 시간: {formatted_time}')
            del self.join_time[member]

    # 24:30 1시간 이상 참가자 알림
    @tasks.loop(time=time(hour=0, minute=30, second=0, tzinfo=KST))
    async def alert_final_attendance(self) -> None:
        if self.attendance_channel is None:
            logging.warning("Attendance channel not set.")
            return

        now = datetime.now(tz=KST)
        complete_members = []

        for member in self.today_members:
            if member in self.voice_channel.members:
                if member in self.voice_times:
                    self.voice_times[member] += now - self.join_time[member]
                else:
                    self.voice_times[member] = now - self.join_time[member]

                if self.voice_times[member] >= timedelta(hours=1) and PARTICIPANT_ID in member.roles:
                    complete_members.append((member, self.voice_times[member]))

            else:
                if (member in self.voice_times
                        and self.voice_times[member] >= timedelta(hours=1)
                        and PARTICIPANT_ID in member.roles):
                    complete_members.append((member, self.voice_times[member]))

        if complete_members:
            mentions_attended = ' '.join([f'<@{member.id}>' for member, _ in complete_members])
            await self.attendance_channel.send(f"20시부터 24시까지 1시간 이상 음성 채널에 참여한 사람들: {mentions_attended}")

        self.join_time.clear()
        self.voice_times.clear()
        self.today_members.clear()
        self.two_hours_members.clear()

    def format_time(self, delta: timedelta) -> str:
        hours, remainder = divmod(delta.total_seconds(), 3600)
        minutes = remainder // 60
        return f'{int(hours)}시간 {int(minutes)}분'


async def setup(bot) -> None:
    # await bot.add_cog(Alert(bot), guild=discord.Object(id=TEST_GUILD_ID))
    await bot.add_cog(Alert(bot))
