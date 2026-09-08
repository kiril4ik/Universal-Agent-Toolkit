# 07 - Content

Real content, written before the design, because layout that was designed
around placeholder text breaks when real text arrives.

Skip when there is no user-visible copy.

## No lorem ipsum

Write the actual words. Placeholder text hides three problems until they are
expensive: real copy is longer than you think, real names break your layout,
and writing the copy usually reveals a missing feature.

## What to produce

- **Interface copy** - buttons, labels, headings, menu items, tooltips.
- **Empty states** - what the screen says before there is data. This is
  where a product explains itself.
- **Error messages** - what went wrong, in the user's terms, and what to do
  next. Never expose a stack trace or an error code alone.
- **Confirmation and success messages.**
- **Transactional emails and notifications** - subject lines included.
- **Legal and boilerplate** - the pages you need but forget until launch.

## Voice

Decide and write down: formal or casual, how you address the user, how you
handle errors (apologetic or matter-of-fact), sentence case or title case.
One paragraph is enough; consistency matters more than sophistication.

## Realistic seed data

Produce fixture data that looks like production, not `test1 / test2 / test3`:

- Names of varied length, including non-Latin scripts and long ones
- Realistic amounts, dates spread across a real range, plausible statuses
- Records at the boundaries: the empty one, the maximal one, the one with
  every optional field missing
- Enough rows to make pagination and sorting visibly work

Realistic data catches layout, sorting and encoding bugs during development
rather than after launch.

## Output

`docs/content/` - copy organised per screen or per flow, plus the voice note,
plus seed data (or the script that generates it).

Plus `.agent-toolkit/reports/07-content.md`.
