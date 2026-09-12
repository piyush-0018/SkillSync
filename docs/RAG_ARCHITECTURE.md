# SkillSync Career Assistant: RAG Architecture

## Overview

The SkillSync Career Assistant uses Retrieval-Augmented Generation (RAG) to answer career questions with evidence from the authenticated student's own SkillSync data. Instead of sending every stored record to the language model, the system retrieves only the pieces that are most relevant to the current question.

```text
User question
    -> question embedding
    -> user-scoped similarity search
    -> relevant SkillSync context
    -> grounded prompt + recent conversation
    -> local language model
    -> personalized answer
```

The searchable knowledge can include the user's profile and target role, parsed resume sections, skills, projects, education, resume analysis, saved job descriptions, and job-match results.

## 1. Document preparation

Application records are first converted into small, readable documents. For example, a project, an education entry, and the missing-skills section of a job match become separate pieces of source material rather than one very large block.

Each document keeps metadata such as:

- the authenticated user who owns it;
- its source type, such as resume, analysis, profile, or job match;
- the source record and chunk position;
- the embedding model used;
- information used to detect when the source has changed.

This metadata supports traceability, safe refreshes, and user-level isolation.

## 2. Chunking

Chunking divides a long document into smaller, meaning-preserving passages. Small chunks improve retrieval because one vector represents a focused topic instead of an entire resume containing many unrelated topics.

SkillSync keeps related content together where possible, such as one project or one group of recommendations. A small overlap can be used between long neighbouring chunks so an important sentence is not lost at a boundary.

Chunking does not summarize or invent content. It only changes how existing data is prepared for search.

## 3. Embeddings

An embedding is a list of numbers that represents the semantic meaning of text. Texts with similar meanings tend to have vectors that point in similar directions, even when they do not use exactly the same keywords.

SkillSync uses Google's `gemini-embedding-001` model with a configured 768-dimensional output. The same embedding model and dimensions must be used for stored chunks and incoming questions; vectors from different models are not directly comparable.

Embeddings are useful here because a question such as "What should I learn for backend development?" can retrieve resume skills and job requirements related to APIs, databases, and server-side development without requiring an exact phrase match.

## 4. PostgreSQL vector storage

PostgreSQL stores each chunk, its ownership and source metadata, and its 768-number embedding. This keeps the searchable knowledge tied to the same database records as the rest of SkillSync.

The default `RAG_VECTOR_BACKEND=python` stores embeddings as JSON and performs exact cosine comparison in Python. The optional `pgvector` mode retains that same storage but casts embeddings to vector expressions and ranks cosine similarity inside PostgreSQL. It requires the server extension to be enabled; see [deployment instructions](DEPLOYMENT.md). Neither mode currently uses approximate indexes or a native vector column.

This approach is practical for a final-year project because each user has a relatively small number of chunks. Exact comparison examines every eligible chunk and does not sacrifice recall for speed.

## 5. Strict user isolation

User isolation is part of the retrieval query, not a filter added after retrieval.

1. Authentication determines the current user's ID on the backend.
2. The client does not choose or submit an arbitrary owner ID.
3. PostgreSQL selects only chunks belonging to that authenticated user and the active embedding model.
4. Cosine similarity is calculated only over those selected rows.
5. Conversation reads, updates, clearing, and message creation are also scoped to the same authenticated user.

Therefore, another user's vector never enters the candidate set for a question. Cross-user tests should remain part of the test suite because a missing ownership condition is a security defect, not merely a relevance problem.

## 6. Exact cosine retrieval

The question is embedded into the same 768-dimensional space as the stored chunks. SkillSync then calculates cosine similarity between the question vector and every eligible user-owned chunk:

```text
cosine_similarity(A, B) = (A . B) / (length(A) * length(B))
```

A higher value means the texts are more semantically related. The best-ranked chunks are selected, with limits on both the number of chunks and total context size. These limits keep the prompt focused and prevent unnecessary model latency.

Keyword search alone can miss equivalent wording. Vector search is used because it retrieves by meaning, while source metadata preserves the connection back to the student's actual data.

## 7. Context and prompt construction

The generation prompt contains four distinct parts:

1. **System rules** — require factual grounding, prohibit invented resume details, and define how missing information must be handled.
2. **Retrieved context** — selected chunks with clear source labels.
3. **Recent conversation history** — enough previous messages to understand follow-up questions without allowing the prompt to grow indefinitely.
4. **Current question** — the student's latest request.

