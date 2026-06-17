# Security Policy

## Scope

This repository is a deterministic EU AI Act triage engine with a local CLI, MCP surface and optional local cockpit. Public demos should use synthetic AI-system profiles only.

## Sensitive Data Surfaces

The tool can process system descriptions, intended-purpose facts, actor roles, deployment context, generated draft artifacts, source manifests and local reviewer notes.

## Required Controls

1. Do not commit client system inventories, confidential product descriptions or privileged assessments.
2. Use synthetic examples for public demos and portfolio screenshots.
3. Keep generated artifacts out of public commits unless they are synthetic and clearly labelled.
4. Treat source manifests as legal-source metadata, not proof that all legal status labels remain current.
5. Do not add current-law claims without checking primary sources.

## Reporting

Report suspected vulnerabilities privately through the maintainer's GitHub profile contact details. Include the affected path, impact and reproduction steps. Do not open public issues for suspected confidential intake data or credential leaks.
