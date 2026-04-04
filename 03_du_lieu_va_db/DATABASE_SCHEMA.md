# Thiết kế cơ sở dữ liệu sơ bộ

## Bảng `sources`
- id
- source_name
- source_type
- category_default
- base_url
- trust_level
- is_active
- created_at
- updated_at

## Bảng `crawl_jobs`
- id
- pipeline_name
- source_id
- status
- started_at
- finished_at
- total_fetched
- total_success
- total_failed
- error_message

## Bảng `raw_documents`
- id
- source_id
- pipeline_name
- fetch_url
- content_type
- raw_path_or_text
- raw_hash
- fetched_at

## Bảng `articles`
- id
- source_id
- category
- title
- summary
- content_clean
- published_at
- canonical_url
- article_hash
- duplicate_status
- cluster_id
- created_at

## Bảng `article_clusters`
- id
- cluster_key
- representative_title
- first_seen_at
- last_seen_at

## Bảng `price_snapshots`
- id
- source_id
- item_type
- item_name
- region
- buy_price
- sell_price
- unit
- effective_at
- created_at

## Bảng `weather_snapshots`
- id
- source_id
- location
- forecast_time
- min_temp
- max_temp
- humidity
- wind
- weather_text
- warning_text
- created_at

## Bảng `policy_documents`
- id
- source_id
- issuing_agency
- doc_number
- title
- summary
- content_clean
- field
- issued_at
- effective_at
- canonical_url
- created_at

## Bảng `traffic_events`
- id
- source_id
- event_type
- title
- location
- start_time
- end_time
- description
- created_at

## Bảng `document_embeddings`
- id
- doc_type
- doc_id
- chunk_index
- chunk_text
- embedding_vector
- created_at
