"""
QABuddy.ai — Prompt Templates
System prompts and templates for the QA-focused RAG chatbot.
All prompts enforce citation and grounding.
"""


SYSTEM_PROMPT = """You are QABuddy.ai — an expert QA engineering assistant for our company.
Your knowledge comes from our internal sources: Selenium framework, Playwright framework,
test case repository, JIRA tickets, PRDs, company documents, meeting notes, and Jenkins logs.

## Your Capabilities
- Answer questions about our test automation frameworks (Selenium & Playwright)
- Help with test case creation, review, and gap analysis
- Assist with test failure analysis and root cause analysis (RCA)
- Provide insights from JIRA bug history and ticket data
- Help build Requirements Traceability Matrices (RTM)
- Assist with bug triage and test planning
- Identify flaky tests and suggest fixes
- Help onboard new QA team members

## CRITICAL RULES
1. **Always cite your sources.** Every claim must reference the specific source document,
   file, JIRA ticket, or test case ID where the information comes from.
2. **Use the format [Source: filename or ticket-ID]** for citations.
3. **If the retrieved context does not contain the answer, say so honestly.**
   Do NOT make up information. Say: "I don't have enough information in my knowledge base to answer this."
4. **Stay grounded.** Only use information from the provided context chunks.
5. **Be specific.** Reference exact method names, class names, test case IDs, and file paths.
6. **For code questions**, include relevant code snippets from the context.

## Response Format
- Start with a direct answer
- Support with details from the retrieved context
- End with citations in a "Sources" section
- Use markdown formatting for readability
"""


QA_PROMPT_TEMPLATE = """## Retrieved Context
The following {num_chunks} chunks are the most relevant results from our knowledge base:

{context}

---

## User Question
{question}

---

## Instructions
Answer the user's question based ONLY on the retrieved context above.
- Cite every source using [Source: filename/ticket-ID] format
- If the context doesn't contain enough information, say so clearly
- Be specific: mention exact file names, method names, test case IDs, and JIRA keys
- For code questions, include the relevant code snippet
- End with a "### Sources" section listing all referenced sources
"""


def build_context_block(search_results: list) -> str:
    """
    Build the context block from search results for insertion into the prompt.

    Args:
        search_results: List of reranked search results

    Returns:
        Formatted context string with numbered chunks and metadata
    """
    context_parts = []

    for i, result in enumerate(search_results, 1):
        metadata = result.get("metadata", {})
        source_type = metadata.get("source_type", "unknown")
        source_file = metadata.get("source_file", "unknown")
        title = metadata.get("title", "")
        language = metadata.get("language", "")
        ticket_key = metadata.get("ticket_key", "")

        # Build source label
        if ticket_key:
            source_label = ticket_key
        elif source_file:
            source_label = source_file
        else:
            source_label = source_type

        # Build chunk header
        header_parts = [f"**Chunk {i}**"]
        if title:
            header_parts.append(f"Title: {title}")
        header_parts.append(f"Source: {source_label}")
        header_parts.append(f"Type: {source_type}")
        if language:
            header_parts.append(f"Language: {language}")

        header = " | ".join(header_parts)

        # Format the chunk content
        text = result.get("text", "")

        # Wrap code in code blocks
        if language in ("java", "python", "javascript", "typescript"):
            chunk_content = f"{header}\n```{language}\n{text}\n```"
        else:
            chunk_content = f"{header}\n{text}"

        context_parts.append(chunk_content)

    return "\n\n---\n\n".join(context_parts)


def build_qa_prompt(question: str, search_results: list) -> str:
    """
    Build the full QA prompt with context and question.

    Args:
        question: User's question
        search_results: List of reranked search results

    Returns:
        Complete prompt string ready for LLM
    """
    context = build_context_block(search_results)

    return QA_PROMPT_TEMPLATE.format(
        num_chunks=len(search_results),
        context=context,
        question=question,
    )
