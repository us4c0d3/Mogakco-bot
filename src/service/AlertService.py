from collections import defaultdict
from datetime import timedelta, timezone, datetime


class AlertService:
    def __init__(self, participant_role_id: int, tzinfo=timezone(timedelta(hours=9))):
        self.participant_role_id = participant_role_id
        self.tzinfo = tzinfo

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
        for member in self.today_members:
            if member in voice_channel_members and member in self.join_time:
                self.voice_times[member] += now - self.join_time[member] - self.join_time[member]

            if (self.voice_times[member] >= timedelta(hours=1)
                    and any(role.id == self.participant_role_id for role in member.roles)):
                complete_members.append((member, self.voice_times[member]))

        return complete_members

    def reset_daily_data(self):
        self.join_time.clear()
        self.voice_times.clear()
        self.today_members.clear()

    @staticmethod
    def format_time(delta: timedelta) -> str:
        hours, remainder = divmod(delta.total_seconds(), 3600)
        minutes = remainder // 60
        return f'{int(hours)}시간 {int(minutes)}분'
