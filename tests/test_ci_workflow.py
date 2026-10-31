"""The public playground deploys from CI, and only after the check jobs pass.

GitHub Pages serves `docs/` on `main`. With the branch as the Pages source, a push
publishes before CI finishes, so a red merge reaches the public playground. The
`deploy` job in `.github/workflows/ci.yml` publishes instead, after `test` and
`web` pass for the same commit. The `web` job also fails on a high or critical
npm advisory in the cockpit's lockfile. These tests read the workflow as text:
the repository has no YAML parser, and the shape checked here is plain block YAML.
"""

from __future__ import annotations

import re
from pathlib import Path

WORKFLOW = Path(".github/workflows/ci.yml")
DEPLOYMENT = Path("DEPLOYMENT.md")
CHECK_JOBS = {"test", "web"}
PUSH_TO_MAIN = "github.event_name == 'push' && github.ref == 'refs/heads/main'"
# A job `if:` without a status function runs only when every needed job succeeded.
STATUS_FUNCTIONS = ("always()", "failure()", "cancelled()", "success()")
PINNED_ACTION = re.compile(r"[\w.-]+/[\w.-]+(?:/[\w./-]+)?@[0-9a-f]{40}")
NPM_AUDIT = "npm audit --audit-level=high"


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _block(lines: list[str], key: str, indent: int) -> list[str]:
    """Return the lines nested under `key:` at `indent`."""
    header = " " * indent + f"{key}:"
    assert header in lines, f"no `{key}:` at indent {indent} in {WORKFLOW}"
    body = []
    for line in lines[lines.index(header) + 1 :]:
        if line.strip() and _indent(line) <= indent:
            break
        body.append(line)
    return body


def _scalars(lines: list[str], indent: int) -> dict[str, str]:
    """Return the `key: value` pairs at exactly `indent`, without trailing comments."""
    pairs = {}
    for line in lines:
        if _indent(line) != indent or ":" not in line:
            continue
        key, _, value = line.strip().partition(":")
        pairs[key] = value.split(" #")[0].strip()
    return pairs


def _steps(job: list[str]) -> list[dict[str, object]]:
    """Return each step of a job as its scalars plus its `with:` scalars."""
    items: list[list[str]] = []
    for line in _block(job, "steps", 4):
        if line.startswith("      - "):
            items.append([line.replace("- ", "  ", 1)])
        elif items:
            items[-1].append(line)
    steps: list[dict[str, object]] = []
    for item in items:
        step: dict[str, object] = dict(_scalars(item, 8))
        step["with"] = _scalars(_block(item, "with", 8), 10) if "with" in step else {}
        steps.append(step)
    return steps


def _workflow() -> list[str]:
    return WORKFLOW.read_text(encoding="utf-8").splitlines()


def _jobs() -> dict[str, list[str]]:
    jobs = _block(_workflow(), "jobs", 0)
    names = [line.strip()[:-1] for line in jobs if _indent(line) == 2 and line.endswith(":")]
    return {name: _block(jobs, name, 2) for name in names}


def test_deploy_job_runs_on_push_to_main_after_both_check_jobs() -> None:
    deploy = _jobs().get("deploy")
    assert deploy is not None, "ci.yml has no deploy job, so Pages publishes without CI"
    fields = _scalars(deploy, 4)
    assert {name.strip() for name in fields["needs"].strip("[]").split(",")} == CHECK_JOBS
    # Pull request runs skip the job; a failed or cancelled check job skips it too.
    assert fields["if"] == PUSH_TO_MAIN
    assert not any(function in fields["if"] for function in STATUS_FUNCTIONS)


def test_only_the_deploy_job_can_write_to_pages() -> None:
    jobs = _jobs()
    assert "deploy" in jobs, "ci.yml has no deploy job"
    assert _scalars(_block(_workflow(), "permissions", 0), 2) == {"contents": "read"}
    # Job permissions replace the workflow's, so the checkout keeps contents: read.
    assert _scalars(_block(jobs["deploy"], "permissions", 4), 6) == {
        "contents": "read",
        "pages": "write",
        "id-token": "write",
    }
    for name in CHECK_JOBS:
        assert "    permissions:" not in jobs[name], f"{name} must keep the read-only token"


def test_deploy_job_publishes_docs_to_the_github_pages_environment() -> None:
    deploy = _jobs().get("deploy")
    assert deploy is not None, "ci.yml has no deploy job"
    assert _scalars(_block(deploy, "environment", 4), 6)["name"] == "github-pages"
    steps = _steps(deploy)
    actions = [str(step["uses"]).split("@")[0] for step in steps if "uses" in step]
    assert actions == ["actions/checkout", "actions/upload-pages-artifact", "actions/deploy-pages"]
    upload = next(step for step in steps if "upload-pages-artifact" in str(step.get("uses")))
    assert upload["with"] == {"path": "docs"}


def test_every_action_is_pinned_to_a_commit_sha() -> None:
    uses = [
        line.split("uses:", 1)[1].split(" #")[0].strip()
        for line in _workflow()
        if line.strip().removeprefix("- ").startswith("uses:")
    ]
    assert uses
    assert [action for action in uses if not PINNED_ACTION.fullmatch(action)] == []


def test_deployment_doc_names_the_ci_deploy_job() -> None:
    text = DEPLOYMENT.read_text(encoding="utf-8")
    assert "the `deploy` job in `.github/workflows/ci.yml`" in text
    assert "after the `test` and `web` jobs pass" in text


def test_web_job_fails_on_high_npm_advisories_before_the_tests() -> None:
    web = _jobs()["web"]
    # The job's steps run in web/, so the audit reads web/package-lock.json.
    assert _scalars(_block(_block(web, "defaults", 4), "run", 6), 8) == {"working-directory": "web"}
    steps = _steps(web)
    runs = [step["run"] for step in steps if "run" in step]
    assert NPM_AUDIT in runs, "the web job installs npm packages without auditing them"
    # It audits the tree npm ci installed, before any of that code runs.
    assert runs.index("npm ci") < runs.index(NPM_AUDIT) < runs.index("npm test")
    audit = next(step for step in steps if step.get("run") == NPM_AUDIT)
    assert "continue-on-error" not in audit
    assert "working-directory" not in audit
