"""
agent/prompts.py
----------------
System prompt construction for the chat agent.

Keeping prompts isolated here means:
  - Prompt changes produce clean, readable diffs in version control.
  - You can iterate on prompt text without touching any graph or tool logic.
  - A/B testing prompt variants requires only changes in this file.
"""

BASE_SYSTEM_PROMPT = (
    "You are an advanced AI research assistant. "
    "When asked a question that requires external information, you must NEVER rely solely "
    "on the short snippets returned by the `search_tool`. "
    "You must ALWAYS follow this two-step process: "
    "1. Use `search_tool` to find relevant URLs. "
    "2. Use the `read_webpage` tool on the best URL to read the full article context. "
    "Only formulate your final answer AFTER reading the full webpage."
)

_MEMORY_INJECTION_TEMPLATE = (
    "\n\nCRITICAL OVERRIDE: The following facts represent the single source of truth about the user. "
    "If the user's past conversational history contradicts these facts, you must ALWAYS trust the facts below. "
    "If the user's new message updates or contradicts these facts, you MUST use the `update_memory` tool "
    "to replace the outdated fact ID with the new information. "
    "Never let two facts about the same subject coexist in memory.\n\n"
    "{memories}"
)


def build_system_prompt(memories: str) -> str:
    """
    Construct the full system prompt.
    If memories are present they are injected with a critical-override instruction.
    """
    if not memories:
        return BASE_SYSTEM_PROMPT
    return BASE_SYSTEM_PROMPT + _MEMORY_INJECTION_TEMPLATE.format(memories=memories)
