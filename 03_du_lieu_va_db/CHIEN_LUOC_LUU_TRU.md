# Chiến lược lưu trữ dữ liệu

## 3 lớp lưu trữ

### 1. Raw Storage
Mục đích:
- giữ dữ liệu gốc
- debug parser
- reprocess

Dạng dữ liệu:
- HTML
- XML RSS
- JSON API

### 2. Structured Storage
Dùng PostgreSQL để lưu dữ liệu đã chuẩn hóa.

### 3. Retrieval Storage
Dùng pgvector hoặc vector DB để lưu embedding.

## Tại sao phải tách 3 lớp
- raw giúp không mất dữ liệu gốc
- structured giúp query chuẩn
- retrieval giúp AI hỏi đáp ngữ nghĩa
