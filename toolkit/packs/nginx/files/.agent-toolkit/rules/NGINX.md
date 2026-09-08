# Nginx Rules
- Inspect existing virtual hosts/includes before editing an existing server.
- Keep each application's config scoped; do not replace unrelated global config.
- Validate with `nginx -t` before reload.
- Prefer reload over restart after a valid config change.
- Configure TLS/security headers/proxy timeouts/body limits from application requirements.
- Back up important existing config before high-risk changes.
