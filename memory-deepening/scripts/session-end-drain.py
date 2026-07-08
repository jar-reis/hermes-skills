# Session-End Drain Script

**Purpose**: Retain session summary to L2 (Hindsight) and train L3 (fact_store) trust scores.

## Code
```python
#!/usr/bin/env python3
from hermes_tools import hindsight_retain, fact_feedback, session_search
from datetime import datetime
import sys

def drain_session(session_id=None):
    summary = f"Session {session_id or 'adhoc'}: {datetime.now().isoformat()} - Key outcomes: "
    hindsight_retain(content=summary, context="session", tags=["session"], async_=True)
    
    facts = session_search(query="*", limit=5)
    for fact in facts.get("results", []):
        fact_feedback(action="helpful", fact_id=fact["id"])
    
    return "Session drain complete."

if __name__ == "__main__":
    print(drain_session(sys.argv[1] if len(sys.argv) > 1 else None))
```