import discord


class MemberRepository:
    def __init__(self, db_connector):
        self.db_connector = db_connector

    def get_member(self, member_id):
        sql = '''
            SELECT * FROM member WHERE member_id = %s;
        '''
        conn = self.db_connector.get_connection()

        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, (member_id,))
                return cursor.fetchone()
        finally:
            conn.close()

    def insert_member(self, member: discord.Member):
        user_id = member.id
        name = member.name
        display_name = member.display_name
        penalty_count = 0

        sql = '''
            INSERT INTO member(user_id, name, display_name, penalty_count)
            VALUES (%s, %s, %s, %s);
        '''
        conn = self.db_connector.get_connection()

        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, (user_id, name, display_name, penalty_count))
                conn.commit()
                return True
        finally:
            conn.close()
