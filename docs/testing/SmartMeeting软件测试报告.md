# SmartMeeting 软件测试报告

## 1. 测试报告说明

- 项目名称：SmartMeeting 智能会议与任务管理系统
- 报告时间：2026-04-16
- 测试基线：Git Commit `cfd2b82`
- 项目路径：`D:\SmartMeeting`

这份报告是我根据 SmartMeeting 项目当前代码和实际测试结果整理出来的，主要目的是说明这个项目目前完成了哪些测试、测试结果怎么样、还存在哪些问题，以及后面如果要继续修改代码，应该怎么做回归测试。

## 2. 测试依据

本次测试主要依据以下内容进行：

1. `docs/SmartMeeting软件需求规格说明书SRS.md`
2. 项目根目录 `README.md`
3. 后端测试配置与夹具：`backend/pytest.ini`、`backend/tests/conftest.py`
4. 前端测试配置：`frontend/package.json`、`frontend/vitest.config.ts`
5. 自动化测试脚本：`scripts/dev/qa.py`、`scripts/dev/smoke.py`
6. 项目当前已有测试代码：`backend/tests/`、`frontend/src/**/*.test.ts`

另外，在整理报告结构时，我参考了公开的测试文档写法，比如测试报告一般会写清楚测试范围、测试环境、测试结果、缺陷记录和最后结论。但这份报告本身还是以本项目实际测试情况为主，不是套模板写出来的。

## 3. 测试目的

这次测试主要想确认下面几件事：

1. 项目的核心功能是不是能正常使用。
2. 后端接口、服务逻辑、前端 API 调用和状态管理是不是基本稳定。
3. 会议从创建到上传音频、转写、生成摘要和任务、再到导出和分享，这条主流程能不能跑通。
4. 当前代码在类型检查、前端构建和已有自动化测试上是否通过。
5. 把测试中发现的问题记录下来，方便后面继续修改和回归测试。

## 4. 测试范围

测试范围主要按照 SRS 里的功能需求来确定。

### 4.1 本次纳入测试的内容

| 模块 | 主要文件 | 本次测试方式 |
|---|---|---|
| 用户认证 | `backend/app/api/v1/endpoints/auth.py`、`frontend/src/api/auth.ts` | 后端接口测试、前端 API 单测 |
| 用户管理 | `backend/app/api/v1/endpoints/users.py` | 后端接口测试 |
| 会议管理 | `backend/app/api/v1/endpoints/meetings.py`、`backend/app/services/meeting_service.py`、`frontend/src/api/meetings.ts` | 后端接口测试、服务测试、前端 API 单测、smoke |
| 音频上传与转写 | `whisper_service.py`、`faster_whisper_service.py` | 服务测试、接口测试、smoke |
| 会议后处理 | `llm_service.py`、`meeting_service.py` | 回归测试、接口测试、smoke |
| 任务管理 | `tasks.py`、`task_service.py`、`frontend/src/api/tasks.ts` | 服务测试、接口测试、前端 API 单测 |
| 参与者管理 | `participants.py`、`frontend/src/api/participants.ts` | 后端接口测试、前端 API 单测 |
| 团队协作与邀请 | `teams.py`、`team_invitations.py` | 后端接口测试 |
| AI 助手与热词 | `ai.py`、`hotwords.py` 及对应前端 API | 接口测试、服务测试、结构分析 |
| 前端页面与路由 | `frontend/src/views/*.vue`、`frontend/src/router/index.ts` | 页面结构分析、构建验证 |

### 4.2 本次没有充分覆盖的内容

这次测试虽然已经覆盖了项目的主要功能，但还有一些地方覆盖得不够：

1. 前端页面级组件自动化测试比较少。
2. 没有做浏览器兼容性实机测试。
3. 没有做专门的性能压力测试和长时间稳定性测试。
4. 没有重新完整跑一遍 MySQL 迁移验证部署场景。

所以这次报告里的结论，主要还是针对“当前开发环境下的功能测试结果”。

## 5. 测试环境

### 5.1 基本环境

- 操作系统：Windows（win32）
- Python：3.14.0
- Node.js：v24.14.0
- npm：11.9.0
- 后端测试框架：pytest 9.0.2
- 前端测试框架：Vitest 3.2.4

