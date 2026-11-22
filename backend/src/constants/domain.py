from enum import StrEnum


class Role(StrEnum):
    REVIEWER = 'reviewer'
    ANALYST = 'analyst'
    OBSERVER = 'observer'


class ReceiptKind(StrEnum):
    LOAN = 'loan'
    REVERSAL = 'reversal'


class RunStatus(StrEnum):
    QUEUED = 'queued'
    DONE = 'done'
    FAILED = 'failed'


class SyncStatus(StrEnum):
    POSTED = 'posted'
    PENDING_ORIGINAL = 'pending_original'
    CONFLICT = 'conflict'
