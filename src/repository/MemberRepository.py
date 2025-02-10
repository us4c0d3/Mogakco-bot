import discord


class MemberRepository:
    def __init__(self, db_connector):
        self.db_connector = db_connector

    def get_member(self, member_id):
        sql = '''
            SELECT * FROM member WHERE member_id = %s;
        '''
        with self.db_connector.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (member_id,))
                return cursor.fetchone()

    def insert_member(self, member: discord.Member):
        user_id = member.id
        name = member.name
        display_name = member.display_name
        penalty_count = 0

        sql = '''
            INSERT INTO member(user_id, name, display_name, penalty_count)
            VALUES (%s, %s, %s, %s);
        '''
        with self.db_connector.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (user_id, name, display_name, penalty_count))
                conn.commit()
                return True
