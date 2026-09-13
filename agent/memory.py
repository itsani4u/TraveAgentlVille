"""
agent/memory.py
-----------------
Minimal conversation + scratchpad memory for the agent. No external
dependency needed - just a couple of Python lists wrapped in a class so the
rest of the code has one clear place to read/write "what happened so far".
"""

from typing import List, Dict


class AgentMemory:
    def __init__(self):
        self.chat_history: List[Dict[str, str]] = []       # user/assistant turns for the Streamlit chat
        self.react_scratchpad: List[str] = []               # THOUGHT/ACTION/OBSERVATION lines for one ReAct run

    # --- chat history -----------------------------------------------------
    def add_user_message(self, text: str) -> None:
        self.chat_history.append({"role": "user", "content": text})

    def add_assistant_message(self, text: str) -> None:
        self.chat_history.append({"role": "assistant", "content": text})

    def get_history(self) -> List[Dict[str, str]]:
        return self.chat_history

    # --- ReAct scratchpad ---------------------------------------------------
    def reset_scratchpad(self) -> None:
        self.react_scratchpad = []

    def add_scratchpad_entry(self, entry: str) -> None:
        self.react_scratchpad.append(entry)

    def get_scratchpad_text(self) -> str:
        return "\n".join(self.react_scratchpad)
