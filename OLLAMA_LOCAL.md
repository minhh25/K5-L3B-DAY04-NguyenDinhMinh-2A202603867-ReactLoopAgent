# Chạy lab bằng Ollama local trên macOS

Repo dùng Python standard library, Python 3.10 trở lên. Không cần cài SDK, không cần
file `.env`, không cần API key thật hoặc key giả. Agent và judge dùng cùng server local:

```python
'ollama': (None, 'http://127.0.0.1:11434/v1/chat/completions')
```

URL trong code là `http://...`, không thêm dấu `\` trước `:`. Adapter không gửi
`Authorization` cho Ollama, không đọc `.env` và không tự fallback sang cloud.
Các provider cloud gốc vẫn được giữ để tương thích với lab, chỉ dùng khi bạn chọn rõ.

## 1. Server Ollama và model

Máy đã kiểm tra trong phiên làm việc: MacBook Air M3, RAM 16 GB, GPU 10 nhân.
Model được chọn là `qwen3.5:4b` để ưu tiên thời gian chạy. Đây không phải cam kết
đạt toàn bộ eval hoặc đạt điểm tối đa; cần kiểm tra trace thực tế.

Nếu dùng ứng dụng Ollama trên Mac:

```bash
open -a Ollama
ollama pull qwen3.5:4b
ollama list
curl http://127.0.0.1:11434/api/version
```

Đặt **Context length = 16384 (16K)** trong Settings của Ollama để bắt đầu làm lab.
16K là cấu hình khởi đầu cho máy này, không phải đảm bảo mọi case dài đều vừa.
Nếu cần tăng lên 32K, theo dõi RAM và giữ nguyên cấu hình giữa hai lần eval so sánh.

Nếu muốn tự chạy server hoàn toàn từ terminal: thoát ứng dụng Ollama bằng Quit trước
để giải phóng cổng 11434, rồi chạy trong **terminal thứ nhất**:

```bash
OLLAMA_HOST=127.0.0.1:11434 \
OLLAMA_CONTEXT_LENGTH=16384 \
OLLAMA_NUM_PARALLEL=1 \
ollama serve
```

Giữ terminal đó mở. Dùng **terminal thứ hai** để tải model nếu chưa có:

```bash
ollama pull qwen3.5:4b
curl http://127.0.0.1:11434/api/version
```

Chọn một cách chạy server. Lỗi `address already in use` thường do server/app đang chạy;
không mở thêm server trên cùng cổng. Đặt `OLLAMA_CONTEXT_LENGTH` ở terminal chạy Python
không thay đổi context của một server đã chạy trước đó.

## 2. Biến môi trường trong terminal dự án

Mở terminal tại thư mục repo, dùng zsh mặc định của macOS:

```bash
labPython="$(command -v python3)"
"$labPython" --version

export PROVIDER=ollama
export MODEL=qwen3.5:4b
export JUDGE_PROVIDER=ollama
export JUDGE_MODEL=qwen3.5:4b
```

Không cần `OPENAI_API_KEY`, `OLLAMA_API_KEY` hay `source .env`. Các key có sẵn trong
môi trường cũng không được gửi tới Ollama. Mở terminal mới thì chạy lại khối trên.

Nếu đã cài `uv` và muốn giống lệnh Windows bạn đưa, thay dòng chọn Python bằng:

```bash
labPython="$(uv --no-cache python find --offline)"
```

Máy đã kiểm tra có Python 3.13.3 nhưng chưa tìm thấy `uv`, nên dùng `python3` là đủ.
PowerShell `$env:MODEL = '...'` đổi thành `export MODEL='...'`; `& $labPython ...`
đổi thành `"$labPython" ...` trên zsh.

## 3. Test offline và chạy thử thật

```bash
"$labPython" -m unittest discover -s tests -v
"$labPython" -m unittest discover -s bonus -p 'test_*.py' -v

"$labPython" run.py 'Kiểm tra GitHub Actions và dẫn nguồn.'

"$labPython" evals/run_evals.py --case E2 --workers 1 \
  --output eval_results_ollama_e2.json
