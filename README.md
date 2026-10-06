# XYNES API documentation

This repository contains Markdown/MDX API reference source. It has no application
package, dependency lockfile or configured MDX renderer. Security remediation
uses `feature/security-audit-remaining-high-medium` based on `main`, the explicitly
approved exception to the workspace's usual `develop` base.

CI validates the source without evaluating MDX, executing examples or requesting
external URLs:

```bash
python3 .github/ci/docs-check.py
PYTHONDONTWRITEBYTECODE=1 python3 .github/ci/docs-check.test.py
PYTHONDONTWRITEBYTECODE=1 python3 .github/ci/docs-check.test.py --coverage
python3 .github/ci/docs-check.py --manifest
```

The validator checks tracked UTF-8 document bytes, bounded regular files, local
link containment/existence, symlink rejection and allowed URL schemes. It emits
a deterministic source manifest with per-file SHA-256 hashes. Regression tests
exercise success and malformed/path/link/CLI rejection. The native Python trace
gate enforces 80% executable-line coverage for this validator; it does not claim
function/branch coverage or coverage of Markdown, YAML or existing API behavior.
Fragment anchor correctness, MDX compilation/rendering and remote link health
are not established by these checks.

Generated CI/provenance TypeScript mirrors come from backend infra's canonical
policy and are strictly typechecked with an immutable platform-contracts tool
checkout and frozen pnpm install. No dependencies are installed in this docs
repository. Required checks are `lint`, `test`, `coverage`, `build`, `typecheck`
and `security`; immutable actions and read-only PR jobs enforce workflow policy.

The prepared manual release workflow requires protected `main`, actual successful
app-bound checks on the exact source commit, approved `release` environment and
read-only policy access. Its artifact is tracked `.md`/`.mdx` documentation plus
`LICENSE`, not a rendered site or application binary. A separate restricted job
attests the same-run digest. No workflow has been dispatched or provenance
published during local preparation.

Protection/provenance setup and independent verification are described in
`xynes/xynes-infra/infra/release/CI-PROVENANCE.md` in the workspace. API-docs main
policy preparation uses infra's `scripts/setup/ci-api-docs-repos.json`; remote
application and any existing GitHub ruleset reconciliation need separate
authorization. Existing reference content is preserved by this CI change.
