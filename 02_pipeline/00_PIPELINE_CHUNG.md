# Quy ước chung cho pipeline

## Cấu trúc đề xuất
- `fetch/`: logic lấy dữ liệu
- `parse/`: logic parse theo nguồn
- `normalize/`: chuẩn hóa schema nội bộ
- `store/`: ghi raw và clean
- `tests/`: test parser

## Dữ liệu đầu vào
- URL/RSS/API endpoint
- source config
- schedule config

## Dữ liệu đầu ra
- raw document
- normalized records
- log job

## Logging bắt buộc
- start_time
- end_time
- source_name
- total_fetched
- total_success
- total_failed
- error_message

## Xử lý lỗi
- retry có kiểm soát
- timeout
- lưu raw dù parse lỗi nếu fetch thành công
- đánh dấu trạng thái job
