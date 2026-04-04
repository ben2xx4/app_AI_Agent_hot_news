# Chiến lược dedup

## 1. Exact duplicate
Áp dụng cho mọi pipeline nếu có thể.
Ví dụ:
- hash(canonical_url)
- hash(title_normalized + source_name)
- hash(raw_content)

## 2. Near duplicate cho tin tức
Áp dụng:
- similarity tiêu đề
- thời gian đăng gần nhau
- cùng chủ đề hoặc cùng cụm từ khóa

## 3. Không dedup quá mạnh cho chính sách
Vì nhiều văn bản có thể gần giống nhau nhưng là văn bản khác.

## 4. Giá cả và thời tiết không dedup như bài báo
Các bản ghi cùng item nhưng khác thời gian là snapshot hợp lệ.
