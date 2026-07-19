# test_search.py — run from backend/
from config import get_qwen_client, QWEN_MODEL

client = get_qwen_client()
resp = client.chat.completions.create(
    model=QWEN_MODEL,
    messages=[{"role": "user", "content": "What major shipping disruptions happened in the Red Sea this week? Cite sources."}],
    extra_body={"enable_search": True},
)
print(resp.choices[0].message.content)