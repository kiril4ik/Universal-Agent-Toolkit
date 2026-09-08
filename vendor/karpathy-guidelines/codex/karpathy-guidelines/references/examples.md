# Examples — Karpathy Guidelines in Practice

Real-world examples demonstrating the four principles. Each shows what agents commonly do wrong and how to fix it.

---

## 1. Think Before Acting

### Hidden Assumptions

**❌ Wrong:** "Add a feature to export user data" → immediately writes code that exports ALL users to a JSON file, picking fields and location without asking.

**✅ Right:**
```
Before implementing, I need to clarify:
1. Scope: Export all users or filtered subset?
2. Format: Download file, background job, or API endpoint?
3. Fields: Which ones? Some might be sensitive.
4. Volume: How many users? Affects pagination approach.

Simplest approach: API endpoint returning paginated JSON.
What's your preference?
```

### Multiple Interpretations

**❌ Wrong:** "Make the search faster" → immediately adds caching + DB indexes + async processing without asking which "faster" matters.

**✅ Right:**
```
"Make the search faster" could mean:
1. Faster response time (< 100ms) — DB indexes, caching
2. Higher throughput — async, connection pooling
3. Faster perceived speed — progressive loading, partial results

Current search: ~500ms. Which aspect matters most?
```

---

## 2. Simplicity First

### Over-abstraction

**❌ Wrong:** "Add a function to calculate discount" → Strategy pattern with ABC, Protocol, dataclass, enum — 30+ lines of setup for a simple percentage calculation.

**✅ Right:**
```python
def calculate_discount(amount: float, percent: float) -> float:
    return amount * (percent / 100)
```
Add complexity only when you actually need multiple discount types.

### Speculative Features

**❌ Wrong:** "Save user preferences to database" → PreferenceManager class with caching, validation, merging, notification hooks — 50+ lines for features nobody asked for.

**✅ Right:**
```python
def save_preferences(db, user_id: int, preferences: dict):
    db.execute("UPDATE users SET preferences = ? WHERE id = ?",
               (json.dumps(preferences), user_id))
```
Add caching, validation, merging only when the need actually arises.

---

## 3. Surgical Changes

### Drive-by Refactoring

**❌ Wrong:** "Fix the bug where empty emails crash the validator" → also improves email validation regex, adds username length check, changes comments, adds docstring.

**✅ Right:** Only change the specific lines that fix empty email handling. Nothing else.

### Style Drift

**❌ Wrong:** "Add logging to the upload function" → also changes quote style ('' → ""), adds type hints, adds docstring, reformats whitespace, changes boolean return logic.

**✅ Right:** Add logging statements matching existing style (single quotes, no type hints, existing pattern). Match, don't reformat.

---

## 4. Goal-Driven Execution

### Vague vs. Verifiable

**❌ Wrong:** "Fix the authentication system" → "I'll review the code, identify issues, make improvements, test changes." No clear criteria.

**✅ Right:**
```
To "fix authentication," I need success criteria. What specific issue?

If the issue is "users stay logged in after password change":
Plan:
1. Write test: Change password → verify old session invalidated ✓ Test fails (reproduces)
2. Implement: Invalidate sessions on password change ✓ Test passes
3. Check edge cases: Multiple sessions, concurrent changes ✓ Additional tests pass
4. Verify no regression: Existing auth tests ✓ Full suite green
```

### Fix Without Reproducing

**❌ Wrong:** "The sorting breaks with duplicate scores" → immediately changes sort logic without confirming the bug exists.

**✅ Right:** First write a test that reproduces the issue, verify it fails, then fix, then verify the test passes.

---

## Anti-Patterns Summary

| Principle | Anti-Pattern | Fix |
|-----------|-------------|-----|
| Think Before Acting | Silently assumes file format, fields, scope | List assumptions, ask for clarification |
| Simplicity First | Strategy pattern for a single calculation | One function until complexity is actually needed |
| Surgical Changes | Reformats quotes, adds type hints while fixing bug | Only change lines that fix the reported issue |
| Goal-Driven | "I'll review and improve the code" | "Write test for bug X → make it pass → verify" |

## Key Insight

The "overcomplicated" examples aren't obviously wrong — they follow design patterns and best practices. The problem is **timing**: complexity before it's needed makes things harder to understand, introduces more bugs, takes longer, and is harder to test.

**Good solutions solve today's problem simply, not tomorrow's problem prematurely.**
