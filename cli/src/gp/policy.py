from __future__ import annotations

import re

BRANCH_TYPES = ("feat", "fix", "chore", "refactor", "test", "docs")
_TYPES_PATTERN = "|".join(BRANCH_TYPES)


class DeliveryPolicy:
    """Enforces branch naming and commit message rules for a given Work ID prefix.

    Acts as the policy gate between a developer's local changes and the remote
    repository — if the branch or commit doesn't comply, the push is blocked.
    """

    def __init__(self, work_id_prefix: str) -> None:
        self.prefix = work_id_prefix
        p = re.escape(work_id_prefix)
        self._work_id_re = re.compile(rf"^{p}-\d+$")
        self._branch_re = re.compile(
            rf"^({_TYPES_PATTERN})/{p}-\d+-[a-z0-9][a-z0-9-]*$"
        )
        self._commit_re = re.compile(
            rf"^({_TYPES_PATTERN})(\(.+\))?: {p}-\d+ .{{3,}}$"
        )

    def valid_work_id(self, work_id: str) -> bool:
        return bool(self._work_id_re.match(work_id))

    def validate_branch(self, name: str) -> list[str]:
        if self._branch_re.match(name):
            return []
        return [
            f"Branch '{name}' does not follow the convention.\n"
            f"  Expected : <type>/{self.prefix}-<N>-<slug>\n"
            f"  Example  : feat/{self.prefix}-42-add-payments\n"
            f"  Types    : {', '.join(BRANCH_TYPES)}"
        ]

    def validate_commit(self, message: str) -> list[str]:
        first_line = message.split("\n")[0].strip()
        if self._commit_re.match(first_line):
            return []
        return [
            f"Commit message does not follow the convention.\n"
            f"  Expected : <type>: {self.prefix}-<N> <description>\n"
            f"  Example  : feat: {self.prefix}-42 Add payment endpoint\n"
            f"  Got      : '{first_line}'"
        ]

    def extract_work_id(self, branch: str) -> str | None:
        m = re.search(rf"{re.escape(self.prefix)}-\d+", branch)
        return m.group(0) if m else None
