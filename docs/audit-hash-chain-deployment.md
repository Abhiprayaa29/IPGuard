# Audit Hash Chain deployment note

The application enforces append-only behavior in the audit service and rejects
ORM updates/deletes for `AuditEvent`. This is an application-layer control. A
database client with direct write privileges can bypass the service hooks.

For deployment, use separate database identities:

- The runtime identity needs `SELECT` and `INSERT` on `audit_events`; it should
  have no `UPDATE` or `DELETE` privilege on that table.
- The runtime identity needs `SELECT`, `INSERT`, and `UPDATE` on
  `audit_chain_heads` to lock and advance the chain head. It should not need
  `DELETE` on chain heads.
- The migration/administration identity applies Alembic migrations and manages
  grants. Do not use this identity as the API or worker runtime identity.

This repository currently reads one `database_url` setting for application and
Alembic connections and does not provision these roles or grants. Configure the
separate identities and least-privilege grants in deployment infrastructure;
this feature does not assume role names or create role-specific migrations.

The hash chain is tamper-evident while an attacker cannot rewrite the events,
head, and any trusted checkpoint together. A database owner or host
administrator may be able to recompute the chain. This feature does not claim
tamper-proof or immutable storage, and it does not provide an external trust
anchor.
