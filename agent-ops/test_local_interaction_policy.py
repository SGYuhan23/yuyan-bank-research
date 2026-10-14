"""Local interaction contract: explicit scopes remain protected, routine research proceeds."""
from deerflow.agents.interaction_policy import _INTERACTIVE_CLARIFICATION_SYSTEM

def test_research_does_not_need_repeated_approval():
    text=_INTERACTIVE_CLARIFICATION_SYSTEM
    assert 'Read-only research is already authorized' in text
    assert 'MANDATORY Clarification Scenarios' not in text
    assert 'destructive' in text
    assert 'sibling calls are dropped' in text


def test_reminders_do_not_reintroduce_blanket_approval():
    from deerflow.agents.interaction_policy import RunInteractionPolicy
    policy=RunInteractionPolicy.interactive()
    assert "anything is unclear" not in policy.thinking_guidance
    assert "ALWAYS clarify" not in policy.clarification_reminder
