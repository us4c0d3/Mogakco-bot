from datetime import timezone, timedelta

tz = timezone(timedelta(hours=+9), 'KST')


class StudyService:
    def __init__(self, member_repo, study_repo):
        self.member_repo = member_repo
        self.study_repo = study_repo

    def save_study_time(self, member_id, study_time, record_date):
        return self.member_repo.save_study_time(member_id, study_time, record_date)
