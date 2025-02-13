import asyncio
import logging
import os
from datetime import timedelta, timezone, time, datetime

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from util.TimeCalc import TimeCalc

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

        self.alertService = bot.alert_service

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
        self.alert_final_attendees.start()

        logging.info('Alert.py is ready')

    # 19:30 20시 참가자 30분 전 알림
    @tasks.loop(time=time(hour=19, minute=30, second=0, tzinfo=KST))
    async def alert_attendance(self) -> None:
        await self.attendance_channel.send(f'<@&{PARTICIPANT_ID}> 20시 모각코 30분 전입니다!')

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
                formatted_time = TimeCalc.format_time(elapsed_time)
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
        complete_members, unterminated_members = self.alertService.get_final_attendees(now, voice_channel_members)

        for member, formatted_time in unterminated_members:
            logging.info(f'{member.display_name} 님 통화방 누적 시간 계산. 누적 접속 시간: {formatted_time}')
            await self.attendance_channel.send(
                f'<@{member.id}> 님의 오늘 통화방 누적 접속 시간: {formatted_time}'
            )

        if complete_members:
            mentions = ' '.join([f'<@{member.id}>' for member, _ in complete_members])
            await self.attendance_channel.send(f"20시부터 24시까지 1시간 이상 음성 채널에 참여한 사람들: {mentions}")
            self.alertService.save_study_date()

        self.alertService.reset_daily_data()

    @tasks.loop(hours=168)
    async def alert_penalty_members(self) -> None:
        today = datetime.now(tz=KST)
        monday, sunday = TimeCalc.calc_past_week(today)
        members = self.get_attendance()

        penalty_members = self.studyService.get_penalty_members(members, monday, sunday)
        penalty_member_names = [member['name'] for member in penalty_members]
        penalty_member_mentions = ' '.join([f"<@{penalty_member['member_id']}>" for penalty_member in penalty_members])

        logging.info(f'This week penalty members: {penalty_member_names}')
        if penalty_members:
            await self.attendance_channel.send(
                f"{penalty_member_mentions} {monday.strftime('%Y-%m-%d')} ~ {sunday.strftime('%Y-%m-%d')} 기간 중 4시간을 채우지 못한 참가자입니다. ")

    @alert_penalty_members.before_loop
    async def before_alert_penalty_members(self) -> None:
        now = datetime.now(tz=KST)
        target_time = now.replace(hour=0, minute=45, second=0)

        days_ahead = 0 - now.weekday()
        if days_ahead <= 0:
            days_ahead += 7

        target_time = target_time + timedelta(days=days_ahead)

        if target_time < now:
            target_time += timedelta(weeks=1)

        delay = (target_time - now).total_seconds()
        logging.info(f'초기 딜레이: {delay}초 후 페널티 체크 작업 시작')
        await asyncio.sleep(delay)

    async def get_attendance(self):
        attendance_role = discord.utils.get(self.attendance_channel.guild.roles, id=PARTICIPANT_ID)
        if not attendance_role:
            logging.info("참가자가 없습니다.")
            return []

        return [member for member in self.attendance_channel.guild.members if attendance_role is member.role]


async def setup(bot) -> None:
    # await bot.add_cog(Alert(bot), guild=discord.Object(id=TEST_GUILD_ID))
    await bot.add_cog(Alert(bot))
