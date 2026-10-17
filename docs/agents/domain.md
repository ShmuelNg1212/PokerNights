# Domain docs

PokerNights uses one domain context. Before domain exploration, read the root GLOSSARY.md if present and relevant decisions under doc/adr/ if present. If absent, proceed; create them lazily when domain-modeling resolves a term or decision.

Use the glossary's vocabulary in code, tests, plans, and explanations. A session is GameNight; a set is GameSession. Keep money, units, and settlement meanings consistent with doc/wiki/spec.md.

Flag contradictions with existing decisions and with doc/wiki/spec.md. Record new decisions in doc/adr/. A change to product intent in spec.md needs human approval.
