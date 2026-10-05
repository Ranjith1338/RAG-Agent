# College FAQ RAG agent

This is a small retrieval-augmented FAQ agent that answers questions from a
college CSV database. It uses only Python's standard library, so it can run
without an API key or external service.

## Run it

```powershell
python college_rag.py
```

Ask a question such as `How do I pay tuition fees?`, or type `exit` to quit.

## Connect the real college database

Replace `data/college_faq.csv` with an export containing these columns:

| Column | Description |
| --- | --- |
| `id` | Stable FAQ or record identifier |
| `category` | Department or topic |
| `question` | The question users may ask |
| `answer` | The verified college answer |
| `keywords` | Optional terms separated with `\|` |

The agent returns a fallback instead of inventing an answer when no FAQ has
enough lexical overlap with the question. Responses include the matching FAQ
IDs so staff can trace the source.
