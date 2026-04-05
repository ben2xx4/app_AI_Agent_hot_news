# Giao diện UI hiện tại

## Mục tiêu của UI
UI hiện tại được tổ chức lại theo hướng:
- rõ luồng sử dụng hơn
- dễ demo với giảng viên hoặc hội đồng
- vẫn đủ công cụ cho người vận hành dữ liệu
- thân thiện hơn với người dùng mới

UI vẫn dùng `Streamlit` và đọc dữ liệu từ FastAPI + database hiện có, không bịa thêm backend mới.

## Cấu trúc mới
Thay vì dồn mọi thứ vào một màn hình dài, UI hiện tại chia thành 4 workspace ở sidebar:

1. `Tổng quan`
2. `Trợ lý AI`
3. `Explorer`
4. `Hệ thống`

## 1. Workspace Tổng quan
Đây là khu dành cho người xem lần đầu.

Bao gồm:
- `Hero` với mô tả ngắn hệ thống
- chip trạng thái nhanh cho `Database`, `Retrieval`, `Chat`, `API`
- số lượng bản ghi thật từ database
- khối `Bắt đầu nhanh`
- preview dữ liệu theo nhóm:
  - `Tin tức & điều phối`
  - `Giá & thời tiết`
  - `Chính sách & giao thông`

Mục tiêu:
- nhìn vào là hiểu hệ thống đang làm gì
- thấy ngay 5 pipeline có giá trị gì
- có CTA rõ để chuyển sang AI hoặc Explorer

## 2. Workspace Trợ lý AI
Đây là khu hội thoại chính, không còn chỉ phụ thuộc vào popover nhỏ.

Bao gồm:
- phần mở đầu giải thích AI dùng dữ liệu local
- badge trạng thái:
  - `Chat`
  - `Retrieval`
  - `Database`
- lịch sử hội thoại rõ ràng
- gợi ý câu hỏi theo nhóm
- câu hỏi gần đây
- follow-up suggestion sau câu trả lời mới nhất
- item trả lời có `Thao tác ▼` để mở các action thật:
  - `Xem chi tiết`
  - `Tóm tắt lại`
  - `Mở nguồn` nếu có URL
- nút `Xóa hội thoại`
- nút chuyển nhanh sang `Explorer`

Lưu ý:
- avatar chat nổi ở góc phải vẫn còn để thao tác nhanh
- lịch sử giữa popover và workspace AI là dùng chung

## 3. Workspace Explorer
Explorer thay cho cách nghĩ `Data Browser` kiểu cũ.

Bao gồm 2 tab:
- `Dữ liệu nghiệp vụ`
- `Bảng kỹ thuật`

Khả năng hiện có:
- chọn dataset
- tìm kiếm từ khóa
- lọc theo:
  - `pipeline`
  - `source`
  - `location`
  - `item_name`
- sắp xếp:
  - `Mới nhất trước`
  - `Cũ nhất trước`
- chỉnh số dòng preview
- xuất `CSV preview`
- chọn một bản ghi trong preview để xem kỹ hơn
- từ bản ghi đang chọn có thể:
  - mở detail nội bộ
  - hỏi AI
  - mở link nguồn nếu có

Mục tiêu:
- đủ thân thiện để dùng khi demo
- vẫn đủ thông tin cho người vận hành mà không cần SQL

## 4. Workspace Hệ thống
Khu này tách phần vận hành khỏi dashboard chính.

Bao gồm:
- `Tình trạng hệ thống`
  - `API`
  - `Database runtime`
  - `Chat runtime`
  - `Retrieval`
- `Sức khỏe nguồn dữ liệu`
  - source ổn định
  - source đến lịch
  - source chưa có snapshot
  - source đang lỗi
- `Quy mô dữ liệu hiện có`
- `Runbook nhanh`

Mục tiêu:
- giữ dashboard gọn hơn
- giúp người kỹ thuật có chỗ kiểm tra runtime và scheduler riêng

## Các cải thiện UX chính
- Điều hướng rõ ràng bằng sidebar thay vì dồn một màn hình dài
- Có `Quick actions` ở sidebar để:
  - tìm nhanh trong Explorer
  - đẩy nhanh câu hỏi sang AI
- Có detail panel nội bộ dùng chung cho `Tổng quan`, `Trợ lý AI`, `Explorer`
- Có luồng liền mạch `preview -> detail -> AI -> Explorer -> nguồn gốc`
- Các card/item hiện dùng `Thao tác ▼` để giảm rối giao diện nhưng vẫn giữ đủ hành động thật
- Có chỉ báo `Demo/Live/Mixed` dựa trên payload preview
- Có CTA từ dashboard sang AI hoặc Explorer
- Có empty state rõ hơn khi dữ liệu đang mỏng
- Chat có cảm giác hội thoại hoàn chỉnh hơn, không còn chỉ là popover nhỏ

## Thành phần được giữ lại
- Hero
- trạng thái hệ thống
- source health
- preview dữ liệu các pipeline
- avatar chat nổi
- Data Browser logic nền

## Thành phần đã refactor
- `Data Browser` được đặt lại vai trò thành `Explorer`
- phần AI có workspace riêng
- phần vận hành được tách sang workspace `Hệ thống`
- `Bắt đầu nhanh` và CTA được tổ chức lại theo user flow

## File chính liên quan
- `app/ui/streamlit_app.py`
- `app/ui/data_browser.py`
- `app/ui/chat_state.py`
- `app/ui/experience.py`
- `app/ui/navigation.py`
- `app/ui/source_health.py`

## Giới hạn hiện tại
- Vẫn là `Streamlit`, nên một số tương tác nâng cao của web app thật còn hạn chế
- Avatar chat nổi vẫn phụ thuộc vào CSS theo DOM hiện tại của Streamlit
- Explorer hiện là preview/filter tốt, chưa phải công cụ quản trị dữ liệu đầy đủ
- Không có backend mới cho global search; quick actions hiện dựa trên flow UI có sẵn
- Chưa có browser automation end-to-end để click thật từng nút; hiện phần xác minh CTA dựa trên helper test, API test, compile và boot Streamlit headless
