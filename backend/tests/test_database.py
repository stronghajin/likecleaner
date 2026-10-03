"""Tables from the migration, and the delete rules from SPEC.md 9/10."""

from datetime import date

from sqlalchemy import delete, select, text

from app.core.db import SessionFactory
from app.models import Job, JobItem, OAuthToken, QuotaUsage, User


async def test_migration_creates_all_tables(started_app):
    async with SessionFactory() as session:
        rows = await session.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = {r[0] for r in rows}
    assert {"users", "oauth_tokens", "quota_usage", "jobs", "job_items"} <= tables


async def test_deleting_a_user_removes_their_data_but_keeps_quota_usage(started_app):
    async with SessionFactory() as session:
        user = User(google_sub="sub-delete-test", email="a@example.com", name="A")
        session.add(user)
        await session.flush()
        session.add(OAuthToken(user_id=user.id, refresh_token="encrypted", scopes="openid"))
        session.add(QuotaUsage(date_pt=date(2026, 10, 3), method="videos.rate", units=50, user_id=user.id, success=True))
        job = Job(id="job-delete-test", user_id=user.id, type="remove_like")
        job.items = [JobItem(position=0, video_id="v1", video_title="Video 1")]
        session.add(job)
        await session.commit()

        await session.execute(delete(User).where(User.id == user.id))
        await session.commit()

        assert await session.scalar(select(OAuthToken).where(OAuthToken.user_id == user.id)) is None
        assert await session.scalar(select(Job).where(Job.id == "job-delete-test")) is None
        assert await session.scalar(select(JobItem).where(JobItem.job_id == "job-delete-test")) is None
        # The quota is shared by everyone, so the usage stays counted (user_id becomes empty).
        usage = await session.scalar(select(QuotaUsage).where(QuotaUsage.method == "videos.rate"))
        assert usage is not None and usage.user_id is None


async def test_status_values_are_checked(started_app):
    async with SessionFactory() as session:
        session.add(User(google_sub="sub-bad-status", email="b@example.com", name="B", status="banned"))
        try:
            await session.commit()
        except Exception:  # noqa: BLE001
            await session.rollback()
        else:
            raise AssertionError("an unknown status must be rejected")


async def test_datetimes_come_back_timezone_aware(started_app):
    async with SessionFactory() as session:
        user = User(google_sub="sub-tz", email="c@example.com", name="C")
        session.add(user)
        await session.commit()
        session.expire_all()
        loaded = await session.scalar(select(User).where(User.google_sub == "sub-tz"))
        assert loaded.created_at.tzinfo is not None
