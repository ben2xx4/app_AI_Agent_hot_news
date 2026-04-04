# Pipeline 1 - Tin tức

## Phạm vi
- tin nóng
- xã hội
- giải trí
- sức khỏe
- giáo dục
- tài chính dạng bài viết

## Nguồn ưu tiên
- RSS báo điện tử
- sau đó mới crawl chi tiết bài báo

## Các bước
1. Fetch RSS
2. Parse item RSS
3. Chuẩn hóa: title, summary, published_at, canonical_url, source_name, category
4. Kiểm tra đã tồn tại chưa theo canonical_url hoặc article_hash
5. Nếu cần, crawl nội dung chi tiết
6. Clean text
7. Dedup exact và near duplicate
8. Cluster các bài cùng sự kiện
9. Lưu PostgreSQL
10. Tạo embedding cho summary hoặc content_clean

## Bảng liên quan
- sources
- raw_documents
- articles
- article_clusters
- document_embeddings

## Tần suất chạy
- 5 đến 15 phút một lần
