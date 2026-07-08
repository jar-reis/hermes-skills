# Monthly Synthesis Script

**Purpose**: Synthesize L1/L2/L3 into OBn vault notes.

## Code
```python
#!/usr/bin/env python3
from hermes_tools import memory, hindsight_recall, fact_store, write_file
from datetime import datetime

def synthesize_memory():
    l1 = memory(target="memory", action="list")
    l2 = hindsight_recall(query="*", limit=20)
    l3 = fact_store(action="probe", entity="*")
    
    synthesis = f"# Memory Synthesis — {datetime.now().strftime('%Y-%m-%d')}\n\n"
    synthesis += "## L1 (Always-Injected)\n" + "\n".join(f"- {item}" for item in l1) + "\n\n"
    synthesis += "## L2 (Hindsight)\n" + "\n".join(f"- {item['content']}" for item in l2.get("results", [])) + "\n\n"
    synthesis += "## L3 (Holographic)\n" + "\n".join(
        f"- {item['content']} (entity: {item['entity']})" for item in l3
    ) + "\n"
    
    write_file(
        path="~/Documents/=notes/claude/memory/memory-synthesis.md",
        content=synthesis
    )
    
    return "Synthesis complete."

if __name__ == "__main__":
    print(synthesize_memory())
```