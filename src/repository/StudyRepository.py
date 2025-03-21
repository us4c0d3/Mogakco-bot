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

    def get_weekly_study_time(self, user_id, start_date, end_date):
        sql = '''
            SELECT COALESCE(SUM(s.study_hours), 0) AS total_hours
            FROM study s
            JOIN member m ON s.member_id = m.id  
            WHERE m.user_id = %s 
            AND s.today BETWEEN %s AND %s
        '''

        with self.db_connector.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (user_id, start_date, end_date))
                result = cursor.fetchone()
                return result['total_hours'] if result else 0

    def get_members_study_time_over_penalty(self, member_ids, start_date, end_date, penalty=4):
        if not member_ids:
            return []

        placeholders = ', '.join(['%s'] * len(member_ids))

        sql = f'''
                SELECT m.*, COALESCE(SUM(s.study_hours), 0) AS total_hours
                FROM study s
                JOIN member m ON s.member_id = m.id
                WHERE m.user_id IN ({placeholders})
                  AND s.today BETWEEN %s AND %s
                GROUP BY m.id
                HAVING COALESCE(SUM(s.study_hours), 0) >= %s
            '''

        params = member_ids + [start_date, end_date, penalty]

        with self.db_connector.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                results = []
                for row in rows:
                    results.append({
                        'member_id': row['user_id'],
                        'name': row['name'],
                        'display_name': row['display_name']
                    })
                return results
