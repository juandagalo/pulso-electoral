"""Reddit collection utilities using PRAW."""

from __future__ import annotations

import os

import praw


def get_reddit_client() -> praw.Reddit:
    """Create a Reddit API client from environment variables.

    Returns
    -------
    praw.Reddit
        Authenticated Reddit client.

    Raises
    ------
    ValueError
        If required environment variables are not set.
    """
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT", "pulso-electoral:v0.1")

    if not client_id or not client_secret:
        msg = "REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET must be set in .env"
        raise ValueError(msg)

    return praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
    )


def collect_reddit_posts(
    subreddit: str,
    keywords: list[str] | None = None,
    sort: str = "hot",
    limit: int = 100,
) -> list[dict]:
    """Collect posts from a subreddit, optionally filtering by keywords.

    Parameters
    ----------
    subreddit : str
        Subreddit name (e.g., 'Colombia').
    keywords : list[str] | None
        Keywords to search for. If None, collects top posts by sort mode.
    sort : str
        Sort mode: 'hot', 'new', 'top'. Defaults to 'hot'.
    limit : int
        Maximum number of posts to collect. Defaults to 100.

    Returns
    -------
    list[dict]
        List of post dicts with Reddit-specific fields.
    """
    reddit = get_reddit_client()
    sub = reddit.subreddit(subreddit)
    posts = []

    if keywords:
        query = " OR ".join(keywords)
        submissions = sub.search(query, sort=sort, limit=limit)
    elif sort == "hot":
        submissions = sub.hot(limit=limit)
    elif sort == "new":
        submissions = sub.new(limit=limit)
    else:
        submissions = sub.top(limit=limit, time_filter="week")

    for submission in submissions:
        posts.append({
            "title": submission.title,
            "selftext": submission.selftext,
            "url": f"https://reddit.com{submission.permalink}",
            "published": submission.created_utc,
            "author": str(submission.author) if submission.author else "deleted",
            "score": submission.score,
            "num_comments": submission.num_comments,
            "flair": submission.link_flair_text,
            "source": f"r/{subreddit}",
        })

    return posts
