from anthropic.types import citation_content_block_location_param
class ChatStore:

    def __init__(self, database):
        self.database = database

    def create_user(self):
        connection = self.database.get_connection()
        cursor = connection.cursor()

        cursor.execute(
            "INSERT INTO users DEFAULT VALUES"
        )

        user_id = cursor.lastrowid

        connection.commit()
        connection.close()

        return user_id

    def create_conversation(self, user_id, title=None):
        connection = self.database.get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO conversations (user_id, title)
            VALUES (?, ?)
            """,
            (user_id, title)
        )

        conversation_id = cursor.lastrowid

        connection.commit()
        connection.close()

        return conversation_id

    def save_message(self, conversation_id, role, content):
        connection = self.database.get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO messages
            (conversation_id, role, content)
            VALUES (?, ?, ?)
            """,
            (conversation_id, role, content)
        )

        message_id = cursor.lastrowid

        connection.commit()
        connection.close()

        return message_id

    def get_recent_messages(self, conversation_id, limit=20):
        connection = self.database.get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT role, content
            FROM messages
            WHERE conversation_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (conversation_id, limit)
        )

        rows = cursor.fetchall()

        connection.close()
        rows.reverse()

        return [
            {
                "role":role,
                "content":content
            }for role,content in rows
        ]
    
    def get_user(self, user_id):
        connection = self.database.get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        )

        user = cursor.fetchone()

        connection.close()

        return user

    def get_user_conversations(self, user_id):
        connection = self.database.get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id, title
            FROM conversations
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,)
        )

        rows = cursor.fetchall()

        connection.close()

        return [
            {
                "id": row[0],
                "title": row[1]
            } for row in rows
        ]

    def get_summary(self, conversation_id):
        connection = self.database.get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT summary
            FROM conversations
            WHERE id = ?
            """,
            (conversation_id,)
        )

        result = cursor.fetchone()

        connection.close()

        return result[0] if result else None

    def update_summary(self, conversation_id, summary):
        connection = self.database.get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE conversations
            SET summary = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (summary, conversation_id)
        )

        connection.commit()
        connection.close()