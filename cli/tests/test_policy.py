import pytest

from gp.policy import BRANCH_TYPES, DeliveryPolicy


@pytest.fixture
def policy() -> DeliveryPolicy:
    return DeliveryPolicy("FIN")


class TestBranchValidation:
    def test_valid_feat_branch(self, policy: DeliveryPolicy) -> None:
        assert policy.validate_branch("feat/FIN-42-add-payment-endpoint") == []

    def test_valid_fix_branch(self, policy: DeliveryPolicy) -> None:
        assert policy.validate_branch("fix/FIN-7-correct-balance-rounding") == []

    def test_all_valid_types(self, policy: DeliveryPolicy) -> None:
        for t in BRANCH_TYPES:
            assert policy.validate_branch(f"{t}/FIN-1-some-slug") == []

    def test_missing_work_id(self, policy: DeliveryPolicy) -> None:
        errors = policy.validate_branch("feat/add-payment")
        assert len(errors) == 1
        assert "FIN" in errors[0]

    def test_wrong_prefix(self, policy: DeliveryPolicy) -> None:
        errors = policy.validate_branch("feat/ABC-42-add-payment")
        assert len(errors) == 1

    def test_uppercase_slug_rejected(self, policy: DeliveryPolicy) -> None:
        errors = policy.validate_branch("feat/FIN-42-AddPayment")
        assert len(errors) == 1

    def test_no_slug(self, policy: DeliveryPolicy) -> None:
        errors = policy.validate_branch("feat/FIN-42")
        assert len(errors) == 1

    def test_invalid_type(self, policy: DeliveryPolicy) -> None:
        errors = policy.validate_branch("hotfix/FIN-42-fix-thing")
        assert len(errors) == 1


class TestCommitValidation:
    def test_valid_commit(self, policy: DeliveryPolicy) -> None:
        assert policy.validate_commit("feat: FIN-42 Add payment endpoint") == []

    def test_valid_commit_with_scope(self, policy: DeliveryPolicy) -> None:
        assert policy.validate_commit("fix(api): FIN-7 Correct balance rounding") == []

    def test_multiline_commit_checks_only_first_line(self, policy: DeliveryPolicy) -> None:
        msg = "feat: FIN-42 Add payment endpoint\n\nDetailed body here."
        assert policy.validate_commit(msg) == []

    def test_missing_work_id(self, policy: DeliveryPolicy) -> None:
        errors = policy.validate_commit("feat: Add payment endpoint")
        assert len(errors) == 1

    def test_description_too_short(self, policy: DeliveryPolicy) -> None:
        errors = policy.validate_commit("feat: FIN-42 Hi")
        assert len(errors) == 1

    def test_wrong_type(self, policy: DeliveryPolicy) -> None:
        errors = policy.validate_commit("hotfix: FIN-42 Fix something important")
        assert len(errors) == 1


class TestWorkIdExtraction:
    def test_extracts_from_valid_branch(self, policy: DeliveryPolicy) -> None:
        assert policy.extract_work_id("feat/FIN-42-add-thing") == "FIN-42"

    def test_returns_none_for_no_match(self, policy: DeliveryPolicy) -> None:
        assert policy.extract_work_id("feat/add-thing") is None

    def test_valid_work_id(self, policy: DeliveryPolicy) -> None:
        assert policy.valid_work_id("FIN-42") is True
        assert policy.valid_work_id("FIN-0") is True

    def test_invalid_work_id(self, policy: DeliveryPolicy) -> None:
        assert policy.valid_work_id("ABC-42") is False
        assert policy.valid_work_id("FIN-") is False
        assert policy.valid_work_id("42") is False
