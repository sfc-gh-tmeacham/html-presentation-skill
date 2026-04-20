Research the following topic for a presentation and return a structured brief.

Topic: [TOPIC]
Audience: [AUDIENCE]
Key points to cover: [KEY_POINTS]
Executive mode: [EXEC_MODE — true or false]

## Tools (use all available)

Do not rely on recalled knowledge alone. Actively use every tool available to you:
- **Web search** — find current statistics, news, and third-party sources
- **Glean / internal search** — find internal docs, customer data, and prior presentations
- **MCP tools** — query any connected data sources (Salesforce, Confluence, Jira, etc.)
- **Other skills** — invoke relevant skills if the topic warrants it

If a tool returns no useful result, note that in the brief. Do not substitute silence with invention.

## Accuracy rules (read carefully before writing anything)

**Wrong is 3x worse than unknown.** Do not guess. If you are not confident in a fact, label it
`[INFERRED]` or omit it entirely. A slide that says "we're not sure of the exact figure" is
recoverable. A slide with a wrong number in front of a customer is not.

Label every fact, statistic, example, and quote with one of two tags:
- `[EXTRACTED]` — the information was stated directly in a source you can cite (verbatim or
  close paraphrase). Include the source inline: `[EXTRACTED] (Source: Name, Year/URL)`
- `[INFERRED]` — the information is your synthesis, estimation, or logical inference from
  multiple sources. Include a brief basis: `[INFERRED] (Basis: derived from X and Y)`

For any statistic about a specific named organization (account counts, employee headcount,
revenue, data volumes, growth percentages), ALSO prefix it with `[UNVERIFIED — confirm with
customer]` regardless of its EXTRACTED/INFERRED tag.

If you cannot find a credible source for a claim, say so explicitly rather than inventing one.

Return:
1. 3–5 compelling statistics or data points — each tagged [EXTRACTED] or [INFERRED] with citation
2. 2–3 concrete real-world examples or case studies — each tagged with source
3. 1–2 strong quotes from credible sources — [EXTRACTED] only; do not fabricate quotes
4. Key terminology or concepts the audience needs to know
5. Common objections or questions the audience may raise
6. Suggested narrative arc: problem → insight → solution → outcome

If `exec_mode` is true: restructure the narrative arc as **conclusion → evidence → context** (BLUF
order). The executive already knows the problem — lead with the recommendation, then prove it, then
provide context only if needed.

Be specific. Format as a structured markdown brief. Do not write slide copy — only gather raw material.
