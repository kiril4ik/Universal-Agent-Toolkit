# FastAPI Rules
- Use Pydantic models for validated request/response boundaries.
- Keep authorization explicit at route/dependency boundaries.
- Do not perform blocking I/O inside async routes without appropriate offloading.
- Keep DB sessions/transactions scoped and closed reliably.
- Return stable API error shapes and test auth/validation/edge cases.
