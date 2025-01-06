import logging
from collections import defaultdict
from datetime import timedelta, timezone, datetime

from utils import TimeCalc


class AlertService:
    def __init__(self, participant_role_id: int, tz=timezone(timedelta(hours=9))):
        self.participant_role_id = participant_role_id
        self.tz = tz

        self.join_time = {}
        self.voice_times = defaultdict(timedelta)
        self.today_members = []

    def track_join(self, member, now: datetime):
        self.join_time[member] = now
        if member not in self.today_members:
            self.today_members.append(member)

    def track_leave(self, member, now: datetime):
        if member in self.join_time:
            elapsed_time = now - self.join_time.pop(member)
            self.voice_times[member] += elapsed_time
            return self.voice_times[member]
        return None

    def get_final_attendees(self, now: datetime, voice_channel_members):
        complete_members = []
        unterminated_members = []
        for member in self.today_members:
            if member in voice_channel_members:
                if member in self.join_time:
                    elapsed_time = now - self.join_time[member]
                    self.voice_times[member] += elapsed_time
                    formatted_time = TimeCalc.format_time(self.voice_times[member])
                    logging.info(f'{member.display_name} 님 통화방 누적 시간 계산. 누적 접속 시간: {formatted_time}')
                    self.join_time.pop(member)
                    unterminated_members.append((member, formatted_time))
                else:
                    logging.info(f'Member {member.display_name} has no join_time. Skipping.')

            if (self.voice_times[member] >= timedelta(hours=1)
                    and any(role.id == self.participant_role_id for role in member.roles)):
                complete_members.append((member, self.voice_times[member]))

        if len(self.join_time):
            logging.info(f'join_time에 사람이 남아있습니다. join_time: {self.join_time}')

        return complete_members, unterminated_members

    def reset_daily_data(self):
        self.join_time.clear()
        self.voice_times.clear()
        self.today_members.clear()

    @staticmethod
    def format_time(delta: timedelta) -> str:
        hours, remainder = divmod(delta.total_seconds(), 3600)
        minutes = remainder // 60
        return f'{int(hours)}시간 {int(minutes)}분'
