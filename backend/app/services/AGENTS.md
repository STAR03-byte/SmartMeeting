# Services AGENTS.md

`backend/app/services/` 是后端业务主层，负责会议编排、任务抽取、鉴权服务、音频与 LLM/Whisper 集成。

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| 会议主流程 | `meeting_service.py` | 创建/查询/摘要生成/任务生成主链路 |
| LLM 摘要与任务抽取 | `llm_service.py` | 失败需回退 rule-based 路径 |
| 音频处理与存储 | `audio_service.py`, `whisper_service.py` | 文件与转写错误需显式抛出 |
| 任务规则与状态 | `task_service.py` | 优先级推断、行动项解析 |
| 用户/鉴权服务 | `user_service.py`, `auth_service.py` | 与 endpoint 解耦，保持纯服务接口 |

## CONVENTIONS

- 服务函数必须有完整类型标注，返回类型可读且稳定。
- 事务边界收敛在服务层：写操作统一 `add/commit/refresh`，避免分散提交。
- 外部能力（LLM/Whisper）必须提供 fallback 或可观测失败路径，不吞异常。
- endpoint 只编排 HTTP 输入输出；业务判断、数据库查询和跨模型流程放在 services。
- 命名遵循动作语义：`create_*`, `list_*`, `generate_*`, `build_*`, `extract_*`。

## ANTI-PATTERNS

- 在 endpoint 里复制 services 的业务逻辑。
- 用 `Any` 或弱类型返回值掩盖 schema/model 不一致。
- LLM 调用失败后直接静默成功（必须返回 fallback 来源标识）。
- 跨函数隐式提交事务（导致部分写入不可控）。

## NOTES

- `meeting_service.py` 是最高复杂度文件之一（多模型 + LLM/rule 双路径），改动前先确认回退策略不被破坏。
- 涉及任务生成逻辑时需同时检查 `task_service.py` 规则函数，避免行为分叉。
