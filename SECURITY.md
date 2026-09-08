# 🔒 Security Policy — Zevion

## Reporting a Vulnerability

If you discover a security vulnerability, please **do not open a public issue**.

Instead, report it privately by opening a draft security advisory on GitHub
(Security → Advisories → New draft advisory), or contact the maintainers directly.

We will respond as quickly as possible and aim to publish a fix before public disclosure.

---

## Security Model

Zevion is a desktop automation tool that executes actions on the user's own
computer. Its safety model is **defense-in-depth** — multiple independent layers
ensure destructive actions cannot run accidentally:

### 1. Hard-Block List
Destructive/system-killer commands (`rm -rf`, `format`, `diskpart`, `bcdedit`,
`taskkill /f`, `del /s`, …) are **never executed**, even with manual approval.
They are re-checked at three independent code layers (SafetyGuard → API dispatch →
DesktopController) so no code path can bypass them.

### 2. System Path Protection
Write/delete into protected system locations (`C:\Windows`, `Program Files`,
`/etc`, `/usr`, `/bin`, …) is automatically blocked. User folders with similar
names (e.g. `~/bin`) are **not** affected.

### 3. Chained Command Detection
Commands using `&&`, `;`, `|`, `||` always require manual confirmation, because a
dangerous command can hide behind a safe one.

### 4. Delete → Recycle Bin
File deletion sends items to the Recycle Bin (recoverable) by default, never a
permanent delete unless explicitly requested.

### 5. Tiered Risk Classification
- **Safe** — runs automatically
- **Moderate** — mode-dependent
- **Dangerous** — mandatory confirmation modal
- **Blocked** — never runs

Plus **Dry-Run mode** (show but don't run) and **Plan-Then-Do mode** (multi-step
plans require approval).

---

## API Key Handling

- API keys are stored locally on the user's machine and **never** logged, printed,
  or returned by the API.
- All keys are masked (e.g. `sk-a••••••••2345`) and redacted from audit logs via
  `sanitize_safe_payload()`.
- The `.gitignore` excludes all credential files (`.env`, `*.key`, `*.pem`).
- Use `.env.example` as a template — never commit real keys.

---

## Responsible Disclosure Guidelines

Please include:
- A clear description of the vulnerability
- Steps to reproduce
- Affected component(s)
- Suggested impact/severity

We appreciate responsible disclosure and will credit reporters where applicable.
