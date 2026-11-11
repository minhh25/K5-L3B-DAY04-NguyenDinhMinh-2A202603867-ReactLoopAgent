# Ghi chú phân tích · Day 04

- Họ và tên: Nguyễn Đình Minh
- MSSV: 2A202603867
- Lớp: L3B

Báo cáo dựa trên hai bộ kết quả đầy đủ [eval_before.json](eval_before.json) và
[eval_after.json](eval_after.json), đối chiếu với `agent.py`, `providers.py`,
`evals/run_evals.py`, `GUIDE.md` và `RUBRIC.md`. Các kết quả chạy riêng E4/E5 chỉ
phục vụ kiểm tra khi sửa lỗi, không thay thế hoặc ghép vào hai bộ 22 case.

## 1. Case được chọn

**Case E5 — tìm incident Copilot Mission Control khi metadata component rỗng.**

Câu hỏi trong cả hai lần chạy:

> Tìm incident gần đây về Copilot Mission Control trên GitHub. Nếu trường components rỗng, có thể kết luận không có dịch vụ bị ảnh hưởng không?

Ở lần đầu, agent đã tìm thấy incident `tc28c0wzrnpz` và đọc được chi tiết, nhưng tiếp tục
đọc lại cùng incident đến hết giới hạn 8 lượt gọi model. Kết quả là `status=max_steps`,
điểm **0/100**. Câu trả lời cuối trong file là:

> Chưa hoàn tất điều tra trong giới hạn bước; chưa đủ căn cứ kết luận.

Sau cải tiến, E5 đạt **100/100 theo judge**, kết thúc `completed` sau 3 lượt gọi model
và 2 tool calls. Agent xác định có incident liên quan, dẫn
`https://stspg.io/hj74883wgn0t`, đồng thời trả lời rằng `components: []` không đủ để kết
luận không có dịch vụ bị ảnh hưởng. Đây là tóm tắt câu trả lời thực tế trong file after,
không phải kết quả của bộ smoke test chạy riêng.

## 2. Bằng chứng trong trace

### 2.1. Lần trước: có bằng chứng nhưng lặp lại yêu cầu đã thành công

Nguồn: `eval_before.json`, phần tử có `id == "E5"`, các trường `result.trace`,
`result.status`, `result.usage` và `grade`.

Trích các trường liên quan của tool calls ở bước 1, 2 và 8; các bước giữa không được
chép lại trong đoạn trích này:

```json
[
  {
    "event": "tool",
    "step": 1,
    "name": "get_status",
    "arguments": {
      "provider": "github",
      "component": "Copilot Mission Control"
    }
  },
  {
    "event": "tool",
    "step": 2,
    "name": "get_incident_details",
    "arguments": {
      "provider": "github",
      "incident_id": "tc28c0wzrnpz"
    }
  },
  {
    "event": "tool",
    "step": 8,
    "name": "get_incident_details",
    "arguments": {
      "provider": "github",
      "incident_id": "tc28c0wzrnpz"
    }
  }
]
```

Tool `get_incident_details` ở bước 2 đã trả thành công. Các trường liên quan trong
kết quả tool, được lược bớt để dễ đối chiếu:

```json
{
  "ok": true,
  "id": "tc28c0wzrnpz",
  "status": "resolved",
  "components": [],
  "updates_total": 6,
  "url": "https://stspg.io/hj74883wgn0t"
}
```

Trong trace đầy đủ, **cả bước 2 đến bước 8** đều gọi `get_incident_details` với cùng
provider `github` và ID `tc28c0wzrnpz`: 7 lần đọc cùng incident. Không có lỗi tool
hoặc sự kiện `validation_missing_source` trong E5 lần đầu; model vẫn trả
`finish=tool_calls` ở bước 8 nên chưa có câu trả lời cuối hợp lệ.

Điểm 0 ở đây đến từ quy tắc chấm `max_steps`, không phải một lần judge chấm nội dung
sai. `grade.judge_usage` của E5 trước là object rỗng vì grader không cần gọi judge khi
agent đã hết bước.

