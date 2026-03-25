import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.models.enums import StepName, StepStatus
from app.services.step_runner import run_step


def _make_step(
    status: StepStatus = StepStatus.PENDING,
    attempts: int = 0,
    max_attempts: int = 3,
) -> MagicMock:
    step = MagicMock()
    step.status = status
    step.attempts = attempts
    step.max_attempts = max_attempts
    step.error_message = None
    step.started_at = None
    step.completed_at = None
    return step


def _make_db(step: MagicMock) -> MagicMock:
    """Return a mock db whose query chain resolves to *step*."""
    db = MagicMock()
    db.query.return_value.filter.return_value.one.return_value = step
    return db


JOB_ID = uuid.uuid4()
STEP_NAME = StepName.NORMALIZATION


class TestRunStepIdempotency:
    def test_skips_already_completed_step(self):
        step = _make_step(status=StepStatus.COMPLETED)
        db = _make_db(step)

        result = run_step(db, JOB_ID, STEP_NAME, execute_fn=MagicMock())

        assert result == StepStatus.COMPLETED
        db.commit.assert_not_called()

    def test_does_not_call_execute_fn_when_completed(self):
        step = _make_step(status=StepStatus.COMPLETED)
        db = _make_db(step)
        fn = MagicMock()

        run_step(db, JOB_ID, STEP_NAME, execute_fn=fn)

        fn.assert_not_called()


class TestRunStepMaxAttempts:
    def test_exhausted_attempts_returns_failed(self):
        step = _make_step(attempts=3, max_attempts=3)
        db = _make_db(step)

        result = run_step(db, JOB_ID, STEP_NAME, execute_fn=MagicMock())

        assert result == StepStatus.FAILED
        assert step.status == StepStatus.FAILED
        db.commit.assert_called_once()

    def test_does_not_call_execute_fn_when_exhausted(self):
        step = _make_step(attempts=3, max_attempts=3)
        db = _make_db(step)
        fn = MagicMock()

        run_step(db, JOB_ID, STEP_NAME, execute_fn=fn)

        fn.assert_not_called()


class TestRunStepSuccess:
    def test_returns_completed_on_success(self):
        step = _make_step()
        db = _make_db(step)

        result = run_step(db, JOB_ID, STEP_NAME, execute_fn=lambda: None)

        assert result == StepStatus.COMPLETED

    def test_sets_status_to_completed(self):
        step = _make_step()
        db = _make_db(step)

        run_step(db, JOB_ID, STEP_NAME, execute_fn=lambda: None)

        assert step.status == StepStatus.COMPLETED

    def test_increments_attempts(self):
        step = _make_step(attempts=1)
        db = _make_db(step)

        run_step(db, JOB_ID, STEP_NAME, execute_fn=lambda: None)

        assert step.attempts == 2

    def test_sets_started_at_and_completed_at(self):
        step = _make_step()
        db = _make_db(step)

        run_step(db, JOB_ID, STEP_NAME, execute_fn=lambda: None)

        assert step.started_at is not None
        assert step.completed_at is not None

    def test_clears_error_message_on_new_attempt(self):
        step = _make_step()
        step.error_message = "previous failure"
        db = _make_db(step)

        run_step(db, JOB_ID, STEP_NAME, execute_fn=lambda: None)

        assert step.error_message is None

    def test_commits_twice(self):
        """One commit for PROCESSING transition, one for COMPLETED."""
        step = _make_step()
        db = _make_db(step)

        run_step(db, JOB_ID, STEP_NAME, execute_fn=lambda: None)

        assert db.commit.call_count == 2


class TestRunStepFailure:
    def test_returns_failed_on_exception(self):
        step = _make_step()
        db = _make_db(step)

        result = run_step(db, JOB_ID, STEP_NAME, execute_fn=lambda: (_ for _ in ()).throw(RuntimeError("boom")))

        assert result == StepStatus.FAILED

    def test_writes_error_message(self):
        step = _make_step()
        db = _make_db(step)

        run_step(db, JOB_ID, STEP_NAME, execute_fn=lambda: (_ for _ in ()).throw(RuntimeError("boom")))

        assert step.error_message == "boom"

    def test_sets_status_to_failed(self):
        step = _make_step()
        db = _make_db(step)

        run_step(db, JOB_ID, STEP_NAME, execute_fn=lambda: (_ for _ in ()).throw(ValueError("bad input")))

        assert step.status == StepStatus.FAILED

    def test_sets_completed_at_on_failure(self):
        step = _make_step()
        db = _make_db(step)

        run_step(db, JOB_ID, STEP_NAME, execute_fn=lambda: (_ for _ in ()).throw(RuntimeError()))

        assert step.completed_at is not None
