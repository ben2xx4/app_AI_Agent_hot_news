# Kien truc tong the

## Muc tieu
He thong duoc to chuc theo tung lop ro rang de co the thay parser, thay nguon va mo rong AI ma khong lam vo luong xu ly du lieu.

## Cac lop chinh
1. Ingestion layer
   - Pipeline doc lap cho `news`, `price`, `weather`, `policy`, `traffic`
   - Moi pipeline co retry, timeout, logging, raw storage
2. Raw storage
   - Luu payload goc theo cau truc `pipeline/source/ngay`
   - Luu kem metadata fetch time, source name, source url
3. Processing layer
   - Cleaner
   - Normalizer
   - Validator
   - Exact dedup va near dedup cho news
   - Chunking document cho policy/news
4. Primary storage
   - PostgreSQL la database chinh
   - Alembic dung de quan ly migration
5. Retrieval layer
   - Bang `document_embeddings` de chua chunk va san sang cho embedding that
   - MVP uu tien truy van SQL/keyword; embedding that duoc bat khi co `OPENAI_API_KEY`
6. Backend/API
   - FastAPI
   - Router tach theo domain
   - Service layer tach khoi repository
7. AI layer
   - Intent router
   - Tool registry noi bo
   - OpenAI Responses API function calling khi du cau hinh
   - Fallback deterministic khi chua co API key
8. UI layer
   - Streamlit
   - Trang tin hot, gia moi nhat, chat tieng Viet

## Quy tac thiet ke da chot
- Khong de AI truy cap web truc tiep
- Khong de route thao tac DB truc tiep, moi truy van di qua service
- Pipeline va API chia file rieng
- Moi nguon deu cau hinh bang YAML
- Moi phase lon deu co cap nhat vao `PLAN.md` va `PROGRESS.md`

## Gia dinh quan trong
- Trong repo nay uu tien luong demo chay on dinh tren local, vi vay moi pipeline deu co fixture fallback.
- Moi truong thuc te se dung PostgreSQL, nhung test va fallback local co the dung SQLite de khong bi block boi driver.
