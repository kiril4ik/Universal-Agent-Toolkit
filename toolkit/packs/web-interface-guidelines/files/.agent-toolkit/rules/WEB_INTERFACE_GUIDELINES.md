# Web Interface Guidelines

Use this checklist when implementing/reviewing web UI.

## Accessibility
- Icon-only buttons need accessible names.
- Form controls need real labels or an accessible label.
- Use semantic HTML before ARIA.
- Keyboard access and visible `:focus-visible` states are mandatory.
- Images need meaningful `alt` or empty alt when decorative.
- Async validation/toasts should be announced appropriately.
- Keep heading hierarchy sensible and do not disable zoom.

## Forms
- Use correct input types, names, autocomplete/inputmode.
- Never block paste.
- Keep labels clickable.
- Show errors next to fields and focus the first invalid field on submit.
- Warn about unsaved changes when navigation can lose work.

## Motion
- Honor `prefers-reduced-motion`.
- Prefer transform/opacity animation; avoid `transition: all`.
- Motion must be interruptible and should communicate state/spatial relationships.

## Layout/content
- Handle long/empty content deliberately.
- Prevent horizontal overflow rather than hiding symptoms globally.
- Use flex/grid before JavaScript layout measurement.
- Explicitly size images to avoid layout shift.
- Large lists should be virtualized only when size/performance justifies it.

## Navigation/state
- Important filters/tabs/pagination should be deep-linkable when users need to share/restore state.
- Use links for navigation and buttons for actions.
- Destructive UI actions need confirmation or an undo window.

## Touch
- Provide adequate touch targets.
- Gesture-only actions require click/tap/keyboard alternatives unless the gesture is inherently essential.

## Locale
- Use locale-aware date/number/currency formatting.
- Do not infer language from IP when browser/user settings are available.

## Content
- Use clear active copy and specific action labels.
- Error messages should tell the user what to do next.

**Source:** Vercel `web-interface-guidelines`, pinned in `vendor/SOURCES.md`.
