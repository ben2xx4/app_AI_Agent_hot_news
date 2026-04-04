CREATE TABLE IF NOT EXISTS sources (
    id BIGSERIAL PRIMARY KEY,
    source_name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    category_default TEXT,
    base_url TEXT,
    trust_level INT DEFAULT 3,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS crawl_jobs (
    id BIGSERIAL PRIMARY KEY,
    pipeline_name TEXT NOT NULL,
    source_id BIGINT REFERENCES sources(id),
    status TEXT NOT NULL,
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    total_fetched INT DEFAULT 0,
    total_success INT DEFAULT 0,
    total_failed INT DEFAULT 0,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS raw_documents (
    id BIGSERIAL PRIMARY KEY,
    source_id BIGINT REFERENCES sources(id),
    pipeline_name TEXT NOT NULL,
    fetch_url TEXT,
    content_type TEXT,
    raw_path_or_text TEXT,
    raw_hash TEXT,
    fetched_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS article_clusters (
    id BIGSERIAL PRIMARY KEY,
    cluster_key TEXT,
    representative_title TEXT,
    first_seen_at TIMESTAMP,
    last_seen_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS articles (
    id BIGSERIAL PRIMARY KEY,
    source_id BIGINT REFERENCES sources(id),
    category TEXT,
    title TEXT NOT NULL,
    summary TEXT,
    content_clean TEXT,
    published_at TIMESTAMP,
    canonical_url TEXT UNIQUE,
    article_hash TEXT,
    duplicate_status TEXT DEFAULT 'unique',
    cluster_id BIGINT REFERENCES article_clusters(id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS price_snapshots (
    id BIGSERIAL PRIMARY KEY,
    source_id BIGINT REFERENCES sources(id),
    item_type TEXT NOT NULL,
    item_name TEXT NOT NULL,
    region TEXT,
    buy_price NUMERIC(18,2),
    sell_price NUMERIC(18,2),
    unit TEXT,
    effective_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS weather_snapshots (
    id BIGSERIAL PRIMARY KEY,
    source_id BIGINT REFERENCES sources(id),
    location TEXT NOT NULL,
    forecast_time TIMESTAMP,
    min_temp NUMERIC(5,2),
    max_temp NUMERIC(5,2),
    humidity NUMERIC(5,2),
    wind TEXT,
    weather_text TEXT,
    warning_text TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS policy_documents (
    id BIGSERIAL PRIMARY KEY,
    source_id BIGINT REFERENCES sources(id),
    issuing_agency TEXT,
    doc_number TEXT,
    title TEXT NOT NULL,
    summary TEXT,
    content_clean TEXT,
    field TEXT,
    issued_at TIMESTAMP,
    effective_at TIMESTAMP,
    canonical_url TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS traffic_events (
    id BIGSERIAL PRIMARY KEY,
    source_id BIGINT REFERENCES sources(id),
    event_type TEXT,
    title TEXT NOT NULL,
    location TEXT,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
