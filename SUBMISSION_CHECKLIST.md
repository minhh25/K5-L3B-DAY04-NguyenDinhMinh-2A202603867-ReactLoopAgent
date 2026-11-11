# Checklist nộp bài · Day 04

- Học viên: Nguyễn Đình Minh — 2A202603867 — L3B
- Đối chiếu: [SUBMISSION.md](SUBMISSION.md), [RULES.md](RULES.md), [RUBRIC.md](RUBRIC.md).
- Ngày kiểm tra: 12/11/2026, giờ Việt Nam.

## Đã kiểm chứng trong workspace

- [x] Tên repo đúng mẫu: `K5-L3B-DAY04-NguyenDinhMinh-2A202603867-ReactLoopAgent`.
- [x] Có `agent.py` đã hoàn thiện loop, trace, xử lý lỗi, giới hạn bước và validation URL.
- [x] Không dùng framework agent; triển khai dùng Python standard library.
- [x] `python3 -m unittest discover -s tests -v`: **46 tests qua**.
- [x] `python3 -m unittest discover -s bonus -p 'test_*.py' -v`: **3 tests qua**.
- [x] `eval_before.json` đủ 22 ID case không trùng, đã chấm 22/22; điểm **81,36/100**, không null.
- [x] `eval_after.json` đủ 22 ID case không trùng, đã chấm 22/22; điểm **82,95/100**, không null.
- [x] Hai file có `config` giống nhau: agent/judge `ollama` + `qwen3.5:4b`, `max_steps=8`, dataset `core`.
- [x] Metadata snapshot quan sát được giống nhau: GitHub và Cloudflare ngày 09/11/2026.
- [x] Không có thay đổi ở `fixtures/`, `evals/cases.json`, `evals/scenarios.py`, `evals/grading.py`, `RUBRIC.md` so với Git HEAD lúc kiểm tra.
- [x] `NOTES.md` đủ 5 mục, dựa trên hai file eval đầy đủ; có case E5, trace, thay đổi, bảng điểm/tokens, lỗi hồi quy và giới hạn.
- [x] Báo cáo dùng đúng tên **`NOTES.md`** theo yêu cầu nộp bài.
- [x] `git ls-files .env .env.example` chỉ hiện `.env.example`; `.env` được Git ignore.
- [x] Không thấy lịch sử commit đường dẫn `.env` qua `git log --all -- .env`.
- [x] Quét các file văn bản được theo dõi và file nộp liên quan không phát hiện mẫu key phổ biến hoặc private key; hai JSON không có trường credential có giá trị. Đây là kiểm tra theo mẫu, không bảo đảm nhận diện mọi dạng bí mật.
- [x] `git diff --check` không báo lỗi whitespace sau khi hoàn thiện báo cáo.
- [x] URL repo truy cập được không đăng nhập: [repo GitHub](https://github.com/minhh25/K5-L3B-DAY04-NguyenDinhMinh-2A202603867-ReactLoopAgent). GitHub API trả HTTP 200, `private=false`, `visibility=public`.
- [x] Có sẵn trace demo: E5 before lặp tool đến hết bước; E5 after gọi status → details → trả lời có nguồn.

Hai file eval được giữ nguyên nội dung khi viết báo cáo. Cấu hình server/context/model
digest không được lưu trong JSON; mục đối chiếu cấu hình chỉ xác nhận các trường
đã có trong `config` và metadata snapshot, không khẳng định mọi tham số runtime giống nhau.

## Cần học viên hoàn tất trước khi nộp

- [ ] Đọc lại `NOTES.md`, đối chiếu các lỗi H1/H2/H3/H7 và có thể giải thích code khi được hỏi.
- [ ] Commit các thay đổi và hai file eval: hiện các kết quả/báo cáo còn ở workspace.
- [ ] Push bản cuối lên nhánh `main`; mở lại repo công khai để kiểm tra đủ `agent.py`, `eval_before.json`, `eval_after.json`, `NOTES.md` và các file hỗ trợ đã sửa.
- [ ] Khi được yêu cầu demo, trình bày được một trace nhiều bước và một lỗi chưa giải quyết; có thể dùng E5 và H7 trong báo cáo.
- [ ] Dán link repo vào đúng bài Day 04 trên LMS bằng tài khoản học viên.
- [ ] Xác nhận ca học/hạn nộp của key coach và thời điểm nộp trên LMS. Chưa có thông tin để đánh dấu đã nộp đúng hạn.

### Lệnh để lưu và đẩy bản cuối sau khi tự kiểm tra

Các lệnh dưới đây là hướng dẫn, chưa được thực thi trong phiên chuẩn bị báo cáo:

```bash
git add agent.py providers.py run.py evals/run_evals.py tests/test_ollama.py \
  README.md OLLAMA_LOCAL.md NOTES.md SUBMISSION_CHECKLIST.md \
  eval_before.json eval_after.json

git diff --cached --stat
git commit -m "Complete local Ollama agent and evaluation report"
git push origin main
```

Repo đang ở nhánh `main` và remote `origin` là URL GitHub ở trên. Sau khi push, kiểm
tra lại các file trên GitHub trước khi dán link lên LMS:

```text
https://github.com/minhh25/K5-L3B-DAY04-NguyenDinhMinh-2A202603867-ReactLoopAgent
```

Theo SUBMISSION.md, hạn mặc định cho ca 9:00–13:00 và 14:00–18:00 là 23:59 cùng
ngày; ca 16:30–20:00 là 12:00 trưa hôm sau, trừ khi key coach thông báo khác.
Không tự suy ra ca học hoặc xác nhận đúng hạn chỉ từ tên lớp L3B.

## Bonus tùy chọn

Chưa có `eval_bonus.json` đủ 10 case. Không khai điểm bonus chỉ từ 3 tests offline.
Bài chính vẫn có đủ hai bộ eval 22 case và báo cáo; bonus không bắt buộc.
