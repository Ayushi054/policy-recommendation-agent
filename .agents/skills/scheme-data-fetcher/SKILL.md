---
name: scheme-data-fetcher
description: Fetches relevant Indian central and state government scheme data based on sector/domain and target beneficiaries.
---

# Scheme Data Fetcher Skill

This skill guides the agent in searching and fetching government scheme data, using available tools like MCP tools, Web search, or built-in knowledge.

## Instructions
1. Map the user's domain (e.g. healthcare, education) to standard government sectors.
2. Use tools to search for matching schemes in the target State/UT or Central government.
3. Retrieve details such as eligibility, funding details, components, and implementation guidelines.
4. Supply retrieved schemes as reference context to the gap analysis and recommendation stages.

### Search and Query Strategy
- Prioritize central schemes (e.g., Centrally Sponsored Schemes) and state-specific policies.
- Retrieve full descriptions, budget, target beneficiaries, eligibility rules, and executing ministry.
- Leverage the custom `myscheme-mcp` tools when available.
