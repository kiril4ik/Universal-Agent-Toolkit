# Interaction Modes

Before project discovery questions, establish one mode and save it in `.agent-toolkit/project.json`.

## Thorough
Ask every question whose answer would materially improve scope, business logic, architecture, design, security, deployment, or implementation. Group related questions; never ask what repository evidence already answers.

## Focused — default
Ask only important/blocking questions. For minor preferences and reversible choices, choose a conventional default and record the assumption.

## Autonomous
Do the work independently. Infer intent from repository evidence, requirements, established patterns, and reasonable defaults. Ask only when:
- materially different interpretations would produce different products;
- required credentials/access are missing;
- the action is destructive, irreversible, externally visible, costly, or security-sensitive;
- a legal/compliance requirement cannot safely be assumed.

Autonomous mode never bypasses data-safety, deployment, credential, deletion, or external-action gates.
