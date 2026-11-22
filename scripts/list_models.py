"""List models the configured provider offers (reads .env; never prints the key)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from arena.llm import LLM  # noqa: E402

llm = LLM("red")
models = [m.id for m in llm._client.models.list().data]
print(len(models), "models; first 25:")
for m in models[:25]:
    print(" ", m)
