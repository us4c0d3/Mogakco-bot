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
    18:30 투표 마감 30분 전 알림
    19:20 투표자 취합
    19:30 참가자 30분 전 알림
    20:30 지각자 알림
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

        self.attend_voters = []

        self.join_time = {}
        self.voice_times = {}
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

        self.alert_vote_end.start()
        self.alert_attendance.start()
        self.alert_late.start()
        self.alert_final_attendance.start()

        logging.info('Alert.py is ready')

    # 18:30 투표 마감 30분 전 알림
    @tasks.loop(time=time(hour=18, minute=30, second=0, tzinfo=KST))
    async def alert_vote_end(self) -> None:
        try:
            if self.vote_channel is None:
                logging.warning(f'Vote channel not set.')
                return

            await self.vote_channel.send(f'<@{PARTICIPANT_ID}> 투표 마감 30분 전입니다!')

        except Exception as e:
            logging.error(e)

    # 19:20 투표자 취합
    def update_voters(self, attend_voters):
        self.attend_voters = attend_voters

    # 19:30 20시 참가자 30분 전 알림
    @tasks.loop(time=time(hour=19, minute=30, second=0, tzinfo=KST))
    async def alert_attendance(self) -> None:
        if not self.attend_voters:
            logging.info('attend_voters is empty')
            return

        mentions = ' '.join([f'<@{member.id}>' for member in self.attend_voters])
        await self.attendance_channel.send(f'{mentions} 20시 모각코 30분 전입니다!')

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        now = datetime.now(tz=KST)

        if time(19, 31, 0) <= now.time() <= time(23, 59, 59):
            if before.channel is None and after.channel is not None:
                self.join_time[member]: datetime = now
                logging.info(f'{member.display_name} 님이 {now}에 통화방에 참가했습니다')

        if before.channel is None and after.channel is not None:
            if member not in self.voice_times:
                self.voice_times[member] = timedelta(0)
            self.voice_times[member] += now - self.join_time[member]
            formatted_time = self.format_time(self.voice_times[member])
            logging.info(f'{member.display_name} 님이 통화방에서 퇴장했습니다. 누적 접속 시간: {formatted_time}')
            await self.attendance_channel.send(f'<@{member.id}> 님의 현재까지 통화방 누적 접속 시간: {formatted_time}')
            del self.join_time[member]

    # 20:30 지각자 알림
    @tasks.loop(time=time(hour=20, minute=30, second=0, tzinfo=KST))
    async def alert_late(self) -> None:
        try:
            if self.voice_channel is None or self.attendance_channel is None:
                logging.warning("Voice channel 또는 notification channel이 설정되지 않았습니다.")
                return

            voice_channel_members = self.voice_channel.members
            logging.info(f'Voice channel members: {voice_channel_members}')

            not_in_voice = [member for member in self.attend_voters if member not in voice_channel_members]
            logging.info(f'Not in voice channel members: {not_in_voice}')

            if not_in_voice:
                mentions = ' '.join([f'<@{member.id}>' for member in not_in_voice])
                await self.attendance_channel.send(f'{mentions} 20시 30분 입니다. 혹시 깜빡하셨나요?')
        except Exception as e:
            logging.error(e)

    # 24:30 참가자 및 불참자 알림
    @tasks.loop(time=time(hour=0, minute=30, second=0, tzinfo=KST))
    async def alert_final_attendance(self) -> None:
        if self.attendance_channel is None:
            logging.warning("Attendance channel not set.")
            return

        if not self.attend_voters:
            logging.info('참가 투표한 사람이 없습니다')
            return

        now = datetime.now(tz=KST)

        attended_members = []
        not_attended_members = []

        for member in self.attend_voters:
            # 접속 중인 사람은 현재 시간으로 계산하여 누적 시간 갱신
            if member in self.voice_channel.members:
                if member in self.voice_times:
                    self.voice_times[member] += now - self.join_time[member]
                else:
                    self.voice_times[member] = now - self.join_time[member]

                # 누적 시간이 2시간 이상인지 체크
                if self.voice_times[member] >= timedelta(hours=2):
                    attended_members.append(member)
                else:
                    not_attended_members.append(member)

            # 통화방에 없는 사람은 기존에 기록된 시간 기준으로 분류
            else:
                if member in self.voice_times and self.voice_times[member] >= timedelta(hours=2):
                    attended_members.append(member)
                else:
                    not_attended_members.append(member)

        if attended_members:
            mentions_attended = ' '.join([f'<@{member.id}>' for member in attended_members])
            await self.attendance_channel.send(f"20시부터 24시까지 2시간 이상 음성 채널에 참여한 사람들: {mentions_attended}")

        if not_attended_members:
            mentions_not_attended = ' '.join([f'<@{member.id}>' for member in not_attended_members])
            await self.attendance_channel.send(f"투표한 사람 중 2시간을 채우지 못한 사람들: {mentions_not_attended}")

        self.join_time.clear()
        self.voice_times.clear()
        self.two_hours_members.clear()
        self.attend_voters.clear()

    def format_time(self, delta: timedelta) -> str:
        hour = delta.days * 24 + delta.seconds // 3600
        minute = (delta.seconds % 3600) // 60
        return f'{hour}시간 {minute}분'


async def setup(bot) -> None:
    # await bot.add_cog(Alert(bot), guild=discord.Object(id=TEST_GUILD_ID))
    await bot.add_cog(Alert(bot))
