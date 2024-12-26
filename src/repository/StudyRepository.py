class StudyRepository:
    def __init__(self, db_connector):
        self.db_connector = db_connector

    def insert(self, member_id, today, times):
        sql = '''
            INSERT INTO study(member_id, today, study_hours) VALUES (%s, %s, %s)
        '''

        with self.db_connector.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (member_id, today, times))
                conn.commit()
                return True

    def get_member_times_on_week(self, user_id, start_date, end_date):
        sql = '''
            SELECT m.name, s.today, s.study_hours 
            FROM study s
            JOIN member m ON s.member_id = m.id  
            WHERE m.user_id = %s 
            AND s.today >= %s AND s.today <= %s
        '''

        with self.db_connector.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (user_id, start_date, end_date))
                results = cursor.fetchall()
                return results
