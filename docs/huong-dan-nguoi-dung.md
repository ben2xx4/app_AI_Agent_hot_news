# Hướng dẫn người dùng

Tài liệu này dành cho người dùng cuối hoặc người demo hệ thống.

Mục tiêu:
- biết vào đâu trước
- biết bấm gì trên giao diện
- biết cách hỏi AI đúng cách
- biết xem dữ liệu chi tiết và mở nguồn bài viết

## 1. Khi mở hệ thống, nên bắt đầu từ đâu
Giao diện hiện tại có 4 workspace ở sidebar:

1. `Tổng quan`
2. `Trợ lý AI`
3. `Explorer`
4. `Hệ thống`

Nếu bạn là người xem demo hoặc người dùng mới:
- bắt đầu ở `Tổng quan`

Nếu bạn muốn hỏi hệ thống bằng tiếng Việt:
- vào `Trợ lý AI`

Nếu bạn muốn tra cứu dữ liệu chi tiết:
- vào `Explorer`

Nếu bạn muốn kiểm tra runtime, scheduler và nguồn dữ liệu:
- vào `Hệ thống`

## 2. Cách dùng workspace Tổng quan
`Tổng quan` là nơi xem nhanh dữ liệu nổi bật trong ngày.

Tại đây bạn sẽ thấy:
- tin tức nổi bật
- giá cả nhanh
- thời tiết theo điểm
- chính sách mới
- giao thông cần chú ý
- biểu đồ nhanh

### Cách thao tác trên từng card
Mỗi card hoặc item preview hiện có nút:

- `Thao tác ▼`

Khi bấm vào, hệ thống sẽ bung ra các lựa chọn thật như:
- `Xem chi tiết`
- `Tóm tắt bằng AI`
- `Hỏi AI`
- `Mở Explorer`
- `Mở nguồn` nếu item có link gốc

### Luồng dùng khuyến nghị
1. Vào `Tổng quan`
2. Chọn một item bạn quan tâm
3. Bấm `Thao tác ▼`
4. Chọn `Xem chi tiết`
5. Từ phần chi tiết, nếu cần thì chọn tiếp:
   - `Tóm tắt bằng AI`
   - `Hỏi AI về mục này`
   - `Mở nguồn`

## 3. Cách dùng workspace Trợ lý AI
`Trợ lý AI` là nơi hội thoại đầy đủ bằng tiếng Việt.

Bạn có thể:
- gõ câu hỏi tự nhiên
- bấm prompt gợi ý
- hỏi lại từ `Câu hỏi gần đây`
- bấm follow-up suggestion sau câu trả lời

### Ví dụ câu hỏi nên dùng
- `Tin hot hôm nay là gì?`
- `Top 5 tin hot`
- `Ở TP HCM có tin hot gì?`
- `Giá vàng SJC hôm nay bao nhiêu?`
- `Hà Nội hôm nay có mưa không?`
- `Có chính sách mới nào về giáo dục không?`
- `Có tuyến đường nào đang bị cấm không?`

### Câu hỏi kiểu tiêu đề bài báo
Bạn cũng có thể hỏi theo kiểu gần giống tiêu đề bài viết, ví dụ:

- `Hôm nay 5.4 là Tết Thanh minh 2026, người Việt cần lưu ý gì?`

Hệ thống sẽ cố tìm các tin liên quan thay vì chỉ nhận diện theo mẫu cứng.

### Mục liên quan trong chat
Sau nhiều câu trả lời, dưới phần trả lời của trợ lý sẽ có:

- `Mục liên quan`

Mỗi item trong đó có nút:

- `Thao tác ▼`

Từ đây bạn có thể:
- xem chi tiết nội bộ
- tóm tắt lại bằng AI
- hỏi AI tiếp về đúng mục đó
- mở nguồn bài viết nếu có URL

## 4. Cách dùng Explorer
`Explorer` dùng để xem dữ liệu chi tiết hơn mà không cần viết SQL.

Hiện có 2 tab:
- `Dữ liệu nghiệp vụ`
- `Bảng kỹ thuật`

### Bạn có thể làm gì trong Explorer
- chọn dataset
- tìm kiếm từ khóa
- lọc theo `pipeline`, `source`, `location`, `item_name`
- đổi sắp xếp `Mới nhất trước` hoặc `Cũ nhất trước`
- chỉnh số dòng preview
- tải `CSV preview`

### Xem kỹ một bản ghi
Trong Explorer, sau khi xem preview:
1. chọn một bản ghi từ danh sách chọn
2. hệ thống sẽ hiện detail preview của bản ghi đó
3. bấm `Thao tác ▼`
4. chọn:
   - `Xem chi tiết`
   - `Tóm tắt bằng AI`
   - `Hỏi AI`
   - `Mở nguồn`

## 5. Cách dùng khu Chi tiết
Khi bạn bấm `Xem chi tiết`, hệ thống sẽ mở một panel chi tiết trong cùng workspace.

Panel này thường hiển thị:
- tiêu đề đầy đủ hơn
- summary dài hơn
- nguồn
- thời gian cập nhật hoặc phát hành
- metadata liên quan như danh mục, lĩnh vực, địa điểm, mặt hàng

Tại đây có thể tiếp tục:
- `Tóm tắt bằng AI`
- `Hỏi AI về mục này`
- `Mở nguồn`

## 6. Cách hiểu dữ liệu đang hiển thị
Không phải lúc nào số lượng bản ghi cũng tăng sau mỗi vòng scheduler.

Lý do:
- nguồn chưa có bài mới
- bài mới bị dedup
- pipeline fetch thành công nhưng không phát sinh record mới

Điều này đặc biệt thường gặp ở:
- `policy`
- `traffic`

Trong khi:
- `price`
- `weather`

thường thấy cập nhật rõ hơn vì là dạng snapshot.

## 7. Cách biết hệ thống có đang cập nhật không
Vào workspace `Hệ thống`.

Ở đây bạn sẽ thấy:
- trạng thái API
- database runtime
- chat runtime
- retrieval
- source health

Nếu bạn đang dùng Docker, scheduler sẽ tự cập nhật theo lịch từng source.

## 8. Luồng demo ngắn gọn nhất
Nếu bạn cần demo nhanh cho giảng viên hoặc hội đồng:

1. Mở `Tổng quan`
2. Xem `Bản tin biên tập`
3. Bấm `Thao tác ▼` trên một tin nổi bật
4. Chọn `Xem chi tiết`
5. Chọn `Tóm tắt bằng AI`
6. Chuyển sang `Trợ lý AI`
7. Hỏi tiếp một câu như:
   - `Top 5 tin hot`
   - `Ở TP HCM có tin hot gì?`
8. Mở `Explorer` để đối chiếu lại dữ liệu

## 9. Lưu ý khi dùng
- AI hiện ưu tiên dữ liệu đã ingest trong hệ thống
- nếu OpenAI không sẵn sàng, hệ thống vẫn fallback sang agent nội bộ
- nếu vừa seed demo mà chưa refresh live, bạn có thể đang thấy dữ liệu demo
- để xem dữ liệu thật hơn trong Docker, nên bật `scheduler` và chạy `refresh_live_data`

## 10. Tài liệu nên đọc tiếp
- `docs/run-local.md`
- `docs/ui.md`
- `docs/ui-functional-map.md`
- `README.md`
