# SmartMeeting 双 LLM 网关设计

**日期**: 2026-03-30  
**状态**: Draft  
**项目**: SmartMeeting  
**基线提交**: `ed4b18b`

## 1. 背景

当前 SmartMeeting 的会议摘要与任务抽取已经可用，但 LLM 接入仍是单一后端：`llm_service.py` 直接面向 OpenAI-compatible SDK。这样做的短板是：

- 主模型不可用时，只能退到规则版，缺少可配置的备用模型路径。
- 本地模型（如 Ollama）无法与云端模型统一切换。
- 配置项与失败路径还不够显式，不利于后续生产部署。

本设计的目标是把 LLM 层收敛成一个小型网关：**默认 OpenAI-compatible，备用 Ollama，最终仍可回退规则引擎**。

## 2. 目标

1. 保持现有服务调用入口不变：`generate_meeting_summary` / `extract_action_items`。
2. 支持主后端与备用后端两套 provider 配置。
3. 默认主后端优先使用 OpenAI-compatible API。
4. 主后端失败时自动切换到备用后端（Ollama）。
5. 主备都失败时继续退回现有规则版摘要/任务抽取。
6. 失败与回退路径可观测，避免“静默成功”。

## 3. 范围

### In Scope

- `backend/app/core/config.py` 增加主/备 LLM 配置项
- `backend/app/services/llm_service.py` 增加 provider 路由与 fallback
- `meeting_service.py` 继续复用现有摘要/任务编排入口
- 为摘要与任务抽取保留统一错误处理和回退来源标识
- 文档补充环境变量与使用方式

### Out of Scope

- 前端模型选择 UI
- 按会议粒度选择 provider
- 多备用模型池或负载均衡
- 提示词编辑器 / 模板中心
- 流式输出

## 4. 方案对比

### 方案 A：双 provider 网关 + 规则兜底（推荐）

在 `llm_service.py` 内部维护 provider 选择逻辑，默认请求 OpenAI-compatible，失败后切 Ollama，仍失败才进入现有规则逻辑。

优点：
- 改动集中，兼容现有调用链
- 可同时支持云端与本地模型
- 风险最小，回退清晰

缺点：
- provider 逻辑会比当前更复杂一些

### 方案 B：按能力拆分为两个独立服务

摘要一个服务，任务抽取一个服务，每个服务都可独立配置主备 provider。

优点：
- 隔离更强

缺点：
- 重复配置与重复错误处理
- 当前规模下过度拆分

### 方案 C：只做 OpenAI-compatible 兼容层

把 Ollama 通过 OpenAI-compatible 接口接入，不做显式备用策略。

优点：
- 接口最统一

缺点：
- 无法表达“主云端、备本地”的明确优先级
- 健康切换能力弱

**结论**：采用方案 A。

## 5. 用户故事

### 5.1 运营/管理员

- 我希望在云端 LLM 不可用时，系统仍能用本地模型继续产出摘要和任务。

### 5.2 开发/运维

- 我希望通过配置切换主备 provider，而不改业务代码。
- 我希望知道当前调用到底命中了哪个 provider。

### 5.3 普通用户

- 我希望会议后处理尽量稳定，不因单点 LLM 故障而完全失效。

## 6. 功能设计

### 6.1 Provider 顺序

默认顺序：

1. OpenAI-compatible 主后端
2. Ollama 备用后端
3. 规则版 fallback

当主后端返回网络错误、鉴权错误、限流错误、服务不可用或超时等可恢复故障时，系统应尝试备用 provider。

### 6.2 配置模型

配置应保持“主后端 + 备用后端”两组独立配置：

- `LLM_PROVIDER=openai|ollama|mock`
- `LLM_API_KEY`
- `LLM_BASE_URL`
- `LLM_MODEL`
- `LLM_FALLBACK_PROVIDER=ollama|mock|none`
- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL`

兼容原则：

- 现有只配置 `LLM_*` 时，行为保持不变。
- 若配置了 `OLLAMA_*` 且 `LLM_FALLBACK_PROVIDER=ollama`，则启用本地备用。
- 若备用 provider 未配置完整，则直接跳过备用，进入规则 fallback。

### 6.3 调用策略

- `generate_meeting_summary` 和 `extract_action_items` 仍作为对外统一入口。
- 内部先按 provider 解析客户端，再执行请求。
- 每次调用最多尝试 2 个 LLM provider。
- 任何 provider 都失败后才走规则逻辑。

### 6.4 可观测性

每次摘要/抽取调用记录：

- 命中的 provider
- 使用的 model
- 失败原因类别
- 最终是否落到规则 fallback

日志应避免打印完整转写内容，防止敏感信息扩散。

## 7. 后端设计

### 7.1 配置层

`backend/app/core/config.py` 增加：

- 主 provider 相关字段（保留现有字段）
- 备用 provider 的 base URL、model、可选 API key

其中 Ollama 默认不需要 API key。

### 7.2 服务层

`backend/app/services/llm_service.py` 调整为三层：

1. **Provider 解析层**：根据配置构造可用客户端
2. **能力调用层**：摘要、任务抽取、健康检查
3. **Fallback 层**：主 provider 失败后切备用，仍失败则返回规则版结果

### 7.3 接口稳定性

- 对外函数名不变。
- 返回类型不变。
- 摘要和任务抽取的上层调用方无需知道 provider 细节。

### 7.4 错误处理

建议将以下情况视为可切换到备用 provider：

- 网络连接错误
- 5xx 服务错误
- 限流错误
- 认证失败（若配置明确允许 fallback）
- 超时

如果备用 provider 也失败，则退回规则逻辑，并在日志中标记最终来源。

## 8. 前端设计

本阶段前端无需新增模型选择 UI。前端仅保留现有会议详情页入口与后处理按钮，不感知 provider 细节。

## 9. 数据流

1. 用户触发会议后处理。
2. `meeting_service.py` 调用 `llm_service.py` 生成摘要 / 抽取任务。
3. `llm_service.py` 先尝试 OpenAI-compatible。
4. 若失败，切换 Ollama。
5. 若仍失败，返回规则版结果。
6. `meeting_service.py` 继续保存结果并记录版本来源。

## 10. 测试策略

### 后端

- 主 provider 正常时命中主 provider
- 主 provider 失败时切到 Ollama
- 主备都失败时回退规则版
- 配置缺失时跳过备用 provider
- `meeting_service.py` 的调用链不变

### 文档/配置

- README 与后端文档补充新增环境变量
- 提供主备 provider 的最小配置示例

## 11. 文件落点

### Backend

- Modify: `backend/app/core/config.py`
- Modify: `backend/app/services/llm_service.py`
- Modify: `backend/app/services/meeting_service.py`（如需记录来源版本）
- Modify: `backend/tests/test_api.py` 或新增服务测试

### Docs

- Modify: `README.md`
- Modify: `backend/README.md`
- Modify: `docs/backend-api.md`（如需补充说明）