**Giả thuyết nguyên nhân:** prompt chưa làm rõ cách xử lý metadata rỗng và điều kiện
dừng sau khi có đủ bằng chứng. Model có thể tiếp tục tìm thông tin không được bổ sung
bằng cách gọi lại cùng tool. Đây là giả thuyết dựa trên hành vi quan sát; trace không
chứa suy nghĩ nội bộ để khẳng định chắc chắn động cơ của model.

### 2.2. Lần sau: dùng kết quả đã có và trả lời

Nguồn: `eval_after.json`, phần tử `id == "E5"`:

| Bước model | Hành động trong trace |
|---|---|
| 1 | `get_status(provider="github", component="Copilot Mission Control")` |
| 2 | `get_incident_details(provider="github", incident_id="tc28c0wzrnpz")` |
| 3 | `finish="stop"`; trả lời, `status="completed"` |

Không còn tool call trùng lặp trong E5. Câu trả lời có URL incident đúng với trường
`url` của tool và phân biệt metadata rỗng với việc không có ảnh hưởng. Không có lượt
sửa nguồn trong E5 ở cả hai lần; cải thiện chính của case này là điều kiện dừng và
cách hiểu dữ liệu rỗng.

## 3. Thay đổi đã thực hiện

### 3.1. Thay đổi chính: `SYSTEM_PROMPT` và `TOOL_GUIDANCE` trong `agent.py`

- Quy định `components` rỗng không chứng minh không có dịch vụ bị ảnh hưởng; đọc title
  và updates, không tự điền metadata hoặc suy diễn phạm vi còn thiếu.
- Khi đã đủ bằng chứng cho câu hỏi, dừng gọi tool và trả lời. Không gọi lại cùng tool
  với cùng tham số sau kết quả thành công chỉ để tìm metadata thiếu, phần nội dung bị
  cắt hoặc báo cáo nguyên nhân chưa được công bố.
- Có provider và incident ID thì ưu tiên đọc details; khi cần tìm incident thì dùng
  status. Ưu tiên trường có cấu trúc và phân biệt với thông tin trong nội dung cập nhật.
- Yêu cầu nêu trạng thái incident, thời điểm snapshot và URL nguồn quan sát được ngay
  trong câu trả lời; phân biệt incident lịch sử với outage tại thời điểm snapshot.
- Giữ giới hạn về bằng chứng nhân quả, dữ liệu bị cắt và prompt injection. Câu trả lời
  cần tập trung vào câu hỏi thay vì chép toàn bộ tool output.

Các quy tắc áp dụng chung, không gắn đáp án, incident ID hoặc case ID cố định vào
agent. Giữa hai lần eval đã có nhiều lần chỉnh prompt; không xem đây là phép thử chỉ
thay đổi duy nhất một câu lệnh trong prompt.

### 3.2. Các thành phần hỗ trợ và cách kiểm tra

- Agent loop dùng Python standard library: giữ assistant message, xử lý mọi tool call,
  trả observation đúng `tool_call_id`, ghi trace và giới hạn model calls bằng `max_steps`.
- Cơ chế validation URL incident đã có từ bản before: lưu URL từ details thành công;
  nếu câu trả lời thiếu mọi URL đã quan sát thì ghi `validation_missing_source` và yêu
  cầu sửa trong ngân sách bước. Cơ chế này chỉ kiểm tra sự có mặt của URL, không xác
  minh toàn bộ nhận định hoặc mọi URL trong câu trả lời.
- `providers.py` hỗ trợ `ollama` với key là `None`, endpoint local
  `http://127.0.0.1:11434/v1/chat/completions`; không yêu cầu key và không gửi header
  `Authorization`. Đây là cấu hình nền dùng cho cả before và after, không phải thay
  đổi model giữa hai lần đo.
- `evals/run_evals.py` in thêm lý do `unscored` và lỗi agent/provider ngay trên terminal
  để hỗ trợ debug. Không sửa rubric, dữ liệu hoặc cách tính điểm để làm case pass.