```

Unit tests dùng fake provider, không cần mạng hoặc Ollama. Hai lệnh sau dùng model thật.
Agent gọi model, giữ nguyên assistant message, thực thi mọi tool call, trả tool result
với đúng `tool_call_id`, rồi lặp trong giới hạn bước. `trace` ghi `model`, `tool`,
`error`, `validation_missing_source`; không yêu cầu model in chain-of-thought.

Adapter Ollama tắt thinking bằng `reasoning_effort='none'`, đặt temperature 0.2,
giới hạn output 2048 token/lượt, timeout 180 giây/request. `finish='length'` hoặc
provider lỗi sẽ trả `error`; không báo `completed`. Nếu thay các tham số này, giữ
nguyên giữa hai phiên bản dùng để so sánh.

`snapshot` đọc fixtures được cung cấp. Sau khi tải model, agent và judge có thể chạy
local, không cần gọi dịch vụ cloud. `--mode live` vẫn cần Internet để đọc status API:

```bash
"$labPython" run.py --mode live 'Kiểm tra GitHub Actions và dẫn nguồn.'
```

Snapshot không đại diện cho trạng thái thực tế hiện tại. Unit tests pass chỉ xác nhận
contract, không chứng minh model thật trả lời đúng. Một case E2 không phải điểm toàn bộ lab.

## 4. Quy trình before/after theo GUIDE

Chỉ chạy toàn bộ sau khi lệnh thử và E2 đã hoạt động:

```bash
"$labPython" evals/run_evals.py --workers 1 --output eval_before.json
```

Đọc `summary`, `cases[].result.trace`, `cases[].grade.reason` và
`cases[].grade.improvement`. Chọn lỗi thật, ghi evidence và nguyên nhân vào `NOTES.md`,
rồi sửa prompt hoặc loop để giải quyết lỗi đó. Agent hiện đã có validation nguồn theo
`tests/test_validation.py`; không coi code chưa triển khai ban đầu là một baseline đã chạy.

Sau thay đổi có căn cứ, chạy tests và eval lần hai:

```bash
"$labPython" -m unittest discover -s tests -v
"$labPython" evals/run_evals.py --workers 1 --output eval_after.json
```

Giữ cùng model agent, judge, context server, snapshot, max steps và dataset. Dùng
`--workers 1` để bắt đầu trên máy RAM 16 GB. Không chạy hai bộ eval đồng thời.

Nếu làm bonus:

```bash
"$labPython" run.py --bonus --max-steps 16 'Kiểm tra status GitHub, Vercel và npm.'
"$labPython" evals/run_evals.py --bonus --workers 1 --output eval_bonus.json
```

Agent lấy schemas/system prompt từ tools bonus, trả lỗi làm observation và giới hạn
retry 429 cho cùng yêu cầu ở một lần thử lại. `Retry-After` quá 5 giây sẽ được hoãn
thay vì gọi API liên tục; agent phải báo phần chưa kiểm tra được. Khi còn `next_offset`,
model cần gọi trang tiếp theo nếu câu hỏi đòi hỏi, không tự tuyên bố đã đọc hết.

Không sửa fixtures, cases, scenarios, grading hoặc kết quả JSON để làm điểm đẹp hơn.
Chỉ điền `NOTES.md` từ trace và hai lần eval thật. Nếu có `unscored`, điểm tổng là
`null`; đọc lỗi và khắc phục trước khi chạy lại. Tự chấm bằng cùng model có thể thiên lệch.
Đối chiếu yêu cầu nộp bài trong [SUBMISSION.md](SUBMISSION.md).

## 5. Kiểm tra lỗi local

- Không kết nối được: kiểm tra `curl http://127.0.0.1:11434/api/version`.
- HTTP 404: kiểm tra `ollama list` và tên `MODEL` trùng model đã tải.
- HTTP 400: kiểm tra model hỗ trợ tool calling và phiên bản Ollama.
- Timeout: kiểm tra tải máy; tăng timeout local nếu cần và giữ cấu hình giữa các eval.
- `finish='length'`: xem trace; nếu output thực sự bị cắt, cân nhắc tăng giới hạn
  token local thay vì coi câu trả lời dở dang là hoàn thành.
- Judge trả JSON sai: xem `grade.reason`; test offline không đánh giá khả năng sinh
  JSON của model thật. Không sửa grading hoặc tự điền điểm.
- Xem `ollama ps` trong lúc model đang chạy để kiểm tra context và GPU sử dụng.

Khi một case là `unscored`, runner in ngay `lý do` và `lỗi agent/provider` nếu có.
Đọc các dòng này trước khi dừng tiến trình: file tổng chỉ được ghi sau khi tất cả case
kết thúc. `SYSTEM_PROMPT` chỉ điều khiển agent; lỗi JSON của judge hoặc lỗi kết nối
Ollama cần được phân tích từ thông báo lỗi, không thể bảo đảm sửa chỉ bằng prompt agent.

Tham khảo chính thức: [OpenAI compatibility](https://docs.ollama.com/api/openai-compatibility),
[Context length](https://docs.ollama.com/context-length).

## Kiểm chứng trong lần setup Ollama ban đầu

- 46 tests trong `tests/` và 3 tests trong `bonus/` đều qua.
- Câu hỏi thử GitHub Actions đã trả `completed` và gọi được `get_status`.
- E2 với bản code cuối: `completed`, judge local chấm 80/100, không có vi phạm
  mechanical checks. Trace có bước yêu cầu sửa câu trả lời thiếu URL nguồn.
- Kết quả E2 thật nằm trong `eval_results_ollama_e2.json`; bản smoke đầu tiên được
  giữ nguyên tại `eval_results_ollama_e2_initial.json`. Đây không phải hai bộ eval đầy đủ.
- Server có sẵn khi kiểm chứng dùng context 4096, model chạy 100% GPU theo `ollama ps`.
  Cấu hình 16K ở trên là khuyến nghị cho các case dài, chưa được benchmark trong phiên này.
- Các lần kiểm chứng setup này chưa chạy toàn bộ 22 case, 10 case bonus hoặc tạo
  báo cáo before/after đầy đủ. Điểm một case và `completed` không chứng minh mọi nhận định của model đều đúng;
  cần đọc trace và đối chiếu lại nhận xét của judge.