Retrieved resumes and job descriptions are treated as untrusted data, not instructions. Delimiting and labelling them helps resist attempts to override system rules, but does not guarantee immunity to prompt injection.

Only the selected context reaches the language model. The full database is never placed into the prompt.

## 8. Grounded and general guidance

The assistant distinguishes two kinds of statements:

- **Grounded guidance** is supported by retrieved SkillSync data and should be described as based on the user's profile, resume, analysis, or saved job match.
- **General guidance** is career knowledge that does not come from the user's records and should be identified as general advice.

If the required fact is absent, the assistant says that the information is unavailable. For example, it must not invent work experience when the resume contains none. It can still offer clearly labelled general steps that may help.

This distinction makes the answer explainable: the student can tell what came from personal data and what came from the model's broader knowledge.

## 9. Conversation history

Conversations and messages are stored separately from knowledge chunks. History makes follow-up questions such as "Which one should I improve first?" understandable.

Only a bounded number of recent messages is included during generation. Older messages remain available to display but do not expand every prompt indefinitely. Clearing a conversation removes its messages for that authenticated user without deleting resume or job-match knowledge.

Conversation history supports continuity, while retrieval supplies current factual evidence. They solve different problems.

## 10. Why this is different from a normal chatbot

A normal chatbot answers mainly from patterns learned during model training and the text currently typed into the chat. It does not automatically know a student's latest resume, analyses, target role, or saved job descriptions.

SkillSync adds a retrieval stage before generation. It searches the student's current data, selects relevant evidence, and supplies that evidence to the language model. As a result, answers can be personalized and updated without retraining the model whenever the resume or a job description changes.

In one sentence:

> A normal chatbot generates from general model knowledge, while SkillSync RAG first retrieves user-owned evidence and then generates a response grounded in that evidence.

## 11. Security and reliability considerations

- LLM and embedding requests are made by the backend; the frontend does not receive database credentials.
- Ownership comes from the authenticated session, not request data.
- Database queries apply ownership constraints before similarity ranking.
- Embedding dimensions and model names are validated to avoid comparing incompatible vectors.
- Source changes trigger re-indexing so stale chunks are replaced rather than mixed with current content.
- Prompt size and conversation history are bounded for predictable performance.
- Retrieved user content is treated as untrusted prompt data.
- If Gemini is unavailable or generation fails, the API reports an error instead of returning fabricated guidance.

## 12. Current pgvector option and future indexed storage

The current opt-in SQL mode computes cosine ranking using JSON-to-vector casts and preserves both chunk and document owner filters. `deploy/init-vector.sql` enables the required extension. No schema backfill is needed; reverting to Python ranking preserves stored data. A real PostgreSQL integration test is provided separately from SQLite tests. This mode remains exact and scans the eligible corpus.

For future native indexed storage, a reviewed migration can:

1. Install/enable the pgvector extension compatible with the chosen PostgreSQL version.
2. Enable it in the SkillSync database with `CREATE EXTENSION vector`.
3. Add a `vector(768)` column and copy or regenerate existing embeddings.
4. Use pgvector cosine distance (`<=>`) while retaining the mandatory `user_id` condition.
5. Keep an ordinary index on ownership columns.
6. Add an approximate HNSW index only when the number of chunks justifies its memory and recall trade-offs.

The future retrieval shape remains:

```sql
SELECT ...
FROM career_chunks
WHERE user_id = :authenticated_user_id
  AND embedding_model = :active_model
ORDER BY embedding <=> :question_embedding
LIMIT :context_limit;
```

The sketch omits the parent-document join for brevity; production queries must retain both ownership predicates. Tenant filtering is always part of the database query. Native vector storage and indexing may improve larger-scale search but require measurement; pgvector does not replace authentication or ownership checks.

## Summary

- **Embeddings** turn text meaning into comparable numeric vectors.
- **Chunking** creates focused searchable passages from larger records.
- **Vector retrieval** finds relevant personal evidence by semantic similarity.
- **User scoping** ensures only the authenticated student's chunks are candidates.
- **Prompt construction** combines system rules, retrieved evidence, recent history, and the question.
- **Grounding** reduces unsupported claims but cannot eliminate them.
- **RAG** personalizes current answers without retraining the language model.
- **Current storage** uses PostgreSQL JSON vectors with Python cosine search by default, or optional pgvector SQL cosine ranking through casts.
- **Scale-up path** replaces JSON with `vector(768)` and pgvector cosine search while preserving the same isolation rules.
