import logging
from datetime import timezone, timedelta

tz = timezone(timedelta(hours=+9), 'KST')


class StudyService:
    def __init__(self, member_repo, study_repo):
        self.member_repo = member_repo
        self.study_repo = study_repo

    def ensure_member(self, member):
        db_member = self.member_repo.get_by_id(member.id)
        if db_member is None:
            self.member_repo.insert_member(member)
            logging.info(f"Inserted member {member.display_name} ({member.id})")

    def save_study_time(self, member, study_time, record_date):
        self.ensure_member(member)
        return self.study_repo.insert(member.id, study_time, record_date)

    def get_members_study_time(self, members, monday, sunday):
        member_ids = [member.id for member in members]
        return self.study_repo.get_members_study_time_over_penalty(member_ids, monday, sunday)
