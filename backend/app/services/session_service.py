"""What sign-out clears besides the cookie: the user's lists and access token in server memory."""

from app.services import memory_store, youtube_gateway


def forget_user(user_id: int) -> None:
    memory_store.forget_user(user_id)
    youtube_gateway.forget_user(user_id)
