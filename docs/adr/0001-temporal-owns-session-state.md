# Temporal owns Session state

A Session is a Temporal workflow, and Temporal's event history is the only record of where a Session is. Every model call, Capability call, Check and Judgement runs as an activity; waiting for Review is a Signal. We do not keep a second copy of Session state in an agent framework's checkpoints or our own tables, because two records of the same Session drift apart and the history stops being evidence. This mirrors the "one state machine, one log" rule proposed for Sefira's Sophia Harness.
