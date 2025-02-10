from datetime import timezone, timedelta

from repository.MemberRepository import MemberRepository
from repository.StudyRepository import StudyRepository

tz = timezone(timedelta(hours=+9), 'KST')


class StudyService:
    def __init__(self):
        self.member_repo = MemberRepository
        self.study_repo = StudyRepository

    def save_study_time(self, member_id, study_time, record_date):
        return self.member_repo.save_study_time(member_id, study_time, record_date)

    def get_members_study_time(self, members, monday, sunday):
        member_ids = [member.id for member in members]
        return self.study_repo.get_members_study_time_over_penalty(member_ids, monday, sunday)
