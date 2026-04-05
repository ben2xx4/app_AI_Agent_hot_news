from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

import feedparser
from bs4 import BeautifulSoup

from app.core.logging import get_logger
from app.pipelines.common.fetcher import fetch_url_text
from app.pipelines.common.processing import (
    build_cluster_key,
    is_datetime_within_age_window,
    normalize_whitespace,
    parse_datetime,
    stable_hash,
)
from app.pipelines.common.records import ArticleRecord, SourceDefinition

logger = get_logger(__name__)

DetailFetcher = Callable[[str, SourceDefinition], str]
NowProvider = Callable[[], datetime]


def _strip_html(value: str | None) -> str:
    if not value:
        return ""
    return normalize_whitespace(BeautifulSoup(value, "html.parser").get_text(" ", strip=True))


def _build_article_record(source: SourceDefinition, entry: dict) -> ArticleRecord | None:
    title = normalize_whitespace(entry.get("title"))
    if not title:
        return None

    summary = _strip_html(entry.get("summary") or entry.get("description"))
    content_value = None
    contents = entry.get("content", [])
    if contents:
        content_value = _strip_html(contents[0].get("value"))

    canonical_url = entry.get("link") or stable_hash(title, source.name)
    published_at = parse_datetime(
        entry.get("published") or entry.get("updated") or entry.get("pubDate")
    )
    return ArticleRecord(
        category=source.category_default,
        title=title,
        summary=summary,
        content_clean=content_value or summary,
        author=normalize_whitespace(entry.get("author")),
        published_at=published_at,
        canonical_url=canonical_url,
        article_hash=stable_hash(canonical_url, title, summary, source.name),
        duplicate_status="unique",
        cluster_key=build_cluster_key(title),
    )


def _default_detail_fetcher(url: str, source: SourceDefinition) -> str:
    timeout_seconds = int(source.extra.get("detail_timeout_seconds", source.timeout_seconds))
    retry_count = int(source.extra.get("detail_retry_count", source.retry_count))
    result = fetch_url_text(
        url,
        timeout_seconds=timeout_seconds,
        retry_count=retry_count,
        headers=source.headers,
        log_name=f"{source.name}:detail",
    )
    return result.text


def _is_article_within_age_window(
    article: ArticleRecord,
    source: SourceDefinition,
    *,
    now_provider: NowProvider,
) -> bool:
    return is_datetime_within_age_window(
        article.published_at,
        source.extra.get("max_age_days"),
        now_provider=now_provider,
    )


def _parse_tuoitre_detail(url: str, payload: str) -> dict[str, object]:
    soup = BeautifulSoup(payload, "html.parser")
    content_root = soup.select_one(".detail-content[data-role='content']") or soup.select_one(
        ".detail-content.afcbc-body"
    )
    paragraphs: list[str] = []
    if content_root is not None:
        for paragraph in content_root.select("p"):
            if paragraph.find_parent("figcaption") is not None:
                continue
            text = normalize_whitespace(paragraph.get_text(" ", strip=True))
            if text:
                paragraphs.append(text)

    summary = normalize_whitespace(
        (
            soup.select_one("meta[property='og:description']")
            or soup.select_one("meta[name='description']")
        ).get("content")
        if (
            soup.select_one("meta[property='og:description']")
            or soup.select_one("meta[name='description']")
        )
        else None
    )
    author_meta = soup.select_one("meta[property='dable:author']")
    author = normalize_whitespace(author_meta.get("content") if author_meta else None).replace(
        ";", ", "
    )
    published_meta = soup.select_one("meta[property='article:published_time']") or soup.select_one(
        "meta[name='pubdate']"
    )

    return {
        "summary": summary or None,
        "content_clean": "\n".join(paragraphs) if paragraphs else summary or None,
        "author": author or None,
        "published_at": parse_datetime(published_meta.get("content")) if published_meta else None,
        "canonical_url": url,
    }


def _parse_tuoitre_feed_with_details(
    source: SourceDefinition,
    payload: str,
    *,
    detail_fetcher: DetailFetcher,
    now_provider: NowProvider,
) -> list[ArticleRecord]:
    parsed = feedparser.parse(payload)
    articles: list[ArticleRecord] = []
    max_items = int(source.extra.get("max_items", 8))

    for entry in parsed.entries:
        if len(articles) >= max_items:
            break
        article = _build_article_record(source, entry)
        if article is None:
            continue
        if not _is_article_within_age_window(article, source, now_provider=now_provider):
            continue

        try:
            detail_payload = detail_fetcher(article.canonical_url, source)
            detail = _parse_tuoitre_detail(article.canonical_url, detail_payload)
            article.summary = normalize_whitespace(detail.get("summary")) or article.summary
            article.content_clean = (
                normalize_whitespace(detail.get("content_clean")) or article.content_clean
            )
            article.author = normalize_whitespace(detail.get("author")) or article.author
            article.published_at = detail.get("published_at") or article.published_at
        except Exception as exc:
            logger.warning("Khong enrich duoc bai viet %s: %s", article.canonical_url, exc)
        if not _is_article_within_age_window(article, source, now_provider=now_provider):
            continue

        articles.append(article)
    return articles


def parse_news_feed(
    source: SourceDefinition,
    payload: str,
    *,
    detail_fetcher: DetailFetcher | None = None,
    now_provider: NowProvider | None = None,
) -> list[ArticleRecord]:
    effective_now_provider = now_provider or (lambda: datetime.now(UTC))
    if source.parser == "tuoitre_rss_detail" and not source.extra.get("_used_demo"):
        return _parse_tuoitre_feed_with_details(
            source,
            payload,
            detail_fetcher=detail_fetcher or _default_detail_fetcher,
            now_provider=effective_now_provider,
        )

    parsed = feedparser.parse(payload)
    articles: list[ArticleRecord] = []
    max_items = int(source.extra.get("max_items", len(parsed.entries) or 50))

    for entry in parsed.entries:
        if len(articles) >= max_items:
            break
        article = _build_article_record(source, entry)
        if article is None:
            continue
        if not _is_article_within_age_window(
            article,
            source,
            now_provider=effective_now_provider,
        ):
            continue
        articles.append(article)
    return articles
