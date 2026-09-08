# 03 - Screens and flows

Turn the domain into the concrete surface a user touches. Skip only when
there is genuinely no user interface.

## Enumerate the surface

List every screen, page, modal and email. For each one:

- **Route / identifier** and who can reach it
- **Purpose** in one sentence - if you cannot write it, the screen is wrong
- **Data shown**, and where each piece comes from
- **Actions available**, and what each one does
- **Entry points** - how a user arrives here
- **Exits** - where they go next

## Every screen has five states

Design all five, or you will ship one and discover the other four in
production:

1. **Empty** - no data yet. Often a user's first impression. What does it say?
2. **Loading** - what shows while waiting? Skeleton, spinner, nothing?
3. **Partial** - some data, some still loading, or some failed.
4. **Error** - what failed, what the user can do about it, how to retry.
5. **Full** - the happy path everyone designs first.

Also: what happens at 10,000 rows? Pagination, virtualisation, or a limit?

## Forms need their own pass

For every form: fields, types, required vs optional, validation rules,
when validation fires, error message wording, what happens on submit, what
happens on submit failure, and whether partial input survives a reload.

## Flows

Map the multi-screen journeys end to end:

- The primary journey - the thing the product is for
- Sign up, sign in, password reset, sign out
- The payment or conversion path, if there is one
- Recovery paths - what a user does after something goes wrong

For each flow: the steps, the decision points, where a user can abandon and
resume, and what happens if they refresh mid-flow.

## Permissions on the surface

For each screen and action, state what an unauthorised user sees: a 404, a
403, a hidden button, or a disabled one. These are different products and
different security postures. Decide deliberately.

## Responsive and accessible

State the breakpoints and what changes at each. Navigation on small screens
is a design decision, not an afterthought.

Accessibility is a requirement, not a phase: keyboard reachability, focus
order, labels, contrast, and what a screen reader announces.

## Output

`docs/screens.md` - the screen inventory, the state matrix, the flows, and a
route map or sitemap.

Plus `.agent-toolkit/reports/03-screens-and-flows.md`.
