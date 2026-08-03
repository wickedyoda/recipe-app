# Security & CI

## Branch protection

- Required status checks match actual jobs in `Verify & Security`
- Required conversation resolution: enabled
- Required linear history: enabled
- Required approving reviews: disabled for solo-contributor workflow

## CI workflow: Verify & Security

- Python Lint
- Python Tests
- Python SAST & Dependencies
- Secrets & Container Scan
- YAML & Compose Validate
- Frontend Validate

## Security findings policy

- Dependency advisories are tracked and remediated where possible
- Code scanning alerts are reviewed instead of dismissed without remediation
- If an alert is a false positive, it should be dismissed with a comment and reasoning