### 5.2 后端测试环境

后端测试使用的是 `backend/tests/conftest.py` 里配置的测试环境，主要特点是：

1. 数据库使用 SQLite 内存库。
2. 通过依赖覆盖把测试数据库注入到 FastAPI 应用里。
3. 管理员和普通成员身份通过测试夹具模拟。
4. 外部依赖（例如 LLM、Whisper、MySQL）尽量使用 mock 或 fallback。

这样做的好处是测试执行比较稳定，也方便反复跑。

### 5.3 前端测试环境

前端测试配置主要来自以下文件：

- `frontend/package.json`
- `frontend/vitest.config.ts`

其中：

- `npm --prefix frontend run test` 用来跑 Vitest
- `npm --prefix frontend run test:coverage` 用来检查覆盖率
- 覆盖率阈值设置为 80%

### 5.4 环境差异说明

需要说明的是，这次测试环境和真实运行环境并不是完全一样的：

1. 后端测试用的是 SQLite，不是 MySQL。
2. AI / Whisper 相关流程优先验证 fallback 和接口行为，不完全等同于真实外部服务调用。
3. 前端没有做真实浏览器自动化测试。

因此，这次测试更适合说明“当前代码功能基本可用”，但不能直接说明“所有生产环境问题都已经验证完毕”。

## 6. 测试方法与测试类型

这次测试没有单独写很复杂的测试计划，而是结合项目现有自动化测试、SRS 功能点和关键使用流程来执行。

### 6.1 本次使用的测试思路

主要用了下面几种比较常见的方法：

1. **按功能流程测试**：比如会议从创建到分享这一整条流程。
2. **按模块测试**：把认证、会议、任务、参与者等模块分别检查。
3. **边界和异常情况检查**：例如权限不足、参数错误、资源不存在、状态流转不合法等。
4. **风险优先**：优先看会议后处理、任务流转、分享与导出这些更关键的功能。

### 6.2 测试类型

| 测试类型 | 是否执行 | 说明 |
|---|---|---|
| 单元测试 | 是 | 后端 pytest、前端 Vitest |
| 模块测试 | 是 | 按服务、接口、Store、API 分模块验证 |
| 集成测试 | 是 | FastAPI + 测试数据库 + 依赖覆盖，外加 smoke 主流程 |
| 系统测试 | 部分执行 | 主要通过关键业务链路和构建验证来完成 |
| 性能测试 | 有限执行 | 只记录了构建体积和部分执行时间，没有做压测 |
| 兼容性测试 | 有限执行 | 没有做多浏览器实测 |

## 7. 现有测试基础情况

### 7.1 后端测试情况

后端目前共有 28 个测试文件，共 161 个测试用例。

比较有代表性的文件如下：

| 文件 | 用例数 | 覆盖内容 |
|---|---:|---|
| `backend/tests/test_api.py` | 51 | 用户、会议、任务、参与人、转写、后处理、导出、分享 |
| `backend/tests/test_meeting_postprocess_regression.py` | 16 | 摘要生成、任务提取、LLM 回退、文本清洗 |
| `backend/tests/test_task_service.py` | 8 | 筛选、排序、分页、状态流转、提醒时间校验 |
| `backend/tests/test_task_assignee_permission.py` | 8 | 任务指派权限边界 |
| `backend/tests/test_teams_api.py` | 7 | 团队创建、加入、删除 |
| `backend/tests/test_meeting_service.py` | 6 | 会议服务逻辑、分享逻辑 |
| `backend/tests/test_team_invitations_api.py` | 6 | 团队邀请、接受、拒绝、幂等 |
| `backend/tests/test_auth_api.py` | 4 | 登录、鉴权、审计日志 |

从这些测试来看，后端测试覆盖得相对比较完整，特别是接口、权限、错误码和业务规则这几部分。

### 7.2 前端测试情况

前端目前共有 13 个测试文件，共 43 个测试用例。

主要集中在 API 封装、工具函数和少量 Store：

| 文件 | 用例数 | 覆盖内容 |
|---|---:|---|
| `frontend/src/api/meetings.test.ts` | 12 | 会议列表、创建、删除、导出、共享、转写、后处理 |
| `frontend/src/api/client.test.ts` | 5 | 错误处理、token 注入 |
| `frontend/src/api/tasks.test.ts` | 4 | 任务过滤、状态更新、日期序列化 |
| `frontend/src/api/participants.test.ts` | 4 | 参与人 CRUD |
| `frontend/src/api/auth.test.ts` | 2 | 登录与当前用户 |
| `frontend/src/api/ai.test.ts` | 2 | AI 建议字段兼容 |
| `frontend/src/stores/authStore.test.ts` | 2 | token 持久化 |
| `frontend/src/stores/meetingStore.test.ts` | 1 | 转写追加 |

前端测试的问题也比较明显：API 层测得比较多，但页面层和交互层还是不够。

### 7.3 质量门禁与冒烟测试脚本

项目里还有两个比较重要的脚本：

1. `scripts/dev/qa.py`
   - 串行执行后端测试、前端测试、前端类型检查和构建。

2. `scripts/dev/smoke.py`
   - 跑 7 个关键流程用例：
     - 创建会议
     - 上传音频
     - 转写音频
     - 会议后处理
     - 任务状态流转
     - 会议导出
     - 会议分享

这两个脚本对这次测试报告帮助很大，因为它们能比较直接地反映项目当前质量状态。

## 8. 测试执行情况

下面这些结果都是我这次实际执行命令得到的，不是只看历史文档整理出来的。

### 8.1 后端测试

执行命令：

```bash
python -m pytest backend/tests -v --tb=short
```

执行结果：

- 测试用例数：161
- 通过：161
- 失败：0
- 总耗时：51.20s

说明：后端当前自动化测试全部通过。

后端测试里主要验证了这些内容：

1. 用户创建、登录和权限范围控制。
2. 会议的创建、查询、更新、删除、过滤和搜索。
3. 音频上传、转写和会议后处理。
4. 分享会议时摘要要求和幂等性。
5. 任务状态流转、提醒时间和权限限制。
6. 团队邀请、会议访问权限、任务访问权限。

### 8.2 后端测试中的告警

这次后端测试虽然通过了，但出现了 67 条 warning，主要有三类：

| 类别 | 说明 | 是否影响本次通过 |
|---|---|---|
| 弃用警告 | `asyncio.iscoroutinefunction` 未来版本会移除 | 否 |
| 弃用警告 | `datetime.utcnow()` 用法即将过时 | 否 |
| 运行提示 | CPU 环境下 Whisper 使用 FP32 | 否 |

这些问题不影响这次测试通过，但说明项目后面如果继续升级 Python 版本，可能还要再做兼容处理。

### 8.3 前端测试

执行命令：

```bash
npm --prefix frontend run test
```

执行结果：

- 测试文件数：13
- 测试用例数：43
- 通过：43
- 失败：0
- 总耗时：1.98s

说明：前端已有单元测试全部通过。

### 8.4 前端覆盖率测试

执行命令：

```bash
npm --prefix frontend run test:coverage
```

执行结果：

| 文件 | Statements | Branches | Functions | Lines |
|---|---:|---:|---:|---:|
| `auth.ts` | 100% | 100% | 100% | 100% |
| `client.ts` | 65.24% | 52.17% | 42.85% | 65.24% |
| `meetings.ts` | 62.37% | 92.30% | 60.00% | 62.37% |
| `participants.ts` | 100% | 100% | 100% | 100% |
| `tasks.ts` | 84.78% | 84.61% | 60.00% | 84.78% |
| **总体** | **71.07%** | **74.54%** | **63.15%** | **71.07%** |

项目里设置的阈值是 80%，所以这一步**没有通过**。

失败信息：

- Coverage for lines (71.07%) does not meet global threshold (80%)
- Coverage for functions (63.15%) does not meet global threshold (80%)
- Coverage for statements (71.07%) does not meet global threshold (80%)
- Coverage for branches (74.54%) does not meet global threshold (80%)

这说明前端虽然“测试通过了”，但并不代表测试已经做得很充分，尤其是函数和复杂分支的覆盖还是不够。

### 8.5 集成测试 / 主流程测试

执行命令：

```bash
python scripts/dev/smoke.py
```

执行结果：

- 测试项：7
- 通过：7
- 失败：0
- 总耗时：64.92s

这个脚本验证的是系统最关键的一条业务流程：

1. 创建会议
2. 上传音频
3. 转写音频
4. 生成摘要和任务
5. 任务状态流转
6. 导出会议
7. 会议分享

这一部分全部通过，说明项目的核心主流程目前是能跑通的。

### 8.6 类型检查和前端构建

执行命令：

```bash
npm --prefix frontend run typecheck
npm --prefix frontend run build
```

执行结果：

- `vue-tsc --noEmit`：通过
- `vite build`：通过
- 构建告警：主包 `assets/index-39TZHCf0.js` 大小为 1016.29 kB，超过 500 kB 告警阈值

说明：

1. 当前前端代码没有类型错误。
2. 项目可以正常构建出生产版本。
3. 但是前端主包体积偏大，后面还有优化空间。

## 9. 代表性测试用例整理

为了让报告和需求对应得更清楚，我把一些代表性的测试项整理如下：

| 用例编号 | 对应需求 | 说明 | 证据来源 | 结果 |
|---|---|---|---|---|
| TC-AUTH-01 | FR-AUTH-01 | 用户登录并拿到 token | `backend/tests/test_auth_api.py::test_login_and_me_flow` | 通过 |
| TC-AUTH-02 | FR-AUTH-02 | 通过 token 获取当前用户 | 同上 | 通过 |
| TC-AUTH-03 | FR-AUTH-03 | 未登录访问受保护资源应被拦截 | `backend/tests/test_auth_protected.py` | 通过 |
| TC-USER-01 | FR-USER-01~05 | 用户 CRUD 和权限范围控制 | `backend/tests/test_api.py`、`test_user_scope.py` | 通过 |
| TC-MEET-01 | FR-MEETING-01 | 创建会议 | `test_api.py::test_meeting_crud_flow` | 通过 |
| TC-MEET-02 | FR-MEETING-02~04 | 会议列表、详情、更新、过滤分页 | `test_api.py`、`test_meeting_search.py` | 通过 |
| TC-MEET-03 | FR-MEETING-06 | 分享会议需要摘要且具备幂等性 | `test_meeting_service.py`、`test_api.py::test_meeting_share_is_idempotent` | 通过 |
| TC-ASR-01 | FR-ASR-01 | 音频上传到会议 | `test_api.py::test_audio_upload_for_meeting` | 通过 |
| TC-ASR-02 | FR-ASR-02 | 上传后可以转写并生成记录 | `test_api.py::test_transcribe_latest_audio_generates_transcript` | 通过 |
| TC-POST-01 | FR-POST-01 | 生成会议摘要和任务 | `test_api.py::test_meeting_postprocess_generates_summary_and_tasks` | 通过 |
| TC-TASK-01 | FR-TASK-01~04 | 任务筛选、排序、状态流转和时间校验 | `test_task_service.py`、`test_api.py` | 通过 |
| TC-PART-01 | FR-PART-01~04 | 参与者 CRUD 与重复校验 | `test_api.py`、`frontend/src/api/participants.test.ts` | 通过 |
| TC-UI-01 | FR-UI-01 | 登录 API 和路由守卫逻辑 | `frontend/src/api/auth.test.ts`、`frontend/src/router/index.ts` | 通过 |
| TC-UI-02 | FR-UI-03~05 | 会议和任务 API 的参数处理与错误处理 | `frontend/src/api/meetings.test.ts`、`tasks.test.ts`、`client.test.ts` | 通过 |
| TC-QG-01 | 工程质量门禁 | 前端覆盖率应达到 80% | `npm --prefix frontend run test:coverage` | 不通过 |

## 10. 测试中发现的问题

### 10.1 缺陷分级

这次报告里我把问题简单分成四级：

- **P1**：严重问题，核心功能不能用
- **P2**：重要问题，主流程能用，但质量上有明显缺陷
- **P3**：一般问题，不影响主流程，但会影响维护、兼容性或性能
- **P4**：轻微问题，属于优化项或说明项

### 10.2 本次发现的主要问题

