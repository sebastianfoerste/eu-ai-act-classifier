from eu_ai_act_classifier.portfolio_workspace import build_example_portfolio_workspace


def test_workspace_builds_system_vault_with_source_and_artifact_refs() -> None:
    workspace = build_example_portfolio_workspace()
    assert workspace.vault.schema_id == "eu-ai-act-classifier.system-vault.v1"
    assert workspace.vault.records
    assert all(record.source_refs for record in workspace.vault.records)
    assert all(record.artifact_refs for record in workspace.vault.records)
    assert workspace.vault.external_action_allowed is False


def test_workspace_builds_guided_assessment_workflows() -> None:
    workspace = build_example_portfolio_workspace()
    assert len(workspace.workflows) == len(workspace.vault.records)
    assert all(len(workflow.steps) == 6 for workflow in workspace.workflows)
    assert all(workflow.reviewer_sign_off_required for workflow in workspace.workflows)
    assert all(workflow.deployment_allowed is False for workflow in workspace.workflows)


def test_command_center_prioritizes_blocked_and_high_risk_systems() -> None:
    workspace = build_example_portfolio_workspace()
    rows = workspace.command_center.rows
    rank = {"critical": 0, "high": 1, "standard": 2}
    assert [rank[row.priority] for row in rows] == sorted(rank[row.priority] for row in rows)
    assert workspace.command_center.summary["systems"] == len(rows)
    assert workspace.command_center.external_action_allowed is False
    assert workspace.draft_only is True
