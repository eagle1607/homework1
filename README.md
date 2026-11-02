# homework1

API quản lý ticket hỗ trợ khách hàng (FastAPI + SQLAlchemy + PostgreSQL), dùng OpenAI để phân loại tin nhắn khách hàng thành ticket.

## Yêu cầu

- Python 3.11+
- PostgreSQL (ví dụ Supabase) hoặc SQLite cho chạy thử
- OpenAI API key

## Cài đặt

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Tạo file `.env` từ mẫu rồi điền giá trị thật:

```bash
cp .env.example .env
```

Các biến bắt buộc:

| Biến | Ý nghĩa |
|---|---|
| `DATABASE_URI` | Chuỗi kết nối DB, ví dụ `postgresql+psycopg://user:password@host:5432/dbname` hoặc `sqlite:///./app.db` |
| `OPENAI_API_KEY` | Key OpenAI |
| `JWT_SECRET` | Chuỗi ngẫu nhiên ≥ 32 ký tự, tạo bằng `python3 -c "import secrets; print(secrets.token_urlsafe(32))"` |

Các biến tuỳ chọn: `OPENAI_MODEL` (mặc định `gpt-5-mini`), `COOKIE_SECURE` (`true` khi chạy HTTPS), `AI_MAX_REQUEST_PER_HOUR` (số ticket tối đa mỗi user tạo qua `/users/complain` trong 1 giờ, `0` = không giới hạn).

## Chạy server

Chạy từ thư mục gốc của project:

```bash
uvicorn app.main:app --reload
```

- API: http://localhost:8000
- Tài liệu Swagger: http://localhost:8000/docs

Bảng được tạo tự động khi server khởi động. Lưu ý: việc này không sửa bảng đã tồn tại, nên khi đổi model phải xoá bảng cũ (hoặc migrate) rồi chạy lại.

## Seed dữ liệu mẫu

Chạy từ thư mục gốc (mặc định 1000 ticket, truyền số để đổi):

```bash
python -m scripts.seed_tickets 200
```

- Script dùng cùng `DATABASE_URI` trong `.env` và tự tạo bảng nếu chưa có.
- Lần chạy đầu, script tự tạo user `system` (mật khẩu ngẫu nhiên, không đăng nhập được) để gắn ticket. Chạy lại không tạo trùng.
- Ticket được tạo ngẫu nhiên intent, severity, status trong 90 ngày gần nhất và gán cho các user đang có (gồm `system` và user bạn đã đăng ký).

## Gọi API cần đăng nhập

Đăng nhập trả về cookie `access_token`; các API còn lại cần cookie này:

```bash
curl -c cookies.txt -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "password": "demo1234"}'

curl -b cookies.txt http://localhost:8000/tickets/queue
```
