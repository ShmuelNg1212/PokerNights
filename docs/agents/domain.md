# Domain docs

PokerNights uses one domain context. Before domain exploration, read the root GLOSSARY.md if present and relevant decisions under doc/adr/ if present. If absent, proceed; create them lazily when domain-modeling resolves a term or decision.

Follow the source order in AGENTS.md. Use the glossary's vocabulary in tickets, code, tests, and explanations. A session is GameNight; a set is GameSession. Keep money, units, and settlement meanings consistent with the approved product rules.

Flag contradictions with existing decisions and higher-authority documents. Record new decisions in doc/adr/; preserve historical studies and append dated addenda when findings change. A new decision does not authorize editing SPEC.md.

Run domain-modeling during terminology discussions or architectural decisions. Use grilling to resolve unclear outcomes during study and planning; tdd for behavioral implementation; diagnosing-bugs for difficult failures; and code-review against the approved plan and repository standards before completing implementation. Use each skill at its applicable stage inside the existing approval workflow.
