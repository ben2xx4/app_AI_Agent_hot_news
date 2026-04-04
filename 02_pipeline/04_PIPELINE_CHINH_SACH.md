# Pipeline 4 - Chính sách

## Phạm vi
- chính sách mới
- văn bản
- thông báo của cơ quan nhà nước
- các chủ đề như giáo dục, y tế, đời sống, kinh tế

## Các bước
1. Fetch danh sách văn bản / tin thông báo
2. Parse metadata: title, doc_number, issuing_agency, issued_at, effective_at, field, url
3. Crawl nội dung đầy đủ nếu cần
4. Clean text
5. Lưu policy_documents
6. Tạo embedding để semantic search

## Bảng liên quan
- policy_documents
- raw_documents
- sources
- document_embeddings

## Tần suất chạy
- 1 đến 2 giờ