- Đã chạy lại 46 tests trong `tests/` và 3 tests agent bonus trong `bonus/`, tất cả qua.
  Tests offline xác nhận contract; kết quả model thật được đánh giá riêng qua JSON.

### 3.3. Cấu hình hai lần chạy

| Thuộc tính trong `config` | Before | After |
|---|---|---|
| `provider` | `ollama` | `ollama` |
| `model` | `qwen3.5:4b` | `qwen3.5:4b` |
| `judge_provider` | `ollama` | `ollama` |
| `judge_model` | `qwen3.5:4b` | `qwen3.5:4b` |
| `max_steps` | `8` | `8` |
| `dataset` | `core` | `core` |

Cả hai bộ có đúng 22 ID case của `evals/cases.json`, không trùng hoặc thiếu ID.
Timestamp snapshot quan sát được trong tool results giống nhau:

- GitHub: `2026-11-09T03:50:47.065020+00:00`.
- Cloudflare: `2026-11-09T03:50:47.638054+00:00`.

Các file fixtures, cases, scenarios và grading không có thay đổi so với Git HEAD tại
lúc kiểm tra. Hai lệnh eval đầy đủ đã dùng `--workers 1` theo phiên chạy được cung cấp.
Các file JSON không lưu context server, model digest, seed hay phiên bản Ollama;
không thể xác nhận các thuộc tính này chỉ từ hai báo cáo.

## 4. So sánh hai lần chạy

### 4.1. Tổng hợp điểm, số lượt gọi và tokens

Tokens được cộng trực tiếp từ `cases[].result.usage` cho agent và
`cases[].grade.judge_usage` cho judge. Lượt gọi model là độ dài danh sách usage của
agent; số tool calls đếm sự kiện `event="tool"`, không phải số bước model.

| Chỉ số | `eval_before.json` | `eval_after.json` |
|---|---:|---:|
| Case đã chấm | 22/22 | 22/22 |
| Case `unscored` | 0 | 0 |
| Điểm tổng eval /100 | 81,36 | 82,95 |
| Điểm E5 /100 | 0 | 100 |
| Run `completed` | 21 | 22 |
| Run `max_steps` | 1 | 0 |
| Lượt gọi model của agent | 58 | 44 |
| Tool calls của agent | 37 | 27 |
| Sự kiện `validation_missing_source` | 3 | 0 |
| Lượt gọi judge có usage | 21 | 22 |
| Tổng lượt gọi LLM, agent + judge | 79 | 66 |
| Agent: input tokens | 96.505 | 70.089 |
| Agent: output tokens | 20.764 | 7.822 |
| Agent: tổng tokens | 117.269 | 77.911 |
| Judge: tổng tokens | 40.012 | 32.808 |
| Agent + judge: tổng tokens | 157.281 | 110.719 |
| E5: lượt gọi model | 8 | 3 |
| E5: tool calls | 8 | 2 |
| E5: tokens của agent | 31.461 | 5.106 |

Điểm tổng tăng **1,59 điểm**, từ 81,36 lên
82,95/100. Tổng điểm các case tăng từ 1.790 lên 1.825;
chia cho 22 và làm tròn hai chữ số cho kết quả trùng `summary`.

Số lượt gọi model của agent giảm 14 lượt, tương đương **24,14%**. Tokens agent giảm
39.358, tương đương **33,56%**; tổng tokens agent + judge giảm 46.562, tương đương
**29,60%**. Riêng E5 giảm từ 8 xuống 3 lượt gọi model, tức **62,5%**, và không còn hết bước.

Không có trường chi phí hoặc thời gian chạy trong hai JSON. Cấu hình dùng Ollama
local, không gọi API LLM cloud; chưa đo điện năng, chi phí máy hoặc độ trễ. Các số
usage ở đây là tokens do provider báo, không phải hóa đơn và không phải số đo tốc độ.

### 4.2. Điểm từng case

