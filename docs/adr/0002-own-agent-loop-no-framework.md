# Own agent loop and retrieval, no agent framework

We write the agent loop, Capability calling and hybrid retrieval (BM25 + pgvector, merged by Reciprocal Rank Fusion) ourselves instead of using LangChain or LangGraph. LangGraph's checkpoints and interrupts would duplicate what Temporal already owns (ADR 0001), and the purpose of this project is to understand every step of the loop. Retrieval sits behind a `Retriever` interface so a framework retriever can be plugged in later for comparison.

## Considered Options

- LangChain for retrieval only: saves about a day, but adds a fast-moving dependency for roughly 150 lines of code.
- LangGraph for the whole agent: rejected; two durability systems and a hidden control flow.
