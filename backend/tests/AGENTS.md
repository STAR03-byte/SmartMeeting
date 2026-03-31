# Backend Tests AGENTS.md

`backend/tests/` 是后端 pytest 测试套件（偏集成测试）。测试夹具集中在 `conftest.py`，通过 dependency override 注入测试 DB 与鉴权。

> 继承：`backend/AGENTS.md`（后端全局约定）。

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| 公共夹具/测试 DB | `conftest.py` | 覆盖 `get_db`，使用 in-memory sqlite + `StaticPool` |
| 认证登录与 /me | `test_auth_api.py` | 创建用户→登录→携带 Bearer 调 /me |
| 端到端冒烟链路 | `scripts/dev/smoke.py` | 按关键路径串行跑单测用例 |

## CONVENTIONS

- 文件命名：`test_*.py`，用例优先覆盖 `/api/v1/...` 的关键流程。
- 避免依赖外部 MySQL：测试默认使用 sqlite（见 `conftest.py` 的 env 与 engine）。
- 当新增/调整 endpoint 行为：先补/改对应测试，再调整实现。

## COMMANDS

```bash
python -m pytest backend/tests -v --tb=short

# 快速回归关键链路（仅 smoke 阶段）
python scripts/dev/smoke.py
```

## ANTI-PATTERNS

- 不要引入对真实外部服务的硬依赖（LLM/Whisper/DB），需要时用 mock 或回退路径。
- 不要让测试依赖执行顺序或共享全局状态；夹具要自行清理 overrides。