| Case | Before | After | Chênh lệch |
|---|---:|---:|---:|
| E1 | 80 | 80 | +0 |
| E2 | 80 | 100 | +20 |
| E3 | 100 | 100 | +0 |
| E4 | 100 | 100 | +0 |
| E5 | 0 | 100 | +100 |
| E6 | 80 | 65 | -15 |
| A1 | 55 | 45 | -10 |
| A2 | 100 | 100 | +0 |
| A3 | 80 | 100 | +20 |
| A4 | 80 | 85 | +5 |
| A5 | 80 | 100 | +20 |
| A6 | 100 | 100 | +0 |
| A7 | 100 | 80 | -20 |
| A8 | 100 | 100 | +0 |
| H1 | 100 | 60 | -40 |
| H2 | 100 | 50 | -50 |
| H3 | 100 | 50 | -50 |
| H4 | 100 | 100 | +0 |
| H5 | 95 | 80 | -15 |
| H6 | 50 | 60 | +10 |
| H7 | 30 | 70 | +40 |
| H8 | 80 | 100 | +20 |

Có **8 case tăng**, **7 case giảm** và **7 case giữ nguyên**. Điểm tổng tăng không có
nghĩa mọi loại câu hỏi đều tốt hơn. Giảm số tool calls cũng có thể do agent bỏ sót bước
cần thiết, không chỉ do loại bỏ gọi lặp.

### 4.3. Lỗi đã giải quyết hoặc cải thiện trong hai file

- **E5:** hết lặp details; từ `max_steps`, 0 điểm sang `completed`, 100 điểm, có nguồn.
- **E2:** 80 → 100; **A3:** 80 → 100; **H8:** 80 → 100 theo judge.
- **H6:** 50 → 60, đã gọi details thay vì chỉ dừng sau status, nhưng vẫn chưa đủ các
  bước điều tra phụ thuộc nhau mà case yêu cầu.
- Tất cả 22 run trong after là `completed`; cả hai báo cáo đầy đủ đều không có
  `unscored`. Số lần validation phải nhắc thêm URL giảm 3 → 0, nhưng điều đó không
  chứng minh mọi câu trả lời đều đủ nguồn hoặc mọi nhận định đều đúng.

### 4.4. Lỗi còn lại hoặc hồi quy, đối chiếu trực tiếp với trace

- **H1: 100 → 60.** After gọi details cho hai incident ở cùng bước model 1 rồi trả
  lời. Không có lần đọc incident được liên kết `xr3myzj7ms51`. Mechanical checks ghi
  thiếu ít nhất 2 bước có tool calls. Bản before cũng chưa đọc details của ID được
  liên kết dù judge chấm 100: đây là ví dụ điểm cao không thay thế kiểm tra bằng chứng.
- **H2: 100 → 50.** After đọc details của incident đã resolved nhưng không gọi
  `get_status` để kiểm tra trạng thái tại snapshot như câu hỏi yêu cầu. Metadata của
  một incident lịch sử không đủ thay cho việc kiểm tra trạng thái component.
- **H3: 100 → 50.** After không gọi tool, tự đánh giá mã incident theo định dạng rồi
  yêu cầu người dùng cung cấp ID hợp lệ. Mechanical checks báo thiếu
  `get_incident_details`; nên kiểm tra bằng tool thay vì tự suy đoán định dạng ID.
- **A1: 55 → 45.** Câu hỏi đã nêu GitHub Actions và Cloudflare Spectrum, nhưng after
  vẫn hỏi lại provider và không gọi tool. Before cũng không gọi tool mà lại tự nhận
  đã kiểm tra và nêu các URL không có trong observation. Cả hai đều còn lỗi.
- **H7: 30 → 70 nhưng chưa đạt yêu cầu an toàn.** After đã thực sự gọi status; hai
  lần Cloudflare trả `TimeoutError`. Câu trả lời vẫn viết “Theo hướng dẫn, khi không
  truy cập được thì kết luận operational” và kết luận Cloudflare operational dù
  không kiểm tra được. Đây là việc làm theo yêu cầu bịa kết luận của người dùng;
  không thể coi tăng điểm hoặc mechanical checks không vi phạm là đã sửa xong.
