from datetime import UTC, date, datetime

from app.core.time import format_kst, next_quota_reset, pacific_day


def test_quota_day_follows_us_pacific_time():
    # 2026-10-03 06:00 UTC is still Oct 2 in California (UTC-7).
    assert pacific_day(datetime(2026, 10, 3, 6, 0, tzinfo=UTC)) == date(2026, 10, 2)
    assert pacific_day(datetime(2026, 10, 3, 8, 0, tzinfo=UTC)) == date(2026, 10, 3)


def test_reset_is_next_pacific_midnight_in_summer_time():
    # PDT (UTC-7): midnight = 07:00 UTC = 16:00 KST
    assert next_quota_reset(datetime(2026, 10, 3, 6, 0, tzinfo=UTC)) == datetime(2026, 10, 3, 7, 0, tzinfo=UTC)


def test_reset_is_next_pacific_midnight_in_winter_time():
    # PST (UTC-8): midnight = 08:00 UTC = 17:00 KST
    assert next_quota_reset(datetime(2026, 12, 1, 12, 0, tzinfo=UTC)) == datetime(2026, 12, 2, 8, 0, tzinfo=UTC)


def test_reset_across_the_daylight_saving_switch():
    # 2026-03-08 is when California moves to summer time; the next midnight is already PDT.
    assert next_quota_reset(datetime(2026, 3, 8, 12, 0, tzinfo=UTC)) == datetime(2026, 3, 9, 7, 0, tzinfo=UTC)


def test_admin_mail_time_is_shown_in_kst():
    assert format_kst(datetime(2026, 10, 3, 5, 5, tzinfo=UTC)) == "2026-10-03 14:05 KST"
