# API AGENTS.md

`frontend/src/api/` 统一封装前端请求层：Axios client、类型定义、领域 API wrapper 与基础测试。

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| HTTP 客户端与拦截器 | `client.ts` | Bearer 注入、超时、错误文本归一化 |
| 认证接口 | `auth.ts` | 登录/当前用户接口约定 |
| 会议域接口 | `meetings.ts` | CRUD、上传、转写、后处理 |
| 任务域接口 | `tasks.ts` | 查询过滤、状态更新 |
| 类型中心 | `types.ts` | payload/response 统一来源 |
| API 单测 | `*.test.ts` | 约束序列化/错误处理与 URL 规则 |

## CONVENTIONS

- 所有请求必须复用 `apiClient`，禁止新建并行 axios 实例。
- URL 统一走后端版本前缀（当前为 `/api/v1/...`），不要在 view/store 拼接裸路径。
- 导出函数返回值与 `types.ts` 对齐，避免隐式 `any`。
- query 参数在 wrapper 内完成清洗（如 trim/null 归一），页面层只传业务语义值。
- 异常文案统一经 `getApiErrorMessage` 归一，不直接向上抛裸 axios 错误对象。

## ANTI-PATTERNS

- 在页面或 store 里复制 URL 与参数拼装逻辑。
- 在 wrapper 返回未声明结构（破坏类型契约）。
- 跳过 API 测试就改动请求序列化规则。
- 在 `client.ts` 外重复定义 token 存储 key。
