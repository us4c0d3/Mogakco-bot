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

            await self.vote_channel.send('@everyone 투표 마감 30분 전입니다!')

        except Exception as e:
            logging.error(e)

    # 19:20 투표자 취합
    def update_voters(self, attend_voters):
        self.attend_voters = attend_voters

    # 19:30 20시 참가자 30분 전 알림
    @tasks.loop(time=time(hour=19, minute=30, second=0, tzinfo=KST))
    async def alert_attendance(self) -> None:
        if len(self.attend_voters) == 0:
            logging.info('attend_voters is empty')
            return

        mentions = ' '.join([f'<@{member.id}>' for member in self.attend_voters])
        await self.attendance_channel.send(f'{mentions} 20시 모각코 30분 전입니다!')

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        now = datetime.now(tz=KST)

        if time(20, 0, 0) <= now.time() <= time(23, 59, 59):
            if before.channel is None and after.channel is not None:
                self.voice_times[member.id] = now
                logging.info(f'{member.name} 님이 {now}에 통화방에 참가했습니다')
            elif before.channel is not None and after.channel is None:
                if member.id in self.voice_times:
                    join_time = self.voice_times.pop(member.id)
                    time_spent = now - join_time
                    logging.info(f'{member.name} 님이 통화방에서 퇴장하셨습니다. 접속 시간: {time_spent}')

                    if time_spent >= timedelta(hours=2):
                        if member.id not in self.two_hours_members:
                            self.two_hours_members.append(member.id)
                            logging.info(f'{member.name}이 2시간 이상 참가했습니다.')

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

            mentions = ' '.join([f'<@{member.id}>' for member in not_in_voice])
            if len(not_in_voice) != 0:
                await self.attendance_channel.send(f'{mentions} 20시 30분 입니다. 혹시 깜빡하셨나요?')
        except Exception as e:
            logging.error(e)

    # 24:30 참가자 및 불참자 알림
    @tasks.loop(time=time(hour=0, minute=30, second=0, tzinfo=KST))
    async def alert_final_attendance(self) -> None:
        if self.attendance_channel is None:
            logging.warning("Attendance channel not set.")
            return

        if len(self.attend_voters) == 0:
            logging.info('참가 투표한 사람이 없습니다')
            return

        # 투표한 사용자 중 2시간 이상 음성 채널에 참여한 사용자
        attended_members = [voter for voter in self.attend_voters if
                            voter.id in [member.id for member in self.two_hours_members]]

        # 투표했지만 2시간 동안 참여하지 않은 사용자
        not_attended_members = [voter for voter in self.attend_voters if
                                voter.id not in [member.id for member in self.two_hours_members]]

        if len(attended_members) > 0:
            mentions_attended = ' '.join([f'<@{member.id}>' for member in attended_members])
            await self.attendance_channel.send(f"20시부터 24시까지 2시간 이상 음성 채널에 참여한 사람들: {mentions_attended}")
        else:
            await self.attendance_channel.send("20시부터 24시까지 2시간 이상 음성 채널에 참여한 사람이 없습니다.")

        if len(not_attended_members) > 0:
            mentions_not_attended = ' '.join([f'<@{member.id}>' for member in not_attended_members])
            await self.attendance_channel.send(f"{mentions_not_attended}, 투표했지만 2시간을 채우지 못했습니다. 다음에는 꼭 참석해주세요!")

        self.two_hours_members.clear()
        self.attend_voters.clear()


async def setup(bot) -> None:
    # await bot.add_cog(Alert(bot), guild=discord.Object(id=TEST_GUILD_ID))
    await bot.add_cog(Alert(bot))
