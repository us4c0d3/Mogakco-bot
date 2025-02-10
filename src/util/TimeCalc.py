from datetime import timedelta, datetime


class TimeCalc:
    @staticmethod
    def format_time(delta: timedelta) -> str:
        hours, remainder = divmod(delta.total_seconds(), 3600)
        minutes = remainder // 60
        return f'{int(hours)}시간 {int(minutes)}분'

    @staticmethod
    def calc_week(today: datetime) -> tuple:
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)

        return monday, sunday

    @staticmethod
    def calc_past_week(today: datetime) -> tuple:
        monday, sunday = TimeCalc.calc_week(today)
        return monday - timedelta(days=7), sunday - timedelta(days=7)
