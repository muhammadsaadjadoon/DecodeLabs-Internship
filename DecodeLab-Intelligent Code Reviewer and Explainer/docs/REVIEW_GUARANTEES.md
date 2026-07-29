# Review Guarantees and Non-Guarantees

## Guarantees Implemented by the Platform

- Unsupported or mismatched uploaded file types are rejected before AI review.
- Available deterministic syntax evidence is included in the final decision.
- Corrected output is validated again before delivery.
- Invalid model corrections are not silently presented as verified.
- Byte-identical previously verified clean source is recognized through a SHA-256 fingerprint.
- Findings and corrections are preserved in an auditable server-side session.
- The exact original-to-corrected change set is available as a unified diff.
- Exported reports contain review metadata, findings, corrected code, and verification evidence.

## Responsible Limitations

- Static analysis cannot prove all runtime behavior.
- Dependency versions, environment variables, external services, databases, and framework configuration may change program behavior.
- AI-assisted findings require developer judgment, especially for architecture, concurrency, security, and business logic.
- A syntactically valid correction is not automatically equivalent to comprehensive test coverage.

## Recommended Production Gate

Before deployment, run the corrected source through:

1. the project test suite;
2. formatting and linting;
3. dependency and security scanning;
4. type checking where applicable;
5. staging execution with representative inputs;
6. human code review.
