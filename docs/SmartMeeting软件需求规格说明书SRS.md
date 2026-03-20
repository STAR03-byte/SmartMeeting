# SmartMeeting 智能会议系统 软件需求规格说明书（SRS）

**文档版本**：V1.0

**编制日期**：2026年03月20日

**编制人**：张航星

**项目角色**：全流程独立负责人

**学号**：202312301035

---

## 目录

1. 引言
2. 总体描述
3. 具体需求
4. 其他需求
5. 附录

---

# 1 引言

## 1.1 项目背景

SmartMeeting 是一款 AI 驱动的轻量化智能会议 SaaS 产品，面向 5-50 人规模中小企业、远程协作团队和小型项目组。产品核心目标是替代传统人工会议记录，打通"会议记录→纪要生成→任务拆解→跟进督办"全流程闭环，解决中小团队会议记录效率低、会后执行断层的核心问题。

本项目基于已有的项目立项规划书（V3.0），通过深入调研分析，将项目愿景转化为可落地验证的软件需求，为系统设计、编码与测试提供明确依据。

## 1.2 编写目的

本文档旨在：

1. 将项目立项规划书中的高层需求转化为可验证的软件需求规格
2. 明确各功能模块的输入、处理逻辑、输出与业务规则
3. 定义非功能性需求与接口需求，为系统设计提供完整约束
4. 为后续开发、测试与验收提供统一的评判标准

## 1.3 预期读者

|读者类型|阅读重点|
|--------|--------|
|开发者（本人）|功能需求第3章、接口需求第3.3节、非功能需求第3.2节|
|测试者（本人）|功能需求第3章（含用例）、验收标准|
|指导教师|引言、总体描述、功能需求概览|

## 1.4 参考资料

|资料名称|版本/日期|用途|
|--------|---------|------|
|SmartMeeting 项目立项规划书|V3.0，2026-03-14|需求来源与项目定位|
|FastAPI 官方文档|最新|后端技术参考|
|Vue 3 官方文档|最新|前端技术参考|
|OpenAI Whisper 文档|最新|语音识别技术参考|
|Element Plus 文档|最新|UI 组件参考|

## 1.5 术语定义

|术语|定义|
|----|-----|
|ASR|Automatic Speech Recognition，自动语音识别|
|LLM|Large Language Model，大语言模型|
|MVP|Minimum Viable Product，最小可行产品|
|SRS|Software Requirements Specification，软件需求规格说明书|
|SaaS|Software as a Service，软件即服务|
|CRUD|Create, Read, Update, Delete，增删改查|
|JWT|JSON Web Token，用于用户认证的令牌标准|
|Pinia|Vue 3 官方状态管理库|

---

# 2 总体描述

## 2.1 产品愿景

SmartMeeting 致力于成为中小团队"会议到执行"的轻量化闭环工具。产品愿景是让每一次会议的结论都能自动结构化沉淀为可执行的任务，让团队协作从"开了会"变成"做成了"。

## 2.2 用户特征

|用户角色|典型场景|核心诉求|技术水平|
|--------|--------|--------|--------|
|团队管理者|主持周例会、项目评审|快速把控会议结论，明确任务责任与时限|中等，熟悉 Web 应用|
|项目经理|项目进度会、需求讨论会|拆解会议任务、分配到人、跟踪状态|中等偏高|
|普通参会成员|日常站会、技术讨论|回顾会议重点，知晓个人任务|一般|

## 2.3 运行环境

### 2.3.1 客户端环境

|环境项|最低要求|推荐配置|
|------|--------|---------|
|操作系统|Windows 10 / macOS 10.15 / Ubuntu 20.04|Windows 11 / macOS 12+|
|浏览器|Chrome 90+ / Firefox 90+ / Edge 90+|Chrome 最新版|
|网络|可访问互联网|稳定宽带连接|
|屏幕分辨率|1280×720|1920×1080|

### 2.3.2 服务端环境

|环境项|最低要求|推荐配置|
|------|--------|---------|
|操作系统|Ubuntu 22.04 / Windows Server|Ubuntu 22.04 LTS|
|Python|3.12+|3.12|
|Node.js|22+|22 LTS|
|MySQL|8.0+|8.0|
|Docker|24.0+|最新版|
|内存|2GB|4GB+|
|磁盘|10GB|20GB+（含音频存储）|

### 2.3.3 AI 服务依赖

|服务|配置方式|默认行为|
|----|--------|---------|
|Whisper 语音识别|本地安装 openai-whisper + ffmpeg|未安装时使用 mock ASR 回退|
|LLM 大语言模型|配置 LLM_API_KEY 环境变量|未配置时使用规则回退生成摘要与任务|

## 2.4 主要约束

1. **开发约束**：单人独立完成全流程，6 周内交付 MVP
2. **成本约束**：AI 接口调用成本需可控，月度总成本不超过 ¥4100
3. **技术约束**：前端使用 Vue 3 + TypeScript + Element Plus，后端使用 FastAPI + MySQL
4. **安全约束**：用户密码不可明文存储，接口认证使用 JWT，敏感配置通过环境变量管理
5. **兼容性约束**：需兼容主流现代浏览器，响应式适配桌面端

## 2.5 假设

1. 用户拥有基本的 Web 应用操作能力
2. 用户的音频文件为常见格式（WAV、MP3、M4A 等）
3. 服务器可访问互联网以调用 AI 服务（或已配置本地模型）
4. MySQL 数据库已正确部署并可连接

---

# 3 具体需求

## 3.1 功能需求

### 3.1.1 用户认证模块（FR-AUTH）

#### 3.1.1.1 用户登录（FR-AUTH-01）

|项目|描述|
|----|-----|
|功能描述|用户通过用户名和密码登录系统，获取认证令牌|
|输入|用户名（字符串）、密码（字符串）|
|处理逻辑|1. 验证用户名是否存在<br>2. 验证密码是否正确（使用 pbkdf2_sha256 哈希比对）<br>3. 生成 JWT access_token（有效期 24 小时）|
|输出|`{access_token: string, token_type: "bearer"}`|
|业务规则|- 用户名唯一<br>- 连续登录失败不锁定（MVP 阶段）<br>- token 过期后需重新登录|
|异常处理|用户名不存在 → 返回 401 "Incorrect username or password"<br>密码错误 → 返回 401 "Incorrect username or password"|

#### 3.1.1.2 获取当前用户（FR-AUTH-02）

|项目|描述|
|----|-----|
|功能描述|通过 token 获取当前登录用户信息|
|输入|Authorization: Bearer {token}|
|处理逻辑|1. 验证 token 有效性与过期时间<br>2. 从 token 中提取用户 ID<br>3. 查询用户信息并返回|
|输出|用户对象（id, username, email, full_name, role, is_active, created_at, updated_at）|
|异常处理|token 无效 → 返回 401|

#### 3.1.1.3 路由鉴权（FR-AUTH-03）

|项目|描述|
|----|-----|
|功能描述|业务接口通过 JWT 验证用户身份|
|依赖|FR-AUTH-01|
|保护范围|/api/v1/meetings/*, /api/v1/tasks/*, /api/v1/transcripts/*, /api/v1/participants/*|
|不保护范围|/api/v1/auth/*, /api/v1/users（创建）, /health|

---

### 3.1.2 用户管理模块（FR-USER）

#### 3.1.2.1 创建用户（FR-USER-01）

|项目|描述|
|----|-----|
|功能描述|创建新用户账号|
|输入|username, email, password_hash, full_name, role（admin/member）|
|处理逻辑|1. 验证 email 格式（EmailStr）<br>2. 检查 username 唯一性<br>3. 存储密码哈希值|
|输出|用户对象|
|业务规则|- email 必须为合法邮箱格式<br>- username 全局唯一<br>- role 仅允许 admin 或 member|
|异常处理|email 格式错误 → 422<br>username 重复 → 500|

#### 3.1.2.2 查询用户列表（FR-USER-02）

|项目|描述|
|----|-----|
|功能描述|获取所有用户列表|
|输入|无|
|输出|用户对象数组（按 ID 倒序排列）|

#### 3.1.2.3 查询用户详情（FR-USER-03）

|项目|描述|
|----|-----|
|功能描述|按 ID 获取单个用户信息|
|输入|user_id（路径参数）|
|输出|用户对象|
|异常处理|用户不存在 → 404|

#### 3.1.2.4 更新用户（FR-USER-04）

|项目|描述|
|----|-----|
|功能描述|更新用户信息|
|输入|user_id, 待更新字段（email, full_name, role, is_active）|
|处理逻辑|仅更新传入的字段，不影响其他字段|

#### 3.1.2.5 删除用户（FR-USER-05）

|项目|描述|
|----|-----|
|功能描述|删除指定用户|
|输入|user_id|
|输出|204 No Content|
|业务规则|删除用户不级联删除其创建的会议和任务（MVP 阶段）|

---

### 3.1.3 会议管理模块（FR-MEETING）

#### 3.1.3.1 创建会议（FR-MEETING-01）

|项目|描述|
|----|-----|
|功能描述|创建新会议|
|输入|title（必填）, description, organizer_id（必填）, scheduled_start_at, scheduled_end_at, location|
|处理逻辑|1. 验证 organizer_id 对应的用户存在<br>2. 若提供时间范围，验证开始时间 < 结束时间<br>3. 设置默认状态为 planned|
|输出|会议对象|
|业务规则|- title 长度 1-200 字符<br>- 状态初始值为 planned<br>- organizer_id 必须指向已存在的用户|
|异常处理|organizer_id 不存在 → 404 "Organizer not found"<br>时间范围非法 → 422|

#### 3.1.3.2 查询会议列表（FR-MEETING-02）

|项目|描述|
|----|-----|
|功能描述|获取会议列表，支持筛选和分页|
|输入|status（可选）, organizer_id（可选）, limit（可选，默认 20）, offset（可选，默认 0）|
|处理逻辑|1. 按条件过滤会议<br>2. 按 scheduled_start_at 降序排列<br>3. 返回带分页信息的结果|
|输出|`{data: 会议对象[], total: int, limit: int, offset: int}`|
|业务规则|- 筛选条件可组合使用<br>- limit 上限为 100|

#### 3.1.3.3 查询会议详情（FR-MEETING-03）

|项目|描述|
|----|-----|
|功能描述|获取单个会议完整信息（含组织者对象）|
|输入|meeting_id（路径参数）|
|输出|会议详情对象（含 organizer 嵌套对象）|
|异常处理|会议不存在 → 404|

#### 3.1.3.4 更新会议（FR-MEETING-04）

|项目|描述|
|----|-----|
|功能描述|更新会议信息|
|输入|meeting_id, 待更新字段|
|处理逻辑|1. 检查会议是否存在<br>2. 若更新时间范围，验证合法性<br>3. 状态流转验证（planned → ongoing → done/cancelled）|
|业务规则|- scheduled_start_at < scheduled_end_at<br>- actual_start_at < actual_end_at<br>- 状态只能向前流转（planned → ongoing → done/cancelled）|
|异常处理|时间范围非法 → 422<br>状态值非法 → 422|

#### 3.1.3.5 删除会议（FR-MEETING-05）

|项目|描述|
|----|-----|
|功能描述|删除指定会议及其关联数据|
|输入|meeting_id|
|输出|204 No Content|

#### 3.1.3.6 分享会议（FR-MEETING-06）

|项目|描述|
|----|-----|
|功能描述|生成会议分享链接|
|输入|meeting_id|
|处理逻辑|1. 生成唯一 share_token<br>2. 记录 shared_at 时间戳|
|输出|`{share_token: string, shared_at: datetime}`|
|业务规则|- 每个会议只有一个 share_token（重复调用返回已有 token）|

#### 3.1.3.7 取消分享（FR-MEETING-07）

|项目|描述|
|----|-----|
|功能描述|取消会议分享|
|输入|meeting_id|
|处理逻辑|清除 share_token 和 shared_at|

---

### 3.1.4 音频上传与语音识别模块（FR-ASR）

#### 3.1.4.1 上传音频（FR-ASR-01）

|项目|描述|
|----|-----|
|功能描述|为指定会议上传音频文件|
|输入|meeting_id, 音频文件（multipart/form-data）|
|处理逻辑|1. 验证会议存在<br>2. 生成唯一文件名<br>3. 保存至 storage/audio/{meeting_id}/ 目录<br>4. 记录文件元数据（文件名、路径、大小、类型）|
|输出|音频记录对象（id, meeting_id, filename, storage_path, content_type, size_bytes, uploaded_at）|
|业务规则|- 支持常见音频格式（WAV, MP3, M4A, FLAC 等）<br>- 单次会议可上传多个音频文件|

#### 3.1.4.2 语音转写（FR-ASR-02）

|项目|描述|
|----|-----|
|功能描述|对最新上传的音频执行语音识别并生成转写片段|
|输入|meeting_id|
|处理逻辑|**真实模式**（Whisper 已安装）：<br>1. 加载 Whisper 模型<br>2. 调用 model.transcribe() 获取分段结果<br>3. 按分段写入 meeting_transcripts 表<br><br>**Mock 模式**（Whisper 未安装）：<br>1. 随机选择 3 套转写模板之一<br>2. 生成 5 个带时间戳的转写片段<br>3. source 标记为 "manual"|
|输出|第一个转写片段对象|
|业务规则|- 优先使用 Whisper 真实转写<br>- Whisper 不可用时自动回退到 mock ASR<br>- 转写片段自动分配递增的 segment_index|
|异常处理|无音频文件 → 400 "No audio found for meeting"|

#### 3.1.4.3 查询转写记录（FR-ASR-03）

|项目|描述|
|----|-----|
|功能描述|获取指定会议的所有转写片段|
|输入|meeting_id（查询参数）|
|输出|转写片段数组（按 segment_index 升序排列）|
|输出字段|id, meeting_id, speaker_user_id, speaker_name, segment_index, start_time_sec, end_time_sec, language_code, source, content|

---

### 3.1.5 会议后处理模块（FR-POST）

#### 3.1.5.1 生成摘要与任务（FR-POST-01）

|项目|描述|
|----|-----|
|功能描述|基于转写内容生成会议摘要并提取任务|
|输入|meeting_id|
|处理逻辑|1. 检查会议是否存在转写记录<br>2. **摘要生成**：<br>   - LLM 模式：调用 LLM API 生成结构化摘要，version = "llm-summary-v1"<br>   - 规则模式：拼接转写内容生成摘要，version = "rule-v1"<br>3. **任务提取**：<br>   - LLM 模式：调用 LLM API 提取 JSON 格式任务列表，version = "llm-task-v1"<br>   - 规则模式：按句号分割生成任务，version = "rule-v1"<br>4. 将摘要写入 meetings.summary，记录 postprocessed_at 和 postprocess_version<br>5. 将提取的任务写入 tasks 表|
|输出|`{meeting_id: int, summary: string, tasks: 任务对象[]}`|
|业务规则|- 无转写记录时返回 400<br>- 幂等：重复调用不重复生成（除非 force_regenerate）<br>- 任务提取自动匹配 assignee（按姓名匹配用户）<br>- 优先级按关键词推断（"紧急"→high，"后续"→low，其余→medium）|
|异常处理|无转写记录 → 400 "No transcripts found for meeting"|

#### 3.1.5.2 强制重新生成（FR-POST-02）

|项目|描述|
|----|-----|
|功能描述|强制重新生成摘要与任务（覆盖已有结果）|
|输入|meeting_id, force_regenerate: true|
|处理逻辑|删除已有关联任务，重新执行 FR-POST-01 流程|
|业务规则|- 仅当 force_regenerate=true 时删除已有任务<br>- 默认行为为幂等（不重复生成）|

---

### 3.1.6 任务管理模块（FR-TASK）

#### 3.1.6.1 查询任务列表（FR-TASK-01）

|项目|描述|
|----|-----|
|功能描述|获取任务列表，支持多条件筛选|
|输入|meeting_id（可选）, assignee_id（可选）, status（可选）, priority（可选）, keyword（可选）, limit, offset|
|处理逻辑|1. 按条件过滤任务<br>2. 返回任务列表，含 is_overdue 和 is_due_soon 标记|
|输出|`{data: 任务对象[], total: int, limit: int, offset: int}`|
|业务规则|- keyword 模糊匹配 title 和 description<br>- is_overdue: due_at < 当前时间 且 status ≠ done<br>- is_due_soon: due_at 在未来 24 小时内 且 status ≠ done|

#### 3.1.6.2 查询任务详情（FR-TASK-02）

|项目|描述|
|----|-----|
|功能描述|获取单个任务详情|
|输入|task_id|
|输出|任务对象（含 meeting 标题、assignee 姓名、reporter 姓名）|
|异常处理|任务不存在 → 404|

#### 3.1.6.3 创建任务（FR-TASK-03）

|项目|描述|
|----|-----|
|功能描述|手动创建新任务|
|输入|meeting_id, title, description, assignee_id, reporter_id, priority, due_at|
|处理逻辑|1. 验证 meeting_id 存在<br>2. 验证 assignee_id 和 reporter_id（若提供）存在<br>3. 创建任务记录|
|输出|任务对象|
|业务规则|- priority 只接受 high/medium/low<br>- status 初始值为 todo<br>- assignee_id 和 reporter_id 为可选|

#### 3.1.6.4 更新任务状态（FR-TASK-04）

|项目|描述|
|----|-----|
|功能描述|更新任务状态（核心流转操作）|
|输入|task_id, status|
|处理逻辑|1. 验证状态流转合法性<br>2. 若状态变为 done，自动设置 completed_at<br>3. 若从 done 变回其他状态，清除 completed_at|
|输出|更新后的任务对象|
|业务规则|- 合法流转：todo → in_progress → done<br>- todo → done（跳过进行中）<br>- done → todo（重新打开）<br>- in_progress → todo（回退）<br>- 其他流转 → 422|
|异常处理|非法状态流转 → 422 "Illegal transition: {from} → {to}"|

#### 3.1.6.5 删除任务（FR-TASK-05）

|项目|描述|
|----|-----|
|功能描述|删除指定任务|
|输入|task_id|
|输出|204 No Content|

---

### 3.1.7 参与者管理模块（FR-PART）

#### 3.1.7.1 添加参与者（FR-PART-01）

|项目|描述|
|----|-----|
|功能描述|为指定会议添加参与者|
|输入|meeting_id, user_id, role（attendee/organizer/note_taker）|
|处理逻辑|1. 验证 meeting_id 和 user_id 存在<br>2. 创建参与记录|
|输出|参与者对象|
|业务规则|- role 仅接受 attendee/organizer/note_taker<br>- 同一会议同一用户只能有一个参与记录|

#### 3.1.7.2 查询参与者列表（FR-PART-02）

|项目|描述|
|----|-----|
|功能描述|获取指定会议的参与者列表|
|输入|meeting_id（查询参数）|
|输出|参与者数组（含 user 嵌套对象）|

#### 3.1.7.3 更新参与者角色（FR-PART-03）

|项目|描述|
|----|-----|
|功能描述|更新参与者的角色|
|输入|participant_id, role|
|输出|更新后的参与者对象|

#### 3.1.7.4 移除参与者（FR-PART-04）

|项目|描述|
|----|-----|
|功能描述|从会议中移除参与者|
|输入|participant_id|
|输出|204 No Content|

---

### 3.1.8 前端页面模块（FR-UI）

#### 3.1.8.1 登录页（FR-UI-01）

|项目|描述|
|----|-----|
|页面路径|/login|
|功能|用户登录表单，输入用户名和密码，提交后跳转到仪表盘|
|前置条件|未登录|
|关联接口|FR-AUTH-01, FR-AUTH-02|

#### 3.1.8.2 仪表盘（FR-UI-02）

|项目|描述|
|----|-----|
|页面路径|/|
|功能|展示会议统计（总数、进行中、计划中、已结束）、近期会议表格、快捷导航|
|前置条件|已登录|
|关联接口|FR-MEETING-02|

#### 3.1.8.3 会议列表页（FR-UI-03）

|项目|描述|
|----|-----|
|页面路径|/meetings|
|功能|会议列表（表格）、状态筛选、关键词搜索、分页、新建会议弹窗、删除会议|
|前置条件|已登录|
|关联接口|FR-MEETING-01, FR-MEETING-02, FR-MEETING-05|

#### 3.1.8.4 会议详情工作台（FR-UI-04）

|项目|描述|
|----|-----|
|页面路径|/meetings/:id|
|功能|会议概览（统计卡片）、音频上传、生成纪要、摘要展示与复制、转写片段列表、任务列表（含状态下拉切换）、新建任务弹窗、刷新按钮|
|前置条件|已登录，会议存在|
|关联接口|FR-MEETING-03, FR-ASR-01, FR-ASR-02, FR-ASR-03, FR-POST-01, FR-TASK-01, FR-TASK-03, FR-TASK-04|

#### 3.1.8.5 任务中心（FR-UI-05）

|项目|描述|
|----|-----|
|页面路径|/tasks|
|功能|任务列表（表格）、状态/优先级筛选、关键词搜索、状态下拉切换、截止时间列、会议链接、逾期/即将到期标签|
|前置条件|已登录|
|关联接口|FR-TASK-01, FR-TASK-04|

#### 3.1.8.6 用户管理页（FR-UI-06）

|项目|描述|
|----|-----|
|页面路径|/users|
|功能|用户列表（表格）、创建用户表单（含密码输入）、角色标签、删除用户|
|前置条件|已登录|
|关联接口|FR-USER-01, FR-USER-02, FR-USER-05|

---

## 3.2 非功能需求

### 3.2.1 性能需求

|需求编号|需求描述|目标值|
|--------|--------|-------|
|NFR-PERF-01|页面首次加载时间（LCP）|≤ 3 秒（宽带环境）|
|NFR-PERF-02|API 接口平均响应时间|≤ 500ms（不含 AI 调用）|
|NFR-PERF-03|30 分钟音频转写完成时间|≤ 5 分钟（Whisper base 模型）|
|NFR-PERF-04|AI 摘要生成完成时间|≤ 30 秒（LLM 调用）|
|NFR-PERF-05|前端构建产物大小|单 chunk ≤ 1MB（gzip 后）|

### 3.2.2 可用性需求

|需求编号|需求描述|目标值|
|--------|--------|-------|
|NFR-AVAIL-01|API 接口可用性|≥ 99.5%（排除计划维护）|
|NFR-AVAIL-02|AI 服务降级能力|Whisper/LLM 不可用时自动回退，不影响核心功能|
|NFR-AVAIL-03|数据库连接失败处理|MySQL 不可用时自动回退到 SQLite（开发环境）|

### 3.2.3 安全性需求

|需求编号|需求描述|实现方式|
|--------|--------|---------|
|NFR-SEC-01|密码安全存储|pbkdf2_sha256 哈希，不存储明文|
|NFR-SEC-02|接口认证|JWT token，有效期 24 小时|
|NFR-SEC-03|敏感配置管理|通过环境变量注入，不硬编码在代码中|
|NFR-SEC-04|SQL 注入防护|使用 SQLAlchemy ORM，不拼接 SQL|
|NFR-SEC-05|CORS 控制|仅允许指定源访问（生产环境需配置）|

### 3.2.4 可维护性需求

|需求编号|需求描述|实现方式|
|--------|--------|---------|
|NFR-MAINT-01|代码规范|后端使用 ruff + black + isort，前端使用 vue-tsc 类型检查|
|NFR-MAINT-02|测试覆盖|后端 pytest 测试（33 项），前端 vitest 测试（7 项）|
|NFR-MAINT-03|CI 自动化|GitHub Actions 自动运行后端测试和前端构建|
|NFR-MAINT-04|文档完整性|README、backend/README、frontend/README、docs/ 全覆盖|

---

## 3.3 接口需求

### 3.3.1 接口规范

- 协议：HTTP/HTTPS
- 风格：RESTful
- 数据格式：JSON（请求体和响应体）
- 认证方式：Bearer JWT（通过 Authorization 请求头传递）
- API 版本前缀：/api/v1/

### 3.3.2 接口一览

|模块|方法|路径|认证|描述|
|----|-----|-----|----|-----|
|认证|POST|/api/v1/auth/login|否|用户登录|
|认证|GET|/api/v1/auth/me|是|获取当前用户|
|用户|POST|/api/v1/users|否|创建用户|
|用户|GET|/api/v1/users|否|查询用户列表|
|用户|GET|/api/v1/users/:id|否|查询用户详情|
|用户|PATCH|/api/v1/users/:id|否|更新用户|
|用户|DELETE|/api/v1/users/:id|否|删除用户|
|会议|POST|/api/v1/meetings|是|创建会议|
|会议|GET|/api/v1/meetings|是|查询会议列表（支持筛选/分页）|
|会议|GET|/api/v1/meetings/:id|是|查询会议详情|
|会议|PATCH|/api/v1/meetings/:id|是|更新会议|
|会议|DELETE|/api/v1/meetings/:id|是|删除会议|
|会议|POST|/api/v1/meetings/:id/share|是|分享会议|
|会议|DELETE|/api/v1/meetings/:id/share|是|取消分享|
|音频|POST|/api/v1/meetings/:id/audio|是|上传音频|
|转写|POST|/api/v1/meetings/:id/audio/transcribe|是|执行语音转写|
|后处理|POST|/api/v1/meetings/:id/postprocess|是|生成摘要与任务|
|转写|GET|/api/v1/transcripts|是|查询转写记录|
|任务|GET|/api/v1/tasks|是|查询任务列表（支持筛选）|
|任务|GET|/api/v1/tasks/:id|是|查询任务详情|
|任务|POST|/api/v1/tasks|是|创建任务|
|任务|PATCH|/api/v1/tasks/:id|是|更新任务状态|
|任务|DELETE|/api/v1/tasks/:id|是|删除任务|
|参与者|POST|/api/v1/participants|是|添加参与者|
|参与者|GET|/api/v1/participants|是|查询参与者列表|
|参与者|PATCH|/api/v1/participants/:id|是|更新参与者|
|参与者|DELETE|/api/v1/participants/:id|是|移除参与者|
|系统|GET|/health|否|健康检查|

### 3.3.3 接口错误码规范

|HTTP 状态码|含义|使用场景|
|-----------|-----|---------|
|200|成功|GET/PATCH 请求成功|
|201|已创建|POST 请求成功创建资源|
|204|无内容|DELETE 请求成功|
|400|请求错误|缺少必要参数、逻辑错误（如无转写记录）|
|401|未认证|token 缺失或无效|
|404|未找到|资源不存在|
|422|验证错误|请求参数格式错误、枚举值非法|
|500|服务器错误|未预期的异常|

错误响应格式：
```json
{
  "detail": "错误描述信息",
  "error_code": "ERROR_CODE_NAME"
}
```

---

# 4 其他需求

## 4.1 数据管理需求

### 4.1.1 数据持久化

|数据类型|存储方式|备份策略|
|--------|--------|---------|
|业务数据（用户/会议/任务等）|MySQL 8.0|定期 mysqldump 或 binlog 备份|
|音频文件|本地文件系统 storage/audio/|备份整个 storage 目录|
|配置信息|.env 文件|不纳入版本控制，手动备份|

### 4.1.2 数据保留策略

- 用户数据：账号删除后保留关联会议和任务（MVP 阶段不级联删除）
- 音频文件：随会议删除而清除
- 转写记录：随会议删除而清除
- 任务数据：独立存在，不随会议删除而清除（MVP 阶段）

### 4.1.3 数据库迁移

- 采用 SQL 脚本驱动的迁移方式（非 alembic）
- 迁移脚本编号执行：001_init_smartmeeting.sql → 006_collaboration_share_fields.sql
- 提供回滚脚本（database/rollback/）
- 种子数据可重复执行（先 DELETE 再 INSERT）

## 4.2 故障处理需求

### 4.2.1 故障检测

|故障类型|检测方式|处理方式|
|--------|--------|---------|
|数据库连接失败|启动时执行 SELECT 1|开发环境自动回退到 SQLite；生产环境报错退出|
|Whisper 不可用|import whisper 失败或 ffmpeg 不存在|自动回退到 mock ASR，记录日志|
|LLM 不可用|API key 未配置或调用超时|自动回退到规则摘要生成，记录日志|
|音频文件丢失|文件不存在异常|返回 400 错误，提示检查文件|

### 4.2.2 错误日志

- 后端使用 Python logging 模块，日志级别通过 LOG_LEVEL 环境变量配置
- 关键操作记录日志：用户登录、音频上传、转写执行、LLM 调用
- 异常堆栈记录到日志文件，便于排查

## 4.3 兼容性需求

### 4.3.1 浏览器兼容性

|浏览器|最低版本|备注|
|------|--------|-----|
|Chrome|90+|推荐使用|
|Firefox|90+|完全兼容|
|Edge|90+|完全兼容|
|Safari|15+|基本兼容（未充分测试）|

### 4.3.2 操作系统兼容性

|操作系统|版本|备注|
|--------|-----|-----|
|Windows|10+|主要开发和测试环境|
|macOS|10.15+|兼容，未充分测试|
|Linux|Ubuntu 20.04+|推荐部署环境|

### 4.3.3 屏幕分辨率

- 最低支持：1280×720
- 推荐使用：1920×1080
- 响应式断点：900px（小屏下网格布局切换为单列）

## 4.4 部署需求

### 4.4.1 Docker 部署

系统提供 docker-compose.yml 实现一键部署，包含三个服务：

|服务|镜像|端口|依赖|
|----|-----|-----|-----|
|db|mysql:8.0|3307→3306|无|
|backend|自构建（python:3.12-slim）|8000|db (healthy)|
|frontend|自构建（node:22-alpine + nginx:1.27-alpine）|5174→5173|backend|

### 4.4.2 环境变量配置

关键环境变量：

|变量名|默认值|说明|
|------|------|-----|
|DB_HOST|127.0.0.1|数据库主机|
|DB_PORT|3306|数据库端口|
|DB_USER|root|数据库用户名|
|DB_PASSWORD|-|数据库密码|
|DB_NAME|smartmeeting|数据库名|
|JWT_SECRET_KEY|change-me|JWT 签名密钥（生产环境必须修改）|
|LLM_API_KEY|-|LLM API 密钥（可选）|
|LLM_MODEL|gpt-4o-mini|LLM 模型名称|
|WHISPER_MODEL|base|Whisper 模型大小|
|WHISPER_DEVICE|cpu|Whisper 运行设备|

---

# 5 附录

## 5.1 数据库实体关系

|实体|核心字段|关联关系|
|----|--------|---------|
|User|id, username, email, password_hash, role|← Meeting.organizer_id, ← Task.assignee_id, ← Participant.user_id|
|Meeting|id, title, organizer_id, status, summary|→ User, ← MeetingAudio, ← MeetingTranscript, ← Task, ← Participant|
|MeetingAudio|id, meeting_id, filename, storage_path|→ Meeting|
|MeetingTranscript|id, meeting_id, speaker_user_id, content|→ Meeting, → User|
|Task|id, meeting_id, assignee_id, title, status, priority, due_at|→ Meeting, → User|
|Participant|id, meeting_id, user_id, role|→ Meeting, → User|
|AuditLog|id, entity_type, entity_id, action|独立日志实体|

## 5.2 用例图描述

### 核心用户用例

```
参与者：团队管理者、项目经理、普通参会成员

用例 1：登录系统
  前置：用户拥有账号
  主流程：输入用户名密码 → 系统验证 → 跳转仪表盘

用例 2：上传会议音频
  前置：已登录，已创建会议
  主流程：选择音频文件 → 上传 → 系统保存 → 可触发转写

用例 3：生成会议纪要
  前置：会议有转写记录
  主流程：点击"生成纪要与任务" → 系统调用 AI → 展示摘要与任务

用例 4：管理任务
  前置：已登录
  主流程：查看任务列表 → 筛选/搜索 → 切换状态 → 完成任务

用例 5：创建会议
  前置：已登录
  主流程：填写会议信息 → 提交 → 会议创建成功
```

## 5.3 需求优先级总览

|优先级|模块|功能点|
|------|-----|-------|
|P0|用户认证|登录、token 验证|
|P0|会议管理|创建、列表、详情、更新、删除|
|P0|音频转写|上传音频、语音转写|
|P0|会议后处理|AI 摘要生成、任务提取|
|P0|任务管理|列表、状态流转|
|P1|用户管理|创建、列表、删除|
|P1|参与者管理|添加、查询、删除|
|P1|前端工作台|仪表盘、会议列表、会议详情、任务中心|
|P2|会议分享|生成分享链接、取消分享|
|P2|工程化|Docker 部署、CI/CD、测试、文档|

## 5.4 需求可行性分析

|需求|可行性|理由|
|----|------|-----|
|语音转写|可行|Whisper 开源模型成熟，支持本地部署；mock 回退保证基本可用|
|AI 摘要生成|可行|LLM API 成熟（OpenAI/通义千问等），规则回退保证降级可用|
|任务提取|可行|LLM 结构化输出能力强，规则模式可按关键词提取|
|任务状态管理|有限|MVP 仅支持线性流转（todo→in_progress→done），后续可扩展|
|会议分享|可行|token 机制简单可靠，无需复杂权限系统|

## 5.5 文档变更记录

|版本|日期|变更人|变更说明|
|------|------|------|---------|
|V1.0|2026-03-20|张航星|初始版本，基于已实现项目编写完整 SRS|