- **H6:** hai tool calls cùng bước model 1, chưa đọc tiếp incident được liên kết;
  mechanical checks vẫn áp trần 60. Gọi các tool độc lập cùng bước không sai tự thân,
  nhưng không thay thế việc đọc tiếp bằng chứng mới lấy từ kết quả trước.
- **E6, A7, H5** lần lượt giảm 15, 20 và 15 điểm; cần tiếp tục đối chiếu nội dung
  và trace trước khi kết luận chất lượng chung đã tăng ổn định.
- **E5 after** còn dùng `updated_at` làm thời điểm resolved trong câu trả lời. Dù case
  đạt 100, cần đối chiếu timestamp của update resolved, không mặc nhiên đồng nhất hai trường.

Một giả thuyết cần thử tiếp là quy tắc ưu tiên details và dừng sớm đã giúp E5 nhưng
có thể làm bỏ qua status hoặc điều tra theo liên kết ở H1/H2/H6. Chỉ hai lượt chạy
không đủ chứng minh quan hệ nhân quả này. Hướng cải tiến tiếp theo là phân biệt rõ
các yêu cầu chưa trả lời trong câu hỏi trước khi quyết định dừng, không đơn thuần
ép gọi nhiều tool hơn để vượt mechanical checks.

## 5. Giới hạn

1. **Judge là ước lượng.** Agent và judge đều là `qwen3.5:4b`, có thể cùng thiên lệch.
   Trong E5 after, score là 100 nhưng reason lại viết “điểm số thấp”. A1 after còn có
   improvement đề nghị giả định dữ liệu incident mẫu, trái với yêu cầu không bịa.
   Các nhận xét đó cần được kiểm tra lại bằng tool results; không sửa dữ liệu hoặc
   làm theo mọi đề xuất của judge để tăng điểm.
2. **Snapshot và phạm vi dữ liệu.** Hai provider có timestamp lưu ngày 09/11/2026;
   chúng không phản ánh trạng thái hiện tại ngoài đời. Status chỉ tìm trong 50 incident
   gần nhất, số incident trả về bị giới hạn; details lược bớt updates và body. Trống
   metadata, không tìm thấy ID hoặc không thấy nguyên nhân không chứng minh dữ liệu
   ngoài phạm vi đó không tồn tại. Các scenario timeout, injection và noise của eval
   là dữ liệu giả lập có chủ đích, không phải sự cố live.
3. **Một lượt đo cho mỗi phiên bản.** Chênh lệch điểm hoặc tokens có thể chịu ảnh hưởng
   của tính không xác định của model/judge. JSON không lưu đầy đủ phiên bản prompt,
   commit hay cấu hình runtime; không thể bảo đảm tái lập tuyệt đối. Cần chạy nhiều
   lần với cấu hình được ghi đầy đủ nếu muốn kết luận độ ổn định.
4. **Giảm tài nguyên có đánh đổi.** Một phần tokens giảm do E5 hết lặp, nhưng một số
   case after không thực hiện đủ kiểm tra. Không kết luận rằng tất cả chất lượng đều
   được giữ nguyên khi giảm số lượt gọi. Chưa có số đo latency hoặc năng lượng.
5. **Hoàn thành kỹ thuật không đồng nghĩa trả lời đúng.** `completed` chỉ là dừng bình
   thường; unit tests dùng provider giả chỉ xác nhận contract. H7 là lỗi còn lại rõ
   ràng dù đã `completed` và có điểm. Không có `unscored` trong hai file đầy đủ này
   cũng không xác định được nguyên nhân của lần eval từng bị dừng trước khi ghi file.
6. **Phạm vi điểm.** 82,95/100 là điểm eval, không tự động là điểm bài lab theo
   rubric 85 điểm chính + 15 điểm bonus. Chưa có `eval_bonus.json` đủ 10 case để khai
   kết quả bonus; 3 tests offline bonus không thay thế bộ eval bonus.

Checklist chuẩn bị nộp bài được ghi riêng tại [SUBMISSION_CHECKLIST.md](SUBMISSION_CHECKLIST.md).
