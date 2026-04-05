# Bản đồ chức năng giao diện web

## Mục tiêu tài liệu
File này mô tả giao diện web hiện tại theo góc nhìn chức năng:
- người dùng nhìn thấy gì
- mỗi khu dùng để làm gì
- thao tác chính nằm ở đâu
- dữ liệu nào là preview, dữ liệu nào là tra cứu sâu

Tài liệu này bám theo code UI hiện tại trong:
- `app/ui/streamlit_app.py`
- `app/ui/data_browser.py`
- `app/ui/chat_state.py`
- `app/ui/experience.py`
- `app/ui/navigation.py`
- `app/ui/source_health.py`

## Công nghệ giao diện
- UI dùng `Streamlit`
- dữ liệu lấy qua `FastAPI`
- backend chính cung cấp:
  - `/health`
  - `/news/hot`
  - `/prices/latest`
  - `/weather/latest`
  - `/policies/search`
  - `/traffic/latest`
  - `/chat/query`

## Cấu trúc điều hướng
Giao diện hiện tại có 4 khu chính trong sidebar:

1. `Tổng quan`
2. `Trợ lý AI`
3. `Explorer`
4. `Hệ thống`

Ngoài ra sidebar còn có:
- `Quick actions`
- chỉ báo runtime ngắn
- điểm vào nhanh để sang AI hoặc Explorer

## 1. Khu Tổng quan
Đây là màn hình người dùng nhìn thấy đầu tiên.

### Thành phần chính
- `Hero`
  - mô tả ngắn hệ thống
  - badge trạng thái:
    - `Database`
    - `Retrieval`
    - `Chat`
    - `API`
- `KPI`
  - số lượng bản ghi đang có
  - số pipeline
  - số nguồn dữ liệu
- `Bắt đầu nhanh`
  - mở câu hỏi mẫu cho AI
  - chuyển nhanh sang Explorer
- `Tin nổi bật hôm nay`
- `Giá nhanh`
- `Thời tiết nhanh`
- `Chính sách mới`
- `Giao thông cần chú ý`

### Mục đích
- giúp người mới hiểu hệ thống đang làm gì
- cho thấy giá trị của 5 pipeline
- dẫn người dùng sang AI hoặc Explorer mà không bị lạc

### Kiểu dữ liệu hiển thị
- là `preview`
- không phải toàn bộ dữ liệu trong database
- phù hợp để demo nhanh trên màn hình lớn

## 2. Khu Trợ lý AI
Đây là khu hội thoại chính.

### Thành phần chính
- phần giới thiệu ngắn về trợ lý
- chỉ báo trạng thái:
  - đang dùng OpenAI hay fallback nội bộ
  - retrieval đang bật hay tắt
  - database runtime
- lịch sử hội thoại
- ô nhập câu hỏi
- gợi ý câu hỏi theo nhóm
- câu hỏi gần đây
- follow-up suggestion
- nút `Xóa hội thoại`

### Người dùng có thể làm gì
- hỏi bằng tiếng Việt tự nhiên
- hỏi về:
  - tin hot
  - giá vàng, USD, xăng
  - thời tiết theo địa điểm
  - văn bản, chính sách
  - giao thông
  - tóm tắt theo chủ đề
- bấm câu hỏi gợi ý để bắt đầu nhanh

### Cơ chế hoạt động
- UI gọi `POST /chat/query`
- backend tự chọn OpenAI tool-calling hoặc fallback nội bộ
- nếu OpenAI không sẵn sàng, hệ thống vẫn trả lời bằng dữ liệu local

### Điểm nổi bật
- chat nổi góc phải vẫn còn để thao tác nhanh
- workspace `Trợ lý AI` là nơi hội thoại đầy đủ, rõ ràng hơn popover nhỏ

## 3. Khu Explorer
Explorer là nơi tra cứu dữ liệu chi tiết hơn.

### Cấu trúc
Explorer có 2 tab:
- `Dữ liệu nghiệp vụ`
- `Bảng kỹ thuật`

### Dữ liệu nghiệp vụ
Phù hợp với người xem demo hoặc người muốn tra cứu nhanh.

Có thể xem:
- `Tin tức`
- `Giá cả`
- `Thời tiết`
- `Chính sách`
- `Giao thông`

