import json
import re
from enum import Enum
from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    PREFERENCE = "preference"
    GOAL = "goal"
    FACT = "fact"
    PLAN = "plan"
    DECISION = "decision"


class Memory(BaseModel):
    memory_type: MemoryType
    key: str
    value: str
    scope: str | None = None


class ExtractedMemories(BaseModel):
    memories: list[Memory] = Field(default_factory=list)


class MemoryExtractor:
    def __init__(self, model):
        self.model = model

    def extract(self, user_message: str) -> list[Memory]:
        system_prompt = (
            "You are a Memory Extractor for a conversational AI agent.\n"
            "Analyze the user's input and extract any long-term memory items like user preferences, facts, goals, plans, or decisions.\n\n"
            "Valid memory types:\n"
            "- preference (e.g. user loves DSA, likes Python)\n"
            "- goal (e.g. wants to crack SDE interview)\n"
            "- fact (e.g. user is a CS student, lives in NY)\n"
            "- plan (e.g. planning to learn Rust next month)\n"
            "- decision (e.g. decided to focus on backend dev)\n\n"
            "Key guidelines:\n"
            "1. Choose a clear, standardized key for the topic (e.g. 'favorite_subject', 'location', 'target_role', 'programming_language').\n"
            "2. Ensure the value clearly states the extracted preference/fact/goal.\n"
            "3. If no relevant long-term memory is present in the input, return {\"memories\": []}.\n"
            "4. Return ONLY valid JSON in this format:\n"
            "{\n"
            '  "memories": [\n'
            '    {"memory_type": "preference", "key": "favorite_subject", "value": "user loves DSA", "scope": null}\n'
            "  ]\n"
            "}"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Extract memory items from this user message:\n\"{user_message}\""}
        ]

        try:
            raw_response = self.model.generate(messages)
            cleaned = raw_response.strip()
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.MULTILINE)
            cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()

            data = json.loads(cleaned)
            memories_raw = data.get("memories", [])

            extracted = []
            for item in memories_raw:
                try:
                    mem = Memory(
                        memory_type=MemoryType(item.get("memory_type", "preference")),
                        key=str(item.get("key", "")).strip().lower(),
                        value=str(item.get("value", "")).strip(),
                        scope=item.get("scope")
                    )
                    if mem.key and mem.value:
                        extracted.append(mem)
                except Exception:
                    continue
            return extracted
        except Exception:
            return []