# SmartMeeting 智能会议与任务管理系统

## 软件详细设计说明书

---

**文档版本**：V1.0  
**编写日期**：2026年4月6日  
**编写人**：开发团队  
**审核人**：技术负责人  
**适用系统**：SmartMeeting v0.1.0

---

## 目录

1. [文档概述](#1-文档概述)
2. [系统概要设计](#2-系统概要设计)
3. [系统详细设计](#3-系统详细设计)
4. [非功能性设计](#4-非功能性设计)
5. [部署架构](#5-部署架构)
6. [附录](#6-附录)

---

## 1. 文档概述

### 1.1 编写目的

本文档为 SmartMeeting 智能会议与任务管理系统的详细设计说明书，旨在：
- 明确系统技术架构与模块划分
- 规范数据库设计与接口定义
- 指导开发人员进行编码实现
- 为系统测试、部署、维护提供技术依据

### 1.2 项目背景

SmartMeeting 是一款面向企业与团队的智能会议管理系统，核心能力包括：
- 会议录制与音频转写（基于 Whisper）
- AI 智能摘要与任务自动提取（基于 LLM）
- 任务全生命周期管理
- 团队协作与权限管控

### 1.3 术语定义

| 术语 | 定义 |
|------|------|
| JWT | JSON Web Token，用于用户身份认证的令牌机制 |
| ORM | Object-Relational Mapping，对象关系映射 |
| ASR | Automatic Speech Recognition，自动语音识别 |
| LLM | Large Language Model，大语言模型 |
| REST | Representational State Transfer，表征状态转移架构风格 |

### 1.4 参考资料

- FastAPI 官方文档 (https://fastapi.tiangolo.com/)
- Vue 3 组合式 API 指南 (https://vuejs.org/)
- SQLAlchemy 2.0 文档 (https://docs.sqlalchemy.org/)
- OpenAI API 参考 (https://platform.openai.com/docs/)

---

## 2. 系统概要设计

### 2.1 系统架构设计

SmartMeeting 采用**前后端分离**的三层架构：

```
┌─────────────────────────────────────────────────────────────┐
│                        表现层 (Presentation)                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Vue 3 + TypeScript + Pinia + Element Plus          │   │
│  │  - Dashboard、Meeting、Task、Team、User 等视图       │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │ HTTPS / RESTful API
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        业务层 (Business)                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  FastAPI + SQLAlchemy 2.0 + Pydantic v2             │   │
│  │  ├─ API 端点 (Endpoints)                           │   │
│  │  ├─ 业务服务 (Services)                            │   │
│  │  ├─ 数据模型 (Models)                              │   │
│  │  └─ 数据校验 (Schemas)                             │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │ SQL / Connection Pool
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        数据层 (Data)                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  MySQL 8.0 + Redis (可选缓存)                        │   │
│  │  - 业务数据持久化                                    │   │
│  │  - 文件存储 (音频文件本地/对象存储)                   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**架构设计原则**：
1. **分层解耦**：表现层、业务层、数据层职责清晰，层间通过接口交互
2. **依赖注入**：数据库会话、认证信息等通过 FastAPI Depends 注入
3. **服务层厚、控制层薄**：业务逻辑集中在 services 目录，endpoints 仅做 HTTP 协议转换

### 2.2 技术架构选型

#### 2.2.1 后端技术栈

| 技术组件 | 版本 | 用途 |
|---------|------|------|
| Python | 3.10+ | 运行时环境 |
| FastAPI | 0.135.1 | Web 框架，提供异步高性能 API |
| Uvicorn | 0.41.0 | ASGI 服务器 |
| SQLAlchemy | 2.0.48 | ORM 框架，数据库操作 |
| Pydantic | 2.12.5 | 数据校验与序列化 |
| PyMySQL | 1.1.2 | MySQL 数据库驱动 |
| python-jose | 3.3.0 | JWT 认证实现 |
| passlib | 1.7.4 | 密码哈希处理 |
| OpenAI-Whisper | 20240930 | 语音识别 (ASR) |
| faster-whisper | 1.0.0 | 加速版 Whisper |
| opencc-python | 0.1.7 | 简繁体转换 |
| pytest | 9.0.2 | 测试框架 |

#### 2.2.2 前端技术栈

| 技术组件 | 版本 | 用途 |
|---------|------|------|
| Vue | 3.5.21 | 渐进式前端框架 |
| TypeScript | 5.9.2 | 类型安全的 JavaScript 超集 |
| Vite | 7.1.3 | 构建工具，支持热更新 |
| Pinia | 3.0.3 | 状态管理 |
| Vue Router | 4.5.1 | 前端路由 |
| Element Plus | 2.11.2 | UI 组件库 |
| Vue I18n | 11.3.0 | 国际化支持 |
| Axios | 1.11.0 | HTTP 客户端 |
| Zod | 3.23.8 | 运行时类型校验 |
| UnoCSS | 66.6.7 | 原子化 CSS |

#### 2.2.3 数据库与基础设施

| 组件 | 版本 | 用途 |
|------|------|------|
| MySQL | 8.0 | 关系型数据库，业务数据持久化 |
| Docker | - | 容器化部署 |
| Docker Compose | - | 多容器编排 |

### 2.3 系统功能模块结构

```
SmartMeeting 系统
│
├── 1. 用户认证模块 (Auth Module)
│   ├── 用户注册 (/api/v1/register)
│   ├── 用户登录 (/api/v1/auth/login)
│   ├── JWT 令牌颁发与验证
│   └── 角色权限控制 (admin/member)
│
├── 2. 会议管理模块 (Meeting Module)
│   ├── 会议 CRUD 操作
│   ├── 会议状态流转 (planned/ongoing/done/cancelled)
│   ├── 音频上传与存储
│   ├── 会议分享 (分享链接生成)
│   └── 会议纪要 AI 生成
│
├── 3. 转写管理模块 (Transcript Module)
│   ├── Whisper 语音转写
│   ├── 转写文本分段存储
│   ├── 发言人识别与标注
│   └── 转写内容查看与编辑
│
├── 4. 任务管理模块 (Task Module)
│   ├── 任务自动提取 (从转写文本)
│   ├── 任务 CRUD 操作
│   ├── 任务状态流转 (todo/in_progress/done)
│   ├── 优先级管理 (high/medium/low)
│   └── 任务提醒与追踪
│
├── 5. 团队管理模块 (Team Module)
│   ├── 团队创建与配置
│   ├── 团队成员管理
│   ├── 团队邀请 (邮件/链接)
│   ├── 公开/私有团队设置
│   └── 团队会议关联
│
├── 6. AI 处理模块 (AI Module)
│   ├── Whisper ASR 服务
│   ├── LLM 摘要生成 (OpenAI/Ollama)
│   ├── 任务智能提取
│   └── 规则回退机制
│
└── 7. 系统管理模块 (System Module)
    ├── 审计日志记录
    ├── 热词管理
    └── 系统配置
```

### 2.4 模块间接口设计

#### 2.4.1 内部服务调用关系

```
┌─────────────────┐
│  MeetingService │
└────────┬────────┘
         │ 依赖
         ▼
┌─────────────────┐     ┌─────────────────┐
│   TaskService   │◄────│  LLMService     │
└────────┬────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│  UserService    │◄────│  AuthService    │
└─────────────────┘     └─────────────────┘
```

#### 2.4.2 外部集成接口

| 外部服务 | 接口类型 | 用途 |
|---------|---------|------|
| OpenAI API | HTTP REST | LLM 摘要与任务提取 |
| Ollama (本地) | HTTP REST | 本地 LLM 服务调用 |
| Whisper (本地) | Python API | 语音识别处理 |

---

## 3. 系统详细设计

### 3.1 数据库设计

#### 3.1.1 E-R 图逻辑模型

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│    users    │       │   meetings  │       │    tasks    │
├─────────────┤       ├─────────────┤       ├─────────────┤
│ PK id       │◄──────┤ PK id       │◄──────┤ PK id       │
│    username │       │ FK organizer│       │ FK meeting  │
│    email    │       │    title    │       │ FK assignee │
│    role     │       │    status   │       │    title    │
└─────────────┘       │    summary  │       │    status   │
       ▲              └─────────────┘       └─────────────┘
       │                     │
       │              ┌──────┴──────┐
       │              │             │
       ▼              ▼             ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   teams     │  │meeting_trans│  │ meeting_part│
├─────────────┤  ├─────────────┤  ├─────────────┤
│ PK id       │  │ PK id       │  │ PK id       │
│    name     │  │ FK meeting  │  │ FK meeting  │
│    is_public│  │    content  │  │ FK user     │
└─────────────┘  │    segment  │  │    role     │
       ▲         └─────────────┘  └─────────────┘
       │
       │    ┌─────────────┐
       └───►│ team_members│
            ├─────────────┤
            │ PK id       │
            │ FK team     │
            │ FK user     │
            │    role     │
            └─────────────┘
```

#### 3.1.2 物理表结构设计

**表 1：users（用户表）**

| 字段名 | 数据类型 | 约束 | 说明 |
|--------|---------|------|------|
| id | BIGINT UNSIGNED | PK, AUTO_INCREMENT | 用户唯一标识 |
| username | VARCHAR(50) | NOT NULL, UNIQUE | 用户名 |
| email | VARCHAR(120) | NOT NULL, UNIQUE | 邮箱地址 |
| password_hash | VARCHAR(255) | NOT NULL | 密码哈希值 |
| full_name | VARCHAR(100) | NOT NULL | 真实姓名 |
| role | ENUM('admin','member') | NOT NULL, DEFAULT 'member' | 用户角色 |
| is_active | TINYINT(1) | NOT NULL, DEFAULT 1 | 账号状态 |
| last_login_at | DATETIME | NULL | 最后登录时间 |
| created_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | NOT NULL, ON UPDATE CURRENT_TIMESTAMP | 更新时间 |

**索引设计**：
- 主键索引：id
- 唯一索引：uk_users_username, uk_users_email
- 普通索引：idx_users_role

---

**表 2：meetings（会议表）**

| 字段名 | 数据类型 | 约束 | 说明 |
|--------|---------|------|------|
| id | BIGINT UNSIGNED | PK, AUTO_INCREMENT | 会议唯一标识 |
| title | VARCHAR(200) | NOT NULL | 会议标题 |
| description | TEXT | NULL | 会议描述 |
| organizer_id | BIGINT UNSIGNED | NOT NULL, FK → users.id | 组织者ID |
| team_id | BIGINT UNSIGNED | NULL, FK → teams.id | 所属团队ID |
| scheduled_start_at | DATETIME | NULL | 计划开始时间 |
| scheduled_end_at | DATETIME | NULL | 计划结束时间 |
| actual_start_at | DATETIME | NULL | 实际开始时间 |
| actual_end_at | DATETIME | NULL | 实际结束时间 |
| location | VARCHAR(255) | NULL | 会议地点/链接 |
| status | ENUM('planned','ongoing','done','cancelled') | NOT NULL, DEFAULT 'planned' | 会议状态 |
| summary | TEXT | NULL | 会议纪要摘要 |
| share_token | VARCHAR(64) | NULL, UNIQUE | 分享令牌 |
| shared_at | DATETIME | NULL | 分享时间 |
| postprocessed_at | DATETIME | NULL | AI处理时间 |
| postprocess_version | VARCHAR(32) | NULL | 处理版本标识 |
| created_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | NOT NULL, ON UPDATE CURRENT_TIMESTAMP | 更新时间 |

**索引设计**：
- 主键索引：id
- 外键索引：idx_meetings_organizer_id
- 状态索引：idx_meetings_status
- 时间索引：idx_meetings_scheduled_start_at
- 唯一索引：share_token

---

**表 3：meeting_transcripts（会议转写表）**

| 字段名 | 数据类型 | 约束 | 说明 |
|--------|---------|------|------|
| id | BIGINT UNSIGNED | PK, AUTO_INCREMENT | 转写记录ID |
| meeting_id | BIGINT UNSIGNED | NOT NULL, FK → meetings.id | 所属会议ID |
| speaker_user_id | BIGINT UNSIGNED | NULL, FK → users.id | 发言用户ID |
| speaker_name | VARCHAR(100) | NULL | 发言人名称 |
| segment_index | INT UNSIGNED | NOT NULL | 片段序号 |
| start_time_sec | DECIMAL(10,3) | NULL | 开始秒数 |
| end_time_sec | DECIMAL(10,3) | NULL | 结束秒数 |
| language_code | VARCHAR(10) | NOT NULL, DEFAULT 'zh-CN' | 语言代码 |
| source | ENUM('whisper','manual','imported') | NOT NULL, DEFAULT 'whisper' | 来源类型 |
| content | LONGTEXT | NOT NULL | 转写文本内容 |
| created_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | NOT NULL, ON UPDATE CURRENT_TIMESTAMP | 更新时间 |

**索引设计**：
- 主键索引：id
- 唯一索引：uk_transcripts_meeting_segment (meeting_id, segment_index)
- 外键索引：idx_transcripts_meeting_id, idx_transcripts_speaker_user_id

---

**表 4：tasks（任务表）**

| 字段名 | 数据类型 | 约束 | 说明 |
|--------|---------|------|------|
| id | BIGINT UNSIGNED | PK, AUTO_INCREMENT | 任务唯一标识 |
| meeting_id | BIGINT UNSIGNED | NOT NULL, FK → meetings.id | 来源会议ID |
| transcript_id | BIGINT UNSIGNED | NULL, FK → meeting_transcripts.id | 来源转写ID |
| title | VARCHAR(200) | NOT NULL | 任务标题 |
| description | TEXT | NULL | 任务描述 |
| assignee_id | BIGINT UNSIGNED | NULL, FK → users.id | 执行人ID |
| reporter_id | BIGINT UNSIGNED | NULL, FK → users.id | 创建人ID |
| priority | ENUM('high','medium','low') | NOT NULL, DEFAULT 'medium' | 优先级 |
| status | ENUM('todo','in_progress','done') | NOT NULL, DEFAULT 'todo' | 任务状态 |
| due_at | DATETIME | NULL | 截止时间 |
| completed_at | DATETIME | NULL | 完成时间 |
| created_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | NOT NULL, ON UPDATE CURRENT_TIMESTAMP | 更新时间 |

**索引设计**：
- 主键索引：id
- 外键索引：idx_tasks_meeting_id, idx_tasks_assignee_id, idx_tasks_reporter_id
- 状态索引：idx_tasks_status
- 时间索引：idx_tasks_due_at

---

**表 5：teams（团队表）**

| 字段名 | 数据类型 | 约束 | 说明 |
|--------|---------|------|------|
| id | BIGINT UNSIGNED | PK, AUTO_INCREMENT | 团队唯一标识 |
| name | VARCHAR(100) | NOT NULL | 团队名称 |
| description | TEXT | NULL | 团队描述 |
| owner_id | BIGINT UNSIGNED | NOT NULL, FK → users.id | 创建者ID |
| is_public | TINYINT(1) | NOT NULL, DEFAULT 0 | 是否公开 |
| max_members | INT | NOT NULL, DEFAULT 50 | 最大成员数 |
| created_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | NOT NULL, ON UPDATE CURRENT_TIMESTAMP | 更新时间 |

---

**表 6：team_members（团队成员表）**

| 字段名 | 数据类型 | 约束 | 说明 |
|--------|---------|------|------|
| id | BIGINT UNSIGNED | PK, AUTO_INCREMENT | 记录ID |
| team_id | BIGINT UNSIGNED | NOT NULL, FK → teams.id | 团队ID |
| user_id | BIGINT UNSIGNED | NOT NULL, FK → users.id | 用户ID |
| role | ENUM('owner','admin','member') | NOT NULL, DEFAULT 'member' | 成员角色 |
| joined_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 加入时间 |

**唯一约束**：(team_id, user_id)

---

**表 7：team_invitations（团队邀请表）**

| 字段名 | 数据类型 | 约束 | 说明 |
|--------|---------|------|------|
| id | BIGINT UNSIGNED | PK, AUTO_INCREMENT | 邀请记录ID |
| team_id | BIGINT UNSIGNED | NOT NULL, FK → teams.id | 团队ID |
| inviter_id | BIGINT UNSIGNED | NOT NULL, FK → users.id | 邀请人ID |
| invitee_email | VARCHAR(120) | NOT NULL | 被邀请人邮箱 |
| status | ENUM('pending','accepted','rejected') | NOT NULL, DEFAULT 'pending' | 邀请状态 |
| token | VARCHAR(64) | NULL, UNIQUE | 邀请令牌 |
| created_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| responded_at | DATETIME | NULL | 响应时间 |

---

**表 8：audit_logs（审计日志表）**

| 字段名 | 数据类型 | 约束 | 说明 |
|--------|---------|------|------|
| id | BIGINT UNSIGNED | PK, AUTO_INCREMENT | 日志ID |
| actor_user_id | BIGINT UNSIGNED | NULL, FK → users.id | 操作用户ID |
| entity_type | VARCHAR(50) | NOT NULL | 实体类型 |
| entity_id | BIGINT UNSIGNED | NOT NULL | 实体ID |
| action | VARCHAR(50) | NOT NULL | 操作类型 |
| details | JSON | NULL | 详细内容 |
| created_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 操作时间 |

---

### 3.2 核心业务逻辑设计

#### 3.2.1 会议创建流程

```
用户请求创建会议
       │
       ▼
┌─────────────┐
│ 1. 权限校验  │◄── 验证用户身份与角色
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 2. 数据验证  │◄── 校验必填字段、时间范围
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 3. 创建会议  │◄── 插入 meetings 表
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 4. 添加组织者 │◄── 自动添加会议参与者（role=organizer）
│ 为参与者     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 5. 返回结果  │
└─────────────┘
```

**业务规则**：
- 会议组织者自动成为会议参与者
- 团队会议需验证用户是否为团队成员
- 计划结束时间必须晚于开始时间

#### 3.2.2 AI 后处理流程

```
触发后处理请求
       │
       ▼
┌─────────────┐
│ 1. 权限检查  │◄── 仅组织者或管理员可操作
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 2. 获取转写  │◄── 查询 meeting_transcripts
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌─────────────────┐
│ 3. 生成摘要  │────►│ LLMService      │
└──────┬──────┘     │ - OpenAI API    │
       │            │ - Ollama 本地   │
       │            │ - Rule 回退     │
       │            └─────────────────┘
       ▼
┌─────────────┐     ┌─────────────────┐
│ 4. 提取任务  │────►│ Task Extraction │
└──────┬──────┘     │ - 模式匹配      │
       │            │ - LLM 提取      │
       │            └─────────────────┘
       ▼
┌─────────────┐
│ 5. 保存结果  │◄── 更新 meetings.summary
│              │    插入 tasks 记录
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 6. 返回结果  │
└─────────────┘
```

**回退机制**：
- LLM 服务不可用时，使用规则引擎提取关键词生成摘要
- 任务提取支持正则匹配 + LLM 双路径

#### 3.2.3 任务状态流转

```
状态图：

    ┌─────────┐    开始执行     ┌─────────────┐
    │  todo   │ ──────────────► │ in_progress │
    └────┬────┘                 └──────┬──────┘
         │                             │
         │         直接完成            │ 完成
         └────────────────────────────►│
                                       ▼
                                 ┌─────────┐
                                 │  done   │
                                 └─────────┘

规则：
- todo → in_progress：执行人开始处理
- todo → done：任务直接完成
- in_progress → done：任务处理完成
- 禁止反向流转
```

### 3.3 API 接口设计

#### 3.3.1 RESTful API 规范

**基础规范**：
- 基础路径：`/api/v1`
- 认证方式：Bearer Token (JWT)
- 请求格式：JSON
- 响应格式：统一包装

**统一响应格式**：
```json
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```

**错误响应格式**：
```json
{
  "code": 400,
  "message": "Invalid request parameters",
  "error_code": "VALIDATION_ERROR"
}
```

#### 3.3.2 核心接口列表

**认证模块**

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /api/v1/register | 用户注册 | 否 |
| POST | /api/v1/auth/login | 用户登录 | 否 |
| GET | /api/v1/auth/me | 获取当前用户 | 是 |

**会议模块**

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /api/v1/meetings | 会议列表 | 是 |
| POST | /api/v1/meetings | 创建会议 | 是 |
| GET | /api/v1/meetings/{id} | 会议详情 | 是 |
| PATCH | /api/v1/meetings/{id} | 更新会议 | 是 |
| DELETE | /api/v1/meetings/{id} | 删除会议 | 是 |
| POST | /api/v1/meetings/{id}/postprocess | AI后处理 | 是 |
| POST | /api/v1/meetings/{id}/audio | 上传音频 | 是 |

**转写模块**

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /api/v1/transcripts | 转写列表 | 是 |
| POST | /api/v1/transcripts | 创建转写 | 是 |
| GET | /api/v1/transcripts/{id} | 转写详情 | 是 |
| PATCH | /api/v1/transcripts/{id} | 更新转写 | 是 |

**任务模块**

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /api/v1/tasks | 任务列表 | 是 |
| POST | /api/v1/tasks | 创建任务 | 是 |
| GET | /api/v1/tasks/{id} | 任务详情 | 是 |
| PATCH | /api/v1/tasks/{id} | 更新任务 | 是 |
| DELETE | /api/v1/tasks/{id} | 删除任务 | 是 |

**团队模块**

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /api/v1/teams | 团队列表 | 是 |
| POST | /api/v1/teams | 创建团队 | 是 |
| GET | /api/v1/teams/{id} | 团队详情 | 是 |
| POST | /api/v1/teams/{id}/invite | 邀请成员 | 是 |
| POST | /api/v1/invitations/{id}/accept | 接受邀请 | 是 |

#### 3.3.3 接口示例

**创建会议接口**

```http
POST /api/v1/meetings
Content-Type: application/json
Authorization: Bearer {jwt_token}

{
  "title": "产品评审会议",
  "description": "讨论Q2产品规划",
  "organizer_id": 1001,
  "scheduled_start_at": "2026-04-10T14:00:00",
  "scheduled_end_at": "2026-04-10T15:30:00",
  "location": "会议室A301",
  "team_id": null
}
```

**响应**：
```json
{
  "id": 2001,
  "title": "产品评审会议",
  "description": "讨论Q2产品规划",
  "organizer_id": 1001,
  "status": "planned",
  "created_at": "2026-04-06T10:30:00"
}
```

### 3.4 界面设计

#### 3.4.1 页面结构规划

```
SmartMeeting Frontend
│
├── 公共布局 (Layout)
│   ├── 侧边栏导航
│   │   ├── 仪表盘
│   │   ├── 会议管理
│   │   ├── 任务中心
│   │   ├── 团队管理
│   │   └── 系统设置
│   ├── 顶部栏
│   │   ├── 用户头像/下拉菜单
│   │   ├── 通知中心
│   │   └── 语言切换
│   └── 主内容区
│
├── 页面视图 (Views)
│   ├── LoginView (登录页)
│   ├── DashboardView (仪表盘)
│   ├── MeetingListView (会议列表)
│   ├── MeetingDetailView (会议详情工作台)
│   ├── TasksView (任务中心)
│   ├── TeamsView (团队列表)
│   ├── TeamDetailView (团队详情)
│   ├── InvitationsView (邀请管理)
│   ├── HotwordsView (热词管理)
│   └── SharedMeetingView (会议分享页)
│
└── 复用组件 (Components)
    ├── ParticipantManager (参与者管理)
    ├── TaskManager (任务管理)
    ├── AppErrorAlert (错误提示)
    └── 各类 Element Plus 组件封装
```

#### 3.4.2 主要页面设计

**1. 登录页 (LoginView)**

```
┌─────────────────────────────────────────┐
│                                         │
│           SmartMeeting                  │
│         智能会议管理系统                  │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ 用户名/邮箱                      │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │ 密码                            │   │
│  └─────────────────────────────────┘   │
│                                         │
│  [         登    录              ]     │
│                                         │
│  还没有账号？ 立即注册                  │
│                                         │
└─────────────────────────────────────────┘
```

**2. 仪表盘 (DashboardView)**

```
┌─────────────────────────────────────────────────────────┐
│  SmartMeeting      [搜索...]      [通知] [用户▼]        │
├──────────┬──────────────────────────────────────────────┤
│  仪表盘   │                                              │
│  会议管理 │   统计卡片                                    │
│  任务中心 │   ┌────────┐ ┌────────┐ ┌────────┐         │
│  团队管理 │   │ 会议数 │ │ 任务数 │ │ 待处理 │         │
│          │   │  128   │ │  45    │ │  12    │         │
│          │   └────────┘ └────────┘ └────────┘         │
│          │                                              │
│          │   ┌──────────────────┐ ┌────────────────┐   │
│          │   │   最近会议        │ │   待办任务      │   │
│          │   │   • 产品评审...   │ │   • 完成API...  │   │
│          │   │   • 周会同步...   │ │   • 更新文档... │   │
│          │   └──────────────────┘ └────────────────┘   │
│          │                                              │
└──────────┴──────────────────────────────────────────────┘
```

**3. 会议详情页 (MeetingDetailView)**

```
┌─────────────────────────────────────────────────────────┐
│  SmartMeeting      [搜索...]      [通知] [用户▼]        │
├─────────────────────────────────────────────────────────┤
│  产品评审会议                                    [编辑]  │
│  组织者: 张三 | 时间: 2026-04-10 14:00                  │
│  状态: 已完成                                           │
├─────────────────────────────────────────────────────────┤
│  [会议纪要] [转写记录] [任务列表] [参与者] [设置]         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ## 会议纪要                                            │
│  本次会议讨论了Q2产品规划，确定了以下事项...              │
│                                                         │
│  [重新生成摘要] [分享会议] [导出文档]                    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**4. 任务中心 (TasksView)**

```
┌─────────────────────────────────────────────────────────┐
│  任务中心                          [新建任务] [筛选▼]    │
├─────────────────────────────────────────────────────────┤
│  [全部] [待办] [进行中] [已完成]                         │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────┐   │
│  │ 优先级 │ 任务标题        │ 会议      │ 状态     │   │
│  ├────────┼─────────────────┼───────────┼──────────┤   │
│  │ 高     │ 完成API接口设计 │ 产品评审  │ 待办     │   │
│  │ 中     │ 更新技术文档    │ 周会同步  │ 进行中   │   │
│  │ 低     │ 整理会议纪要    │ 产品评审  │ 已完成   │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  [上一页] 第 1/5 页 [下一页]                             │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

#### 3.4.3 交互流程设计

**创建会议流程**：
```
1. 用户点击"新建会议"按钮
   ↓
2. 弹出表单抽屉/模态框
   - 输入会议标题（必填）
   - 输入会议描述（选填）
   - 选择计划时间（起止时间）
   - 输入地点/链接
   - 选择所属团队（选填）
   ↓
3. 前端表单校验
   - 标题不能为空
   - 结束时间必须晚于开始时间
   ↓
4. 提交 API 请求
   ↓
5. 后端处理并返回结果
   ↓
6. 前端显示成功提示，刷新列表
```

**AI 后处理触发流程**：
```
1. 用户进入会议详情页
   ↓
2. 查看转写记录是否已存在
   ↓
3. 点击"生成摘要"按钮
   ↓
4. 前端显示加载状态
   ↓
5. 调用 POST /api/v1/meetings/{id}/postprocess
   ↓
6. 后端异步处理（Whisper → LLM）
   ↓
7. 返回摘要内容和提取的任务
   ↓
8. 前端更新会议纪要展示
   ↓
9. 任务自动添加到任务列表
```

---

## 4. 非功能性设计

### 4.1 安全性设计

#### 4.1.1 认证与授权

**JWT 认证机制**：
```python
# Token 结构
{
  "sub": "1001",           # 用户ID
  "exp": 1712380800,       # 过期时间
  "iat": 1712294400        # 签发时间
}

# 认证流程
请求头: Authorization: Bearer {jwt_token}
   ↓
中间件解析 Token
   ↓
验证签名与过期时间
   ↓
查询用户是否存在且激活
   ↓
注入 current_user 到请求上下文
```

**权限控制矩阵**：

| 功能 | Admin | Member (组织者) | Member (参与者) | 访客 |
|------|-------|----------------|----------------|------|
| 创建会议 | ✓ | ✓ | ✓ | ✗ |
| 编辑他人会议 | ✓ | ✗ | ✗ | ✗ |
| 删除会议 | ✓ | ✓(自己的) | ✗ | ✗ |
| 管理参与者 | ✓ | ✓ | ✗ | ✗ |
| 查看会议 | ✓ | ✓ | ✓ | ✓(分享的) |
| 创建任务 | ✓ | ✓ | ✗ | ✗ |
| 更新任务状态 | ✓ | ✓ | ✓(自己的) | ✗ |

#### 4.1.2 数据安全

**密码安全**：
- 使用 PBKDF2-SHA256 算法进行密码哈希
- 盐值随机生成，存储于哈希字符串中
- 禁止明文存储或传输密码

**敏感数据保护**：
- API 密钥、数据库凭据存储于环境变量
- JWT Secret 定期轮换机制
- 生产环境强制 HTTPS 传输

**SQL 注入防护**：
- 使用 SQLAlchemy ORM，禁止直接拼接 SQL
- 所有用户输入参数化查询

### 4.2 性能设计

#### 4.2.1 数据库性能

**索引策略**：
- 所有外键字段建立索引
- 常用查询条件字段建立索引（status、created_at 等）
- 复合索引优化组合查询

**查询优化**：
```python
# 使用 joinedload 避免 N+1 查询
from sqlalchemy.orm import joinedload

query = (
    db.query(Meeting)
    .options(joinedload(Meeting.organizer))
    .filter(Meeting.status == "planned")
    .all()
)
```

**分页设计**：
- 列表接口默认返回 20 条/页
- 最大限制 100 条/页
- 支持游标分页（大数据量场景）

#### 4.2.2 缓存策略

**热词缓存**：
```python
# 应用启动时加载热词到内存
_hotword_cache: set[str] = set()

def get_hotword_terms(db: Session) -> set[str]:
    if not _hotword_cache:
        terms = db.query(Hotword.word).all()
        _hotword_cache.update([t[0] for t in terms])
    return _hotword_cache
```

**LLM 结果缓存（可选）**：
- 相同转写内容的摘要请求可缓存 1 小时
- 使用 Redis 作为分布式缓存（后续扩展）

### 4.3 可扩展性设计

#### 4.3.1 微服务拆分预留

当前单体架构预留以下服务拆分点：

```
当前:                    未来可能的拆分:
┌─────────────────┐      ┌─────────────────┐
│  SmartMeeting   │      │  API Gateway    │
│  Monolith       │  →   ├─────────────────┤
│                 │      │  User Service   │
│  - API          │      │  Meeting Service│
│  - Services     │      │  Task Service   │
│  - AI Process   │      │  AI Service     │
└─────────────────┘      │  Notification   │
                         └─────────────────┘
```

#### 4.3.2 插件化设计

**AI 服务 Provider 接口**：
```python
class LLMProvider(ABC):
    @abstractmethod
    async def generate_summary(self, transcripts: list[str]) -> str:
        pass

class OpenAIProvider(LLMProvider): ...
class OllamaProvider(LLMProvider): ...
class RuleBasedProvider(LLMProvider): ...  # 回退实现
```

---

## 5. 部署架构

### 5.1 Docker 部署

**容器架构**：
```yaml
# docker-compose.yml 核心服务
services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_ROOT_PASSWORD}
      MYSQL_DATABASE: smartmeeting
    volumes:
      - mysql_data:/var/lib/mysql

  backend:
    build: ./backend
    environment:
      DATABASE_URL: mysql+pymysql://...
      LLM_API_KEY: ${LLM_API_KEY}
    volumes:
      - audio_storage:/app/storage/audio
    depends_on:
      - mysql

  frontend:
    build: ./frontend
    ports:
      - "5174:80"
    depends_on:
      - backend
```

### 5.2 环境配置

**生产环境 checklist**：
- [ ] 修改 JWT_SECRET_KEY（强随机字符串）
- [ ] 配置正式 MySQL 数据库
- [ ] 配置对象存储（音频文件）
- [ ] 配置 LLM API Key
- [ ] 启用 HTTPS
- [ ] 配置日志收集（ELK/Fluentd）
- [ ] 配置监控告警（Prometheus/Grafana）

### 5.3 CI/CD 流程

```
Git Push
   ↓
GitHub Actions
   ├── Backend Tests (pytest)
   ├── Frontend Type Check
   ├── Frontend Build
   └── Docker Build & Push
   ↓
Deployment (手动/自动)
```

---

## 6. 附录

### 6.1 数据库迁移记录

| 版本 | 文件名 | 说明 |
|------|--------|------|
| 001 | 001_init_smartmeeting.sql | 初始 schema |
| 002 | 002_enhance_smartmeeting.sql | 增强字段 |
| 003 | 003_sp_task_query.sql | 存储过程 |
| 004 | 004_indexes_perf.sql | 性能索引 |
| 005 | 005_audit_and_participants.sql | 审计与参与者 |
| 006 | 006_collaboration_share_fields.sql | 协作分享 |
| 007 | 007_create_team_invitations.sql | 团队邀请 |
| ... | ... | ... |
| 018 | 018_create_team_invite_links.sql | 邀请链接 |

### 6.2 API 端点汇总

完整 API 文档参考：`docs/backend-api.md`

### 6.3 前端路由映射

| 路由 | 视图组件 | 说明 |
|------|---------|------|
| /login | LoginView | 登录 |
| / | DashboardView | 仪表盘 |
| /meetings | MeetingListView | 会议列表 |
| /meetings/:id | MeetingDetailView | 会议详情 |
| /tasks | TasksView | 任务中心 |
| /teams | TeamsView | 团队列表 |
| /teams/:id | TeamDetailView | 团队详情 |
| /invitations | InvitationsView | 邀请管理 |
| /invite/:token | InviteAcceptView | 接受邀请 |
| /hotwords | HotwordsView | 热词管理 |
| /share/:token | SharedMeetingView | 分享查看 |

### 6.4 开发规范

**后端规范**：
- 遵循 PEP 8 代码风格
- 类型注解全覆盖
- 函数文档字符串（Google Style）
- 单元测试覆盖率 > 80%

**前端规范**：
- ESLint + Prettier 自动格式化
- Composition API + `<script setup>`
- 组件名 PascalCase
- 组合式函数 useXxx 命名

---

**文档结束**

---

*本文档由 SmartMeeting 开发团队维护，如有变更请及时更新。*