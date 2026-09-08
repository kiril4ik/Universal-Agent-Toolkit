# 06 - Stack

Choose the technologies, and write down why. Skip only when the stack is
already fixed by an existing codebase or an explicit requirement.

## Decide from constraints, not preference

Constraints that legitimately drive the choice:

- What the team already knows and maintains
- What the existing codebase already is
- Where it must be deployed, and by whom
- Real scale and latency requirements - measured or estimated, not imagined
- Compliance, data residency, procurement rules
- Budget, including the cost of managed services
- How long this must be maintained, and by how many people

"It is popular" and "I like it" are not constraints.

## Decide these explicitly

Language and runtime; framework; database; migrations tool; cache; queue and
background jobs; search; file and object storage; authentication and session
strategy; API style; frontend framework; styling approach; component library;
build tool; test frameworks at each level; linter and formatter; static
analysis; container strategy; web server and reverse proxy; CI; hosting;
logging, metrics and error tracking.

For each: what you chose, the alternative you seriously considered, and the
one-line reason. If you cannot name a real alternative, you have not made a
decision - you have made an assumption.

## Pin versions

Record the actual major and minor versions you are targeting. Rules and best
practices are version-specific; "React" is not a version, and advice for
React 17 can be actively wrong for React 19.

## Bias toward boring

Prefer technology that is well-documented, widely deployed, and easy to hire
for. Novelty is a cost paid by whoever maintains this next. Reserve it for the
one or two places where it genuinely buys something.

Prefer fewer moving parts. Every service in the architecture is a thing that
can be down at 3am. A background job table in the database you already run
beats a message broker you do not need yet.

## Output

`docs/stack.md` - the choices, versions, rationale, and rejected alternatives.

Plus `.agent-toolkit/reports/06-stack.md`.
