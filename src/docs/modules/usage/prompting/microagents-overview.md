# Microagents Overview

Microagents are specialized prompts that enhance TeAI with domain-specific knowledge, repository-specific context
and task-specific workflows. They help by providing expert guidance, automating common tasks, and ensuring
consistent practices across projects.

## Microagent Types

Currently TeAI supports the following types of microagents:

* [Repository Microagents](./microagents-repo): Repository-specific context and guidelines for TeAI.
* [Public Microagents](./microagents-public): General guidelines triggered by keywords for all TeAI users.

When TeAI works with a repository, it:

1. Loads repository-specific instructions from `.teai/microagents/` if present in the repository.
2. Loads general guidelines triggered by keywords in conversations.
See current [Public Microagents](https://github.com/All-Hands-AI/TeAI/tree/main/microagents/knowledge).

## Microagent Format

All microagents use markdown files with YAML frontmatter that have special instructions to help TeAI accomplish
tasks:
```
---
name: <Name of the microagent>
type: <MicroAgent type>
version: <MicroAgent version>
agent: <The agent type (Typically CodeActAgent)>
triggers:
- <Optional keywords triggering the microagent. If triggers are removed, it will always be included>
---

<Markdown with any special guidelines, instructions, and prompts that TeAI should follow.
Check out the specific documentation for each microagent on best practices for more information.>
```