### Bảng kỹ thuật
Phù hợp với người vận hành hoặc muốn soi hệ thống.

Có thể xem:
- `sources`
- `crawl_jobs`
- `raw_documents`
- `document_embeddings`

### Chức năng chính
- chọn dataset
- tìm kiếm
- lọc theo:
  - `pipeline`
  - `source`
  - `location`
  - `item_name`
- sắp xếp:
  - `Mới nhất trước`
  - `Cũ nhất trước`
- chọn số dòng preview
- export CSV preview

### Mục đích
- giúp người dùng xem dữ liệu mà không cần SQL
- vẫn giữ đủ chi tiết để demo kỹ thuật

## 4. Khu Hệ thống
Đây là khu dành cho theo dõi runtime và vận hành.

### Thành phần chính
- `Tình trạng hệ thống`
  - API
  - Database runtime
  - Chat runtime
  - Retrieval
- `Sức khỏe nguồn dữ liệu`
  - source ổn
  - source lỗi
  - source đến lịch
  - source stale
- `Quy mô dữ liệu hiện có`
- `Runbook nhanh`

### Mục đích
- tách phần vận hành khỏi dashboard tổng quan
- giúp người kỹ thuật xem hệ thống có đang chạy tốt không

## Quick actions
Quick actions nằm ở sidebar.

### Tác dụng
- nhập nhanh một truy vấn
- chọn:
  - `Tìm trong Explorer`
  - `Hỏi AI`

### Mục đích
- giảm số bước thao tác
- giúp demo nhanh hơn

## Chat nổi góc phải
Ngoài workspace `Trợ lý AI`, UI vẫn có avatar chat nổi ở góc phải.

### Đặc điểm
- avatar tròn
- có bubble gợi ý
- mở popover chat nhanh
- dùng chung lịch sử với workspace AI

### Mục đích
- cho phép hỏi nhanh từ bất kỳ khu nào
- giữ cảm giác có trợ lý luôn sẵn sàng

## Phân biệt preview và tra cứu sâu
- `Tổng quan`:
  - dùng để xem nhanh
  - dữ liệu là preview có chọn lọc
- `Trợ lý AI`:
  - dùng để hỏi đáp tự nhiên
  - câu trả lời dựa trên dữ liệu đã crawl trong hệ thống
- `Explorer`:
  - dùng để tra cứu sâu hơn
  - có filter, sort, export
- `Hệ thống`:
  - dùng để theo dõi vận hành

## Trạng thái dữ liệu hiển thị
Giao diện có thể làm việc với 2 trạng thái dữ liệu:
- `demo`
- `live`

Tùy theo database hiện tại và các pipeline đã chạy hay chưa, payload có thể là:
- hoàn toàn live
- hoàn toàn demo
- hoặc mixed

UI hiện có chỉ báo để người xem hiểu trạng thái này khi demo.

## Những tình huống giao diện đã hỗ trợ
- dữ liệu ít:
  - có empty state hoặc gợi ý chạy refresh
- OpenAI không sẵn sàng:
  - chat vẫn dùng fallback nội bộ
- scheduler không có snapshot:
  - khu hệ thống vẫn render, không bị crash
- người dùng không biết hỏi gì:
  - có câu hỏi gợi ý và câu hỏi gần đây

## Giới hạn hiện tại
- vẫn là Streamlit, nên chưa thể đạt trải nghiệm SPA hoàn chỉnh như React app
- một số tương tác chat nổi phụ thuộc CSS/DOM của Streamlit
- Explorer hiện mạnh ở preview/filter, chưa phải công cụ quản trị dữ liệu chuyên sâu
- chưa có global search backend riêng cho toàn hệ thống

## Cách mở giao diện
```bash
.venv/bin/uvicorn app.main:app --reload
.venv/bin/streamlit run app/ui/streamlit_app.py
```

Hoặc bằng Docker:
```bash
docker compose up -d postgres api ui scheduler
```

## Tóm tắt ngắn
Giao diện hiện tại phục vụ 3 nhu cầu chính:
- xem nhanh tình hình dữ liệu trong ngày
- hỏi đáp bằng AI
- tra cứu dữ liệu chi tiết và theo dõi hệ thống
