import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app')))

from app.memory.context_manager import ContextManager, estimate_tokens


class TestContextManager(unittest.TestCase):

    def setUp(self):
        self.cm = ContextManager(
            system_instructions="Test Persona instructions.",
            max_total_tokens=1000,
            max_memory_tokens=300,
            max_history_tokens=500
        )

    def test_token_estimation(self):
        self.assertEqual(estimate_tokens(""), 0)
        self.assertEqual(estimate_tokens("Hello world!"), 3)
        self.assertGreater(estimate_tokens("A longer paragraph of text to test token estimation capabilities."), 10)

    def test_memory_categorization(self):
        memories = [
            {"content": "PREFERENCE [favorite_language]: user loves Python", "metadata": {"memory_type": "preference"}},
            {"content": "GOAL [target_role]: wants to become SDE", "metadata": {"memory_type": "goal"}},
            {"content": "FACT [location]: lives in New York", "metadata": {"memory_type": "fact"}},
            {"content": "PLAN [next_skill]: learning Rust next month", "metadata": {"memory_type": "plan"}},
            {"content": "DECISION [focus]: decided on backend dev", "metadata": {"memory_type": "decision"}}
        ]

        formatted = self.cm.format_categorized_memories(memories)

        self.assertIn("### User Preferences:", formatted)
        self.assertIn("user loves Python", formatted)
        self.assertIn("### User Goals:", formatted)
        self.assertIn("wants to become SDE", formatted)
        self.assertIn("### User Facts & Context:", formatted)
        self.assertIn("lives in New York", formatted)
        self.assertIn("### User Plans:", formatted)
        self.assertIn("learning Rust next month", formatted)
        self.assertIn("### User Decisions:", formatted)
        self.assertIn("decided on backend dev", formatted)

    def test_context_assembly(self):
        summary = "User discussed Python and SDE goals."
        recent_messages = [
            {"role": "user", "content": "Hi there!"},
            {"role": "assistant", "content": "Hello! How can I help you today?"}
        ]
        memories = [{"content": "PREFERENCE [fav]: Python", "metadata": {"memory_type": "preference"}}]

        context = self.cm.build_context(
            summary=summary,
            recent_messages=recent_messages,
            current_message="What is my favorite language?",
            long_term_memories=memories
        )

        self.assertGreaterEqual(len(context), 4)  # system, 2 history, current user
        self.assertEqual(context[0]["role"], "system")
        self.assertIn("Test Persona instructions.", context[0]["content"])
        self.assertIn("User Preferences", context[0]["content"])
        self.assertEqual(context[-1]["role"], "user")
        self.assertEqual(context[-1]["content"], "What is my favorite language?")

    def test_dynamic_context_pruning(self):
        # Create a ContextManager with a very small history budget to force pruning
        strict_cm = ContextManager(
            system_instructions="Short system prompt",
            max_total_tokens=1000,
            max_history_tokens=30  # ~120 characters max for history
        )

        # 5 messages history
        recent_messages = [
            {"role": "user", "content": "Turn 1: This is a very long message filling history tokens."},
            {"role": "assistant", "content": "Turn 1 Response: Responding to Turn 1 with more long text."},
            {"role": "user", "content": "Turn 2: Another long message in conversation history."},
            {"role": "assistant", "content": "Turn 2 Response: Assistance response."},
            {"role": "user", "content": "Turn 3: Recent turn."}
        ]

        context = strict_cm.build_context(
            summary=None,
            recent_messages=recent_messages,
            current_message="Current turn request",
            long_term_memories=None
        )

        stats = strict_cm.get_last_context_stats()
        self.assertGreater(stats["history_messages_pruned"], 0)
        self.assertLess(stats["history_messages_included"], len(recent_messages))
        # Ensure the most recent message before current message is preserved
        included_roles = [m["role"] for m in context]
        self.assertEqual(included_roles[0], "system")
        self.assertEqual(included_roles[-1], "user")

    def test_context_stats(self):
        self.cm.build_context(
            summary="Brief summary",
            recent_messages=[{"role": "user", "content": "Hello"}],
            current_message="How are you?",
            long_term_memories=[{"content": "FACT: user is human", "metadata": {"memory_type": "fact"}}]
        )

        stats = self.cm.get_last_context_stats()
        self.assertIn("system_tokens", stats)
        self.assertIn("history_tokens", stats)
        self.assertIn("total_estimated_tokens", stats)
        self.assertEqual(stats["memory_count"], 1)
        self.assertEqual(stats["history_messages_included"], 1)
        self.assertEqual(stats["history_messages_pruned"], 0)


if __name__ == "__main__":
    unittest.main()
