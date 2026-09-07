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
            SELECT id, created_at
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

    def save_memory(self,user_id,memory_type,key,value,scope=None):
        connection = self.database.get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO long_term_memories
            (user_id, memory_type, key, value, scope)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                memory_type,
                key,
                value,
                scope
            )
        )

        memory_id = cursor.lastrowid

        connection.commit()
        connection.close()

        return memory_id

    def find_memory(self,user_id,memory_type,key,scope=None):

        connection = self.database.get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id, value
            FROM long_term_memories
            WHERE user_id = ?
            AND memory_type = ?
            AND key = ?
            AND (
                scope = ?
                OR (scope IS NULL AND ? IS NULL)
            )
            """,
            (
                user_id,
                memory_type,
                key,
                scope,
                scope
            )
        )

        row = cursor.fetchone()

        connection.close()

        if not row:
            return None

        return {
            "id": row[0],
            "value": row[1]
        }


    def get_memories(self, user_id):
        connection = self.database.get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id, memory_type, key, value, scope
            FROM long_term_memories
            WHERE user_id = ?
            """,
            (user_id,)
        )

        rows = cursor.fetchall()

        connection.close()

        return [
            {
                "id": row[0],
                "memory_type": row[1],
                "key": row[2],
                "value": row[3],
                "scope": row[4]
            }
            for row in rows
        ]

    def update_memory(self, memory_id, value):
        connection = self.database.get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE long_term_memories
            SET value = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (value, memory_id)
        )

        connection.commit()
        connection.close()

    def delete_memory(self, memory_id):
        connection = self.database.get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM long_term_memories
            WHERE id = ?
            """,
            (memory_id,)
        )

        connection.commit()
        connection.close()

    def delete_memory_by_key(self, user_id, memory_type, key, scope=None):
        connection = self.database.get_connection()
        cursor = connection.cursor()

        # Find matching memory IDs first
        cursor.execute(
            """
            SELECT id FROM long_term_memories
            WHERE user_id = ?
            AND memory_type = ?
            AND key = ?
            AND (
                scope = ?
                OR (scope IS NULL AND ? IS NULL)
                OR (scope = '' AND (? IS NULL OR ? = ''))
            )
            """,
            (user_id, memory_type, key, scope, scope, scope, scope)
        )
        rows = cursor.fetchall()
        deleted_ids = [row[0] for row in rows]

        if deleted_ids:
            placeholders = ",".join(["?"] * len(deleted_ids))
            cursor.execute(
                f"DELETE FROM long_term_memories WHERE id IN ({placeholders})",
                deleted_ids
            )
            connection.commit()

        connection.close()
        return deleted_ids

    def delete_all_memories(self, user_id):
        connection = self.database.get_connection()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT id FROM long_term_memories WHERE user_id = ?",
            (user_id,)
        )
        rows = cursor.fetchall()
        deleted_ids = [row[0] for row in rows]

        cursor.execute(
            "DELETE FROM long_term_memories WHERE user_id = ?",
            (user_id,)
        )

        connection.commit()
        connection.close()
        return deleted_ids

    def delete_conversation(self, conversation_id: int) -> bool:
        connection = self.database.get_connection()
        cursor = connection.cursor()

        # Delete messages associated with conversation
        cursor.execute(
            "DELETE FROM messages WHERE conversation_id = ?",
            (conversation_id,)
        )

        cursor.execute(
            "DELETE FROM conversations WHERE id = ?",
            (conversation_id,)
        )
        deleted = cursor.rowcount > 0

        connection.commit()
        connection.close()
        return deleted

    def delete_user(self, user_id: int) -> bool:
        connection = self.database.get_connection()
        cursor = connection.cursor()

        # 1. Find all user conversations
        cursor.execute(
            "SELECT id FROM conversations WHERE user_id = ?",
            (user_id,)
        )
        conv_rows = cursor.fetchall()
        conv_ids = [r[0] for r in conv_rows]

        # 2. Delete messages for all user conversations
        if conv_ids:
            placeholders = ",".join(["?"] * len(conv_ids))
            cursor.execute(
                f"DELETE FROM messages WHERE conversation_id IN ({placeholders})",
                conv_ids
            )

        # 3. Delete user conversations
        cursor.execute(
            "DELETE FROM conversations WHERE user_id = ?",
            (user_id,)
        )

        # 4. Delete user memories
        cursor.execute(
            "DELETE FROM long_term_memories WHERE user_id = ?",
            (user_id,)
        )

        # 5. Delete user
        cursor.execute(
            "DELETE FROM users WHERE id = ?",
            (user_id,)
        )
        deleted = cursor.rowcount > 0

        connection.commit()
        connection.close()
        return deleted


