# Security Policy

## Secrets

Never commit `.env`, API tokens, account identifiers, session data, databases, generated user images, or uploaded avatars.

Use `.env.example` only as a template. Store live credentials in the local root `.env` file or in the secret manager provided by the deployment platform.

If a credential is accidentally committed, revoke or rotate it immediately and remove it from Git history before publishing the repository.

## Reporting

For a private project, report security issues directly to the repository owner instead of opening a public issue containing sensitive details.
