# Security Policy

QKDpy is a **research and educational simulator** of Quantum Key
Distribution. It models QKD protocols, channels, satellite links, and
attacks with phenomenological approximations. It is **not** a hardened
cryptographic module and **must not** be used to protect real key
material in production environments.

---

## Scope

### In scope for security reports

- Disclosure of hardcoded credentials, tokens, or secrets in the source
  tree or documentation.
- Clear-text logging or exposure of key material (simulated or real)
  beyond what the API documents.
- Code or configuration that could aid an attacker in compromising
  a user's environment (e.g., command injection, insecure deserialization,
  arbitrary file writes).
- Weak cryptographic primitives in the `qkdpy.crypto` module that are
  presented as reference implementations without adequate warning.

### Out of scope

- Attacks requiring physical access to the user's machine.
- Social engineering of the project's maintainers or users.
- Denial-of-service against the GitHub repository or CI infrastructure.
- Theoretical attacks on QKD protocols that the library is modelling
  (these belong in academic peer review, not a security tracker).

---

## Supported Versions

Only the **latest release** on PyPI receives security patches.
Older versions are not backported.

| Version | Supported |
|---------|-----------|
| Latest  | ✅ |
| Older   | ❌ |

Users of the Enterprise or Premium tiers should contact the maintainer
directly through the agreed commercial support channel.

---

## Reporting a Vulnerability

**Do not open a public GitHub issue.**

To report a security vulnerability, use GitHub's private disclosure
workflow:

1. Go to https://github.com/Pranava-Kumar/qkdpy/security/advisories
2. Click **"Report a vulnerability"**
3. Fill out the form with a clear description, reproduction steps, and
   the potential impact

You will receive an acknowledgement within **72 hours**. The maintainer
will work with you to understand the issue, assess severity, and plan a
fix. After a patch is released, you will be credited in the advisory
(unless you prefer to remain anonymous).

For **Enterprise / Premium** license holders, you may additionally
report through your designated support channel for faster triage.

---

## Disclosure Timeline

| Event | Target |
|-------|--------|
| Initial acknowledgement | 72 hours |
| Triage and severity assessment | 5 business days |
| Patch release (CRITICAL / HIGH) | 14 days from triage |
| Patch release (MEDIUM / LOW) | Next regular release cycle |
| Public advisory on GitHub | Same day as patch release |

If the maintainer cannot reproduce or validate the report within the
triage window, the issue may be closed with an explanation.

---

## Preferred Languages

Reports in **English** are preferred. If English is a barrier, reports
in the maintainer's native languages are also accepted.

---

## Thanks

We appreciate the community's help in keeping QKDpy safe. Please
report responsibly and give us time to fix issues before disclosure.