| 编号 | 级别 | 问题 | 证据 | 说明 |
|---|---|---|---|---|
| BUG-01 | P2 | 前端覆盖率没有达到 80% | `npm --prefix frontend run test:coverage` 失败 | 说明前端测试做得还不够全面 |
| BUG-02 | P3 | 前端主包体积偏大 | `vite build` 输出大包告警 | 可能影响首屏加载速度 |
| BUG-03 | P3 | Python 3.14 下有依赖弃用警告 | pytest 输出警告信息 | 目前能运行，但以后升级可能有问题 |
| BUG-04 | P4 | 缺少浏览器兼容性实测 | 当前没有 Playwright 或多浏览器回归记录 | 兼容性结论还不够充分 |
| BUG-05 | P4 | 历史文档里的测试数字和现在不一致 | `README.md` 里仍有旧测试统计 | 后面整理材料时容易混淆 |

## 11. 测试结果分析

### 11.1 后端部分

从这次结果来看，后端测试做得相对扎实一些。

原因主要有：

1. 后端测试文件比较多，覆盖范围也比较广。
2. 不只是测接口返回值，还测了权限、幂等性、状态流转这些业务规则。
3. 有 `smoke.py` 这样的主流程测试脚本，能把关键功能串起来验证。

所以目前后端的功能稳定性相对更让人放心。

### 11.2 前端部分

前端的问题不是“没有测试”，而是“测试主要集中在 API 层”。

具体来说：

1. API 调用、工具函数这些地方测试还可以。
2. 但是页面交互、组件行为、路由切换这些内容基本没测到。
3. 覆盖率也说明了这个问题：总体没达到项目设定的 80%。

所以前端现在属于“基础功能有测试，但还不够完整”。

### 11.3 对性能和兼容性的看法

这次测试里，我记录了构建体积和执行耗时，也看到了主包体积偏大的问题。

但是严格来说，这次并没有真正做：

- 并发压力测试
- 长时间稳定性测试
- 多浏览器兼容性测试
- 移动端适配专项测试

所以这部分只能写成“有初步结果和风险提示”，不能写得太满。

## 12. 测试结论

根据这次实际测试结果，我认为可以得出下面的结论：

1. 项目的核心功能目前是能正常使用的。
   - 后端 161 个测试全部通过。
   - 系统主流程 7 个关键测试全部通过。
   - 会议、任务、认证、转写、摘要、导出、分享这些主要功能都能正常工作。

2. 项目已经具备课程项目提交和演示的基础。
   - 前端测试通过。
   - 前端类型检查通过。
   - 前端构建通过。

3. 目前还有一些地方没有做到特别完善。
   - 前端覆盖率不足。
   - 浏览器兼容性测试不够。
   - 前端性能还有优化空间。
   - 部分依赖在 Python 3.14 下有弃用警告。

综合来看，我认为：

> SmartMeeting 项目当前版本已经达到了课程项目提交的基本要求，主要功能可以正常运行，核心流程也已经通过测试；不过如果后面还要继续完善，这个项目最需要补的还是前端覆盖率、兼容性测试和前端性能优化。

## 13. 后续回归测试建议

如果后面还要继续修改代码，建议至少再跑一遍下面这些命令：

```bash
python -m pytest backend/tests -v --tb=short
python scripts/dev/smoke.py
npm --prefix frontend run test
npm --prefix frontend run typecheck
npm --prefix frontend run build
npm --prefix frontend run test:coverage
```

如果改动的是不同模块，也可以按情况补充：

1. 改鉴权或权限：重点回归 `test_auth_api.py`、`test_auth_protected.py`、`test_user_scope.py`
2. 改会议或任务流程：重点回归 `test_api.py`、`test_task_service.py`、`smoke.py`
3. 改 AI 或转写：重点回归 `test_meeting_postprocess_regression.py`、`test_whisper_service.py`、`test_faster_whisper.py`
4. 改前端 API 或状态逻辑：重点回归 `frontend/src/api/*.test.ts` 和 `stores/*.test.ts`

## 14. 本次实际执行命令

```bash
python -m pytest backend/tests -v --tb=short
npm --prefix frontend run test
python scripts/dev/smoke.py
npm --prefix frontend run test:coverage
npm --prefix frontend run typecheck
npm --prefix frontend run build
python --version
node --version
npm --version
git rev-parse --short HEAD
```
