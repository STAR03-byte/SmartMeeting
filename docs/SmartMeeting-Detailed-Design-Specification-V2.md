# SmartMeeting 智能会议与任务管理系统

## 软件详细设计说明书

**文档编号**：SM-DDD-V1.0  
**版本号**：V1.0  
**编制单位**：SmartMeeting 开发团队  
**编制日期**：2026年4月6日  
**审核日期**：  
**批准日期**：

---

## 文档控制页

### 版本历史

| 版本号 | 修改日期 | 修改人 | 修改说明 |
|--------|----------|--------|----------|
| V1.0 | 2026-04-06 | 开发团队 | 初始版本，按 GB/T 8567-2006 标准编制 |

### 审核记录

| 审核角色 | 审核人 | 审核日期 | 审核意见 |
|----------|--------|----------|----------|
| 编制人 | 开发团队 | 2026-04-06 | 完成编制 |
| 审核人 | | | |
| 批准人 | | | |

### 分发记录

| 分发对象 | 分发日期 | 分发份数 | 接收人签字 |
|----------|----------|----------|------------|
| | | | |

---

## 目 录

1. [引言](#1-引言)
2. [总体设计](#2-总体设计)
3. [程序系统结构设计](#3-程序系统结构设计)
4. [程序（模块）设计说明](#4-程序模块设计说明)
5. [数据库设计](#5-数据库设计)
6. [接口设计](#6-接口设计)
7. [界面详细设计](#7-界面详细设计)
8. [系统出错处理设计](#8-系统出错处理设计)
9. [系统维护设计](#9-系统维护设计)
10. [附录](#10-附录)

---

## 1. 引言

### 1.1 编写目的

本文档是 SmartMeeting 智能会议与任务管理系统的详细设计说明书。本文档的编写目的如下：

1. **指导开发**：为软件开发人员提供详细的技术实现指导，确保开发工作按照统一的标准和规范进行；
2. **沟通工具**：作为开发团队、测试团队、运维团队之间的技术沟通依据；
3. **验收基准**：作为系统测试和验收的技术基准文档；
4. **维护参考**：为系统后期维护和升级提供技术参考。

本文档的预期读者包括：软件开发工程师、测试工程师、系统架构师、项目经理、运维工程师。

### 1.2 背景

**项目名称**：SmartMeeting 智能会议与任务管理系统

**项目提出者**：企业信息化建设部门

**开发单位**：SmartMeeting 开发团队

**用户单位**：企业内部团队及协作部门

**项目背景**：
随着企业规模扩大和远程办公需求增加，传统的会议管理方式（邮件通知、人工记录、分散的任务跟进）已无法满足高效协作的需求。SmartMeeting 旨在通过 AI 技术实现会议录制、语音转写、智能摘要和任务自动提取，提升会议效率和信息留存质量。

### 1.3 定义

本说明书中的术语定义如下：

| 术语 | 英文全称 | 定义 |
|------|----------|------|
| JWT | JSON Web Token | 一种开放标准（RFC 7519），用于在网络应用环境间安全地传输信息 |
| ORM | Object-Relational Mapping | 对象关系映射，实现面向对象编程语言与关系数据库之间的数据转换 |
| ASR | Automatic Speech Recognition | 自动语音识别，将语音信号转换为文本的技术 |
| LLM | Large Language Model | 大语言模型，具有强大文本理解和生成能力的 AI 模型 |
| REST | Representational State Transfer | 表述性状态转移，一种软件架构风格 |
| API | Application Programming Interface | 应用程序编程接口 |
| SQL | Structured Query Language | 结构化查询语言，用于关系型数据库操作 |
| CRUD | Create, Read, Update, Delete | 数据持久化的四种基本操作 |
| CI/CD | Continuous Integration/Continuous Deployment | 持续集成/持续部署 |

### 1.4 参考资料

1. 《SmartMeeting 智能会议系统项目立项规划书》，SmartMeeting 开发团队，2026年3月
2. 《SmartMeeting 软件需求规格说明书 SRS》，SmartMeeting 开发团队，2026年4月
3. GB/T 8567-2006《计算机软件文档编制规范》
4. GB/T 25000.51-2016《系统与软件工程 系统与软件质量要求和评价》
5. FastAPI 官方文档：https://fastapi.tiangolo.com/
6. Vue 3 官方文档：https://vuejs.org/
7. SQLAlchemy 2.0 文档：https://docs.sqlalchemy.org/
8. Element Plus 组件库文档：https://element-plus.org/

---

## 2. 总体设计

### 2.1 需求规定

本系统的功能需求和非功能需求详见《SmartMeeting 软件需求规格说明书 SRS》。核心需求概要如下：

**功能需求**：
- 用户注册、登录、权限管理
- 会议创建、管理、分享
- 音频录制、上传、转写
- AI 会议纪要生成
- 任务自动提取与追踪
- 团队协作与邀请

**非功能需求**：
- 系统响应时间：API 响应 < 500ms（95分位）
- 并发用户：支持 100+ 并发
- 可用性：99.5% 在线率
- 数据安全：JWT 认证、密码加密、SQL 注入防护

### 2.2 运行环境

#### 2.2.1 服务器环境

| 组件 | 版本/配置 | 说明 |
|------|-----------|------|
| 操作系统 | Linux (Ubuntu 22.04 LTS) | 推荐，支持 Docker |
| Python | 3.10+ | 后端运行时 |
| MySQL | 8.0 | 主数据库 |
| Redis | 7.0+ | 可选缓存 |
| Docker | 24.0+ | 容器化部署 |
| Docker Compose | 2.20+ | 多容器编排 |

#### 2.2.2 客户端环境

| 组件 | 版本 | 说明 |
|------|------|------|
| 浏览器 | Chrome 90+, Firefox 90+, Edge 90+ | 现代浏览器 |
| 最低分辨率 | 1280×768 | 响应式布局支持 |

### 2.3 基本设计概念和处理流程

#### 2.3.1 系统架构风格

本系统采用**前后端分离的三层架构模式**：

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

#### 2.3.2 核心业务流程

**会议创建与处理流程**：

```
用户登录
   │
   ▼
创建会议 ──────────────────────┐
   │                           │
   ▼                           │
上传音频文件                   │
   │                           │
   ▼                           │
语音识别 (Whisper)             │
   │                           │
   ▼                           │
生成转写文本                   │
   │                           │
   ▼                           ▼
AI 后处理 (LLM) ◄──────────────┘
   │
   ├──► 生成会议纪要
   │
   └──► 自动提取任务
            │
            ▼
      任务分配与追踪
```

### 2.4 结构

#### 2.4.1 系统模块划分

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

#### 2.4.2 技术栈结构

**后端技术栈**：

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

**前端技术栈**：

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

### 2.5 功能需求与程序的关系

| 功能需求 | 认证模块 | 会议模块 | 转写模块 | 任务模块 | 团队模块 | AI模块 | 系统模块 |
|----------|----------|----------|----------|----------|----------|--------|----------|
| 用户注册/登录 | ✓ | | | | | | ✓ |
| 会议创建/管理 | ✓ | ✓ | | | ✓ | | |
| 音频上传/转写 | ✓ | ✓ | ✓ | | | ✓ | |
| 会议纪要生成 | ✓ | ✓ | ✓ | | | ✓ | |
| 任务自动提取 | ✓ | | ✓ | ✓ | | ✓ | |
| 任务追踪 | ✓ | | | ✓ | | | |
| 团队协作 | ✓ | ✓ | | ✓ | ✓ | | |
| 审计日志 | | | | | | | ✓ |

### 2.6 人工处理过程

本系统设计中需要人工介入的环节：

1. **音频上传**：用户需要手动上传会议录音文件
2. **转写校正**：AI 转写结果可能需要人工校对和修正
3. **任务确认**：自动提取的任务需要执行人确认接受
4. **会议纪要审核**：重要会议的 AI 生成摘要建议人工复核
5. **系统配置**：管理员需配置 LLM API 密钥、热词等系统参数

### 2.7 尚未解决的问题

1. **实时转写**：当前仅支持录音文件上传后转写，未实现会议实时转写
2. **多语言支持**：目前主要支持中文，多语言转写和摘要需后续扩展
3. **移动端适配**：当前以 Web 端为主，移动端体验需优化
4. **音视频同步**：未实现转写文本与音频时间点同步播放

---

## 3. 程序系统结构设计

### 3.1 程序(模块)划分

#### 3.1.1 程序(模块)划分表

| 模块编号 | 模块名称 | 功能描述 | 优先级 | 对应文件/目录 |
|----------|----------|----------|--------|---------------|
| M01 | 认证模块 | 用户注册、登录、JWT管理、权限验证 | 高 | `backend/app/services/auth_service.py` |
| M02 | 用户模块 | 用户信息管理、角色管理 | 高 | `backend/app/services/user_service.py` |
| M03 | 会议模块 | 会议CRUD、状态管理、分享 | 高 | `backend/app/services/meeting_service.py` |
| M04 | 转写模块 | 转写记录管理、分段存储 | 高 | `backend/app/services/transcript_service.py` |
| M05 | 任务模块 | 任务CRUD、状态流转、优先级管理 | 高 | `backend/app/services/task_service.py` |
| M06 | 团队模块 | 团队管理、成员管理、邀请 | 中 | `backend/app/services/team_service.py` |
| M07 | AI处理模块 | Whisper转写、LLM摘要、任务提取 | 高 | `backend/app/services/llm_service.py` |
| M08 | 系统模块 | 审计日志、热词管理、配置 | 中 | `backend/app/services/` |
| M09 | 前端展示模块 | 用户界面、交互逻辑 | 高 | `frontend/src/views/` |

#### 3.1.2 程序(模块)层次结构关系

```
SmartMeeting System
│
├── Presentation Layer (前端)
│   ├── LoginView (M09)
│   ├── DashboardView (M09)
│   ├── MeetingListView (M09)
│   ├── MeetingDetailView (M09)
│   ├── TasksView (M09)
│   ├── TeamsView (M09)
│   └── SharedMeetingView (M09)
│
└── Business Layer (后端)
    ├── API Endpoints
    │   ├── auth_router (M01)
    │   ├── user_router (M02)
    │   ├── meeting_router (M03)
    │   ├── transcript_router (M04)
    │   ├── task_router (M05)
    │   ├── team_router (M06)
    │   └── system_router (M08)
    │
    └── Services
        ├── AuthService (M01)
        ├── UserService (M02)
        ├── MeetingService (M03)
        ├── TranscriptService (M04)
        ├── TaskService (M05)
        ├── TeamService (M06)
        └── LLMService (M07)
```

### 3.2 程序(模块)功能分配

#### 3.2.1 功能分配表

| 功能编号 | 功能名称 | 程序(模块)编号 | 程序(模块)名称 |
|----------|----------|----------------|----------------|
| F01 | 用户注册 | M01, M02 | 认证模块、用户模块 |
| F02 | 用户登录 | M01 | 认证模块 |
| F03 | JWT验证 | M01 | 认证模块 |
| F04 | 创建会议 | M03, M01 | 会议模块、认证模块 |
| F05 | 更新会议 | M03, M01 | 会议模块、认证模块 |
| F06 | 删除会议 | M03, M01 | 会议模块、认证模块 |
| F07 | 音频上传 | M03, M04 | 会议模块、转写模块 |
| F08 | 语音识别 | M07, M04 | AI模块、转写模块 |
| F09 | 生成摘要 | M07, M03 | AI模块、会议模块 |
| F10 | 提取任务 | M07, M05 | AI模块、任务模块 |
| F11 | 任务管理 | M05, M01 | 任务模块、认证模块 |
| F12 | 团队管理 | M06, M01 | 团队模块、认证模块 |
| F13 | 邀请成员 | M06, M02 | 团队模块、用户模块 |
| F14 | 审计日志 | M08 | 系统模块 |

#### 3.2.2 功能与模块交叉引用矩阵

```
          M01  M02  M03  M04  M05  M06  M07  M08  M09
F01 注册   ✓    ✓                              ✓
F02 登录   ✓                                  ✓
F03 JWT    ✓
F04 创建   ✓         ✓                        ✓
F05 更新   ✓         ✓                        ✓
F06 删除   ✓         ✓                        ✓
F07 上传   ✓         ✓    ✓                   ✓
F08 识别             ✓         ✓    ✓         ✓
F09 摘要        ✓    ✓              ✓         ✓
F10 提取                  ✓    ✓    ✓         ✓
F11 任务   ✓                   ✓              ✓
F12 团队   ✓                        ✓         ✓
F13 邀请   ✓    ✓                   ✓         ✓
F14 日志                           ✓    ✓
```

---

## 4. 程序（模块）设计说明

### 4.1 程序(模块)1：认证模块 (M01)

#### 4.1.1 模块描述

本模块负责系统的身份认证与权限管理，包括用户注册、登录、JWT令牌管理、权限验证等功能。

#### 4.1.2 功能

- 用户注册：新用户注册账号
- 用户登录：验证用户凭据并颁发JWT令牌
- Token刷新：支持令牌续期
- 权限验证：基于角色的访问控制(RBAC)
- 密码管理：密码哈希存储与验证

#### 4.1.3 性能

- 登录响应时间：< 200ms
- Token验证开销：< 10ms
- 并发认证：支持100+并发登录

#### 4.1.4 输入项

| 名称 | 标识 | 类型 | 格式 | 有效范围 | 精度 | 输入方式 |
|------|------|------|------|----------|------|----------|
| 用户名 | username | string | 字母、数字、下划线 | 3-50字符 | - | API请求 |
| 密码 | password | string | 任意字符 | 8-128字符 | - | API请求 |
| 邮箱 | email | string | 邮箱格式 | 5-120字符 | - | API请求 |
| Token | token | string | JWT格式 | - | - | HTTP Header |

#### 4.1.5 输出项

| 名称 | 标识 | 类型 | 格式 | 有效范围 | 精度 | 输出方式 |
|------|------|------|------|----------|------|----------|
| 访问令牌 | access_token | string | JWT | - | - | JSON响应 |
| 令牌类型 | token_type | string | "bearer" | - | - | JSON响应 |
| 用户ID | user_id | integer | 正整数 | >0 | - | JSON响应 |
| 错误信息 | error | string | 错误描述 | - | - | JSON响应 |

#### 4.1.6 算法

**JWT生成算法**：
```python
# Header
header = base64url_encode({"alg": "HS256", "typ": "JWT"})

# Payload
payload = base64url_encode({
    "sub": user_id,
    "exp": current_time + expire_minutes * 60,
    "iat": current_time
})

# Signature
signature = HMAC_SHA256(
    key=SECRET_KEY,
    message=f"{header}.{payload}"
)

token = f"{header}.{payload}.{signature}"
```

**密码哈希算法 (PBKDF2-SHA256)**：
```python
hash = pbkdf2_sha256.hash(password, rounds=29000, salt_size=16)
```

#### 4.1.7 流程逻辑

**登录流程**：
```
用户提交登录请求
       │
       ▼
┌─────────────┐
│ 参数校验     │◄── 验证必填字段、格式
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 查询用户     │◄── 通过 username/email 查找
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 验证密码     │◄── 对比密码哈希
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 生成JWT     │◄── 创建访问令牌
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 返回结果     │◄── 返回token和用户信息
└─────────────┘
```

#### 4.1.8 接口

**对外接口**：

| 接口名称 | 方法 | 路径 | 认证 | 说明 |
|----------|------|------|------|------|
| register | POST | /api/v1/register | 否 | 用户注册 |
| login | POST | /api/v1/auth/login | 否 | 用户登录 |
| get_current_user | GET | /api/v1/auth/me | 是 | 获取当前用户 |

**内部接口**：

| 接口名称 | 参数 | 返回值 | 说明 |
|----------|------|--------|------|
| authenticate_user | db, username, password | User/None | 验证用户凭据 |
| create_access_token | user_id, expires_delta | str | 创建JWT令牌 |
| verify_token | token | TokenData | 验证JWT有效性 |
| get_current_active_user | token | User | 获取当前用户 |

#### 4.1.9 存储分配

- JWT Secret Key：存储于环境变量，启动时加载到内存
- Token有效期：配置文件中定义，默认24小时

#### 4.1.10 注释设计

```python
def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    验证用户凭据
    
    Args:
        db: 数据库会话
        username: 用户名
        password: 明文密码
        
    Returns:
        User对象（验证成功）或None（验证失败）
        
    Raises:
        无异常，验证失败返回None
    """
```

#### 4.1.11 限制条件

- JWT Secret Key必须强度足够，生产环境至少32字节随机字符串
- Token过期后必须重新登录获取新Token
- 密码最小长度8位，需包含字母和数字

#### 4.1.12 测试计划

| 测试项 | 测试内容 | 预期结果 |
|--------|----------|----------|
| 正常登录 | 使用正确凭据登录 | 返回有效JWT |
| 错误密码 | 使用错误密码登录 | 返回401错误 |
| 用户不存在 | 使用不存在的用户名登录 | 返回401错误 |
| Token过期 | 使用过期Token访问受保护接口 | 返回401错误 |
| Token伪造 | 使用篡改的Token访问 | 返回401错误 |

### 4.2 程序(模块)2：会议模块 (M03)

#### 4.2.1 模块描述

会议模块是系统的核心模块，负责会议的创建、管理、分享，以及与音频、转写、任务的关联管理。

#### 4.2.2 功能

- 会议CRUD操作
- 会议状态管理（planned/ongoing/done/cancelled）
- 音频文件上传与存储
- 会议纪要生成与更新
- 会议分享（生成分享链接）
- 参与者管理

#### 4.2.3 性能

- 会议列表查询：< 300ms（分页20条）
- 会议详情查询：< 100ms
- 音频上传：支持最大 500MB 文件

#### 4.2.4 输入项

| 名称 | 标识 | 类型 | 格式 | 有效范围 | 输入方式 |
|------|------|------|------|----------|----------|
| 会议标题 | title | string | 文本 | 1-200字符 | API请求 |
| 会议描述 | description | string | 文本 | 0-5000字符 | API请求 |
| 组织者ID | organizer_id | integer | 正整数 | >0 | API请求 |
| 团队ID | team_id | integer | 正整数 | >0 或 null | API请求 |
| 计划开始时间 | scheduled_start_at | datetime | ISO8601 | 未来时间 | API请求 |
| 计划结束时间 | scheduled_end_at | datetime | ISO8601 | 晚于开始时间 | API请求 |
| 地点 | location | string | 文本 | 0-255字符 | API请求 |
| 音频文件 | audio_file | file | MP3/WAV/M4A | < 500MB | 表单上传 |

#### 4.2.5 输出项

| 名称 | 标识 | 类型 | 格式 | 说明 |
|------|------|------|------|------|
| 会议ID | id | integer | 正整数 | 唯一标识 |
| 会议状态 | status | enum | planned/ongoing/done/cancelled | 当前状态 |
| 会议纪要 | summary | string | 文本 | AI生成的摘要 |
| 分享令牌 | share_token | string | 64位随机字符串 | 用于匿名访问 |
| 创建时间 | created_at | datetime | ISO8601 | 记录创建时间 |

#### 4.2.6 算法

**分享令牌生成**：
```python
share_token = secrets.token_urlsafe(48)  # 64字符
```

**会议状态流转**：
```
planned → ongoing → done
   │         │
   └────────► cancelled
```

#### 4.2.7 流程逻辑

**会议创建流程**：
```
用户请求创建会议
       │
       ▼
┌─────────────┐
│ 权限校验     │◄── 验证用户身份
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 数据验证     │◄── 校验必填字段、时间范围
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 创建会议记录 │◄── 插入 meetings 表
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 添加组织者   │◄── 自动添加参与者记录
│ 为参与者     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 返回结果     │
└─────────────┘
```

**AI后处理流程**：
```
触发后处理请求
       │
       ▼
┌─────────────┐
│ 权限检查     │◄── 仅组织者或管理员可操作
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 获取转写内容 │◄── 查询 meeting_transcripts
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 调用LLM服务  │◄── 生成摘要
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 提取任务     │◄── 从摘要中识别任务
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 保存结果     │◄── 更新会议、创建任务
└─────────────┘
```

#### 4.2.8 接口

| 接口名称 | 方法 | 路径 | 认证 | 说明 |
|----------|------|------|------|------|
| list_meetings | GET | /api/v1/meetings | 是 | 获取会议列表 |
| create_meeting | POST | /api/v1/meetings | 是 | 创建会议 |
| get_meeting | GET | /api/v1/meetings/{id} | 是 | 获取会议详情 |
| update_meeting | PATCH | /api/v1/meetings/{id} | 是 | 更新会议 |
| delete_meeting | DELETE | /api/v1/meetings/{id} | 是 | 删除会议 |
| postprocess | POST | /api/v1/meetings/{id}/postprocess | 是 | AI后处理 |
| upload_audio | POST | /api/v1/meetings/{id}/audio | 是 | 上传音频 |
| share | POST | /api/v1/meetings/{id}/share | 是 | 生成分享链接 |
| get_shared | GET | /api/v1/share/{token} | 否 | 通过分享链接查看 |

### 4.3 程序(模块)3：任务模块 (M05)

#### 4.3.1 模块描述

任务模块负责任务的全生命周期管理，包括任务的自动提取、创建、分配、状态更新和追踪。

#### 4.3.2 功能

- 任务CRUD操作
- 任务状态流转（todo → in_progress → done）
- 优先级管理（high/medium/low）
- 任务分配与指派
- 从会议纪要自动提取任务

#### 4.3.3 状态流转

```
        开始执行
    ┌────────────►
    │             │
┌───┴───┐     ┌───┴───────┐
│  todo │────►│in_progress│
└───┬───┘     └───┬───────┘
    │             │
    │ 直接完成     │ 完成
    └────────────►│
                  ▼
            ┌─────────┐
            │  done   │
            └─────────┘
```

**流转规则**：
- todo → in_progress：执行人开始处理
- todo → done：任务直接完成
- in_progress → done：任务处理完成
- 禁止反向流转（done 不可回到前序状态）

#### 4.3.4 接口

| 接口名称 | 方法 | 路径 | 说明 |
|----------|------|------|------|
| list_tasks | GET | /api/v1/tasks | 获取任务列表 |
| create_task | POST | /api/v1/tasks | 创建任务 |
| get_task | GET | /api/v1/tasks/{id} | 获取任务详情 |
| update_task | PATCH | /api/v1/tasks/{id} | 更新任务 |
| delete_task | DELETE | /api/v1/tasks/{id} | 删除任务 |

---

## 5. 数据库设计

### 5.1 逻辑结构设计

#### 5.1.1 E-R 图

```
┌─────────────────────────────────────────────────────────────────┐
│                           实体关系图                              │
└─────────────────────────────────────────────────────────────────┘

   ┌──────────────┐         ┌──────────────┐         ┌──────────────┐
   │    users     │         │   meetings   │         │    tasks     │
   ├──────────────┤         ├──────────────┤         ├──────────────┤
   │ PK id        │◄───────►│ PK id        │◄───────►│ PK id        │
   │    username  │  组织   │ FK organizer │  包含   │ FK meeting   │
   │    email     │         │    title     │         │ FK assignee  │
   │    role      │         │    status    │         │    title     │
   └──────────────┘         └───────┬──────┘         │    status    │
          ▲                         │                └──────────────┘
          │                         │
          │                  ┌──────┴──────┐
          │                  │             │
          ▼                  ▼             ▼
   ┌──────────────┐   ┌──────────────┐  ┌──────────────┐
   │    teams     │   │   transcripts│  │ participants │
   ├──────────────┤   ├──────────────┤  ├──────────────┤
   │ PK id        │   │ PK id        │  │ PK id        │
   │    name      │   │ FK meeting   │  │ FK meeting   │
   │    is_public │   │    content   │  │ FK user      │
   └───────┬──────┘   │    segment   │  │    role      │
           │          └──────────────┘  └──────────────┘
           │
           │     ┌──────────────┐
           └───► │ team_members │
                 ├──────────────┤
                 │ PK id        │
                 │ FK team      │
                 │ FK user      │
                 │    role      │
                 └──────────────┘
```

#### 5.1.2 实体描述

| 实体名称 | 中文名称 | 描述 | 主键 |
|----------|----------|------|------|
| users | 用户 | 系统注册用户 | id |
| meetings | 会议 | 会议基本信息 | id |
| meeting_transcripts | 会议转写 | 语音转写文本分段 | id |
| tasks | 任务 | 会议衍生的任务 | id |
| teams | 团队 | 协作团队 | id |
| team_members | 团队成员 | 团队与用户的关联 | id |
| team_invitations | 团队邀请 | 团队邀请记录 | id |
| meeting_participants | 会议参与者 | 会议与用户的关联 | id |
| audit_logs | 审计日志 | 操作审计记录 | id |

### 5.2 物理结构设计

#### 5.2.1 表结构设计

**表 1：users（用户表）**

| 字段名 | 数据类型 | 长度 | 是否可空 | 默认值 | 约束 | 说明 |
|--------|----------|------|----------|--------|------|------|
| id | BIGINT UNSIGNED | - | 否 | AUTO_INCREMENT | PK | 用户唯一标识 |
| username | VARCHAR | 50 | 否 | - | UNIQUE | 用户名 |
| email | VARCHAR | 120 | 否 | - | UNIQUE | 邮箱地址 |
| password_hash | VARCHAR | 255 | 否 | - | - | 密码哈希值 |
| full_name | VARCHAR | 100 | 否 | - | - | 真实姓名 |
| role | ENUM | - | 否 | 'member' | - | 用户角色(admin/member) |
| is_active | TINYINT | 1 | 否 | 1 | - | 账号状态(1=激活) |
| last_login_at | DATETIME | - | 是 | NULL | - | 最后登录时间 |
| created_at | DATETIME | - | 否 | CURRENT_TIMESTAMP | - | 创建时间 |
| updated_at | DATETIME | - | 否 | CURRENT_TIMESTAMP | ON UPDATE | 更新时间 |

**索引**：
- PRIMARY KEY (id)
- UNIQUE INDEX uk_users_username (username)
- UNIQUE INDEX uk_users_email (email)
- INDEX idx_users_role (role)

---

**表 2：meetings（会议表）**

| 字段名 | 数据类型 | 长度 | 是否可空 | 默认值 | 约束 | 说明 |
|--------|----------|------|----------|--------|------|------|
| id | BIGINT UNSIGNED | - | 否 | AUTO_INCREMENT | PK | 会议唯一标识 |
| title | VARCHAR | 200 | 否 | - | - | 会议标题 |
| description | TEXT | - | 是 | NULL | - | 会议描述 |
| organizer_id | BIGINT UNSIGNED | - | 否 | - | FK | 组织者ID |
| team_id | BIGINT UNSIGNED | - | 是 | NULL | FK | 所属团队ID |
| scheduled_start_at | DATETIME | - | 是 | NULL | - | 计划开始时间 |
| scheduled_end_at | DATETIME | - | 是 | NULL | - | 计划结束时间 |
| actual_start_at | DATETIME | - | 是 | NULL | - | 实际开始时间 |
| actual_end_at | DATETIME | - | 是 | NULL | - | 实际结束时间 |
| location | VARCHAR | 255 | 是 | NULL | - | 会议地点/链接 |
| status | ENUM | - | 否 | 'planned' | - | 会议状态 |
| summary | TEXT | - | 是 | NULL | - | 会议纪要摘要 |
| share_token | VARCHAR | 64 | 是 | NULL | UNIQUE | 分享令牌 |
| shared_at | DATETIME | - | 是 | NULL | - | 分享时间 |
| postprocessed_at | DATETIME | - | 是 | NULL | - | AI处理时间 |
| postprocess_version | VARCHAR | 32 | 是 | NULL | - | 处理版本标识 |
| created_at | DATETIME | - | 否 | CURRENT_TIMESTAMP | - | 创建时间 |
| updated_at | DATETIME | - | 否 | CURRENT_TIMESTAMP | ON UPDATE | 更新时间 |

**索引**：
- PRIMARY KEY (id)
- FOREIGN KEY (organizer_id) REFERENCES users(id)
- FOREIGN KEY (team_id) REFERENCES teams(id)
- INDEX idx_meetings_organizer_id (organizer_id)
- INDEX idx_meetings_status (status)
- INDEX idx_meetings_scheduled_start_at (scheduled_start_at)
- UNIQUE INDEX uk_meetings_share_token (share_token)

---

**表 3：meeting_transcripts（会议转写表）**

| 字段名 | 数据类型 | 长度 | 是否可空 | 默认值 | 约束 | 说明 |
|--------|----------|------|----------|--------|------|------|
| id | BIGINT UNSIGNED | - | 否 | AUTO_INCREMENT | PK | 转写记录ID |
| meeting_id | BIGINT UNSIGNED | - | 否 | - | FK | 所属会议ID |
| speaker_user_id | BIGINT UNSIGNED | - | 是 | NULL | FK | 发言用户ID |
| speaker_name | VARCHAR | 100 | 是 | NULL | - | 发言人名称 |
| segment_index | INT UNSIGNED | - | 否 | - | - | 片段序号 |
| start_time_sec | DECIMAL | (10,3) | 是 | NULL | - | 开始秒数 |
| end_time_sec | DECIMAL | (10,3) | 是 | NULL | - | 结束秒数 |
| language_code | VARCHAR | 10 | 否 | 'zh-CN' | - | 语言代码 |
| source | ENUM | - | 否 | 'whisper' | - | 来源类型 |
| content | LONGTEXT | - | 否 | - | - | 转写文本内容 |
| created_at | DATETIME | - | 否 | CURRENT_TIMESTAMP | - | 创建时间 |
| updated_at | DATETIME | - | 否 | CURRENT_TIMESTAMP | ON UPDATE | 更新时间 |

**索引**：
- PRIMARY KEY (id)
- FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
- FOREIGN KEY (speaker_user_id) REFERENCES users(id)
- UNIQUE INDEX uk_transcripts_meeting_segment (meeting_id, segment_index)
- INDEX idx_transcripts_meeting_id (meeting_id)

---

**表 4：tasks（任务表）**

| 字段名 | 数据类型 | 长度 | 是否可空 | 默认值 | 约束 | 说明 |
|--------|----------|------|----------|--------|------|------|
| id | BIGINT UNSIGNED | - | 否 | AUTO_INCREMENT | PK | 任务唯一标识 |
| meeting_id | BIGINT UNSIGNED | - | 否 | - | FK | 来源会议ID |
| transcript_id | BIGINT UNSIGNED | - | 是 | NULL | FK | 来源转写ID |
| title | VARCHAR | 200 | 否 | - | - | 任务标题 |
| description | TEXT | - | 是 | NULL | - | 任务描述 |
| assignee_id | BIGINT UNSIGNED | - | 是 | NULL | FK | 执行人ID |
| reporter_id | BIGINT UNSIGNED | - | 是 | NULL | FK | 创建人ID |
| priority | ENUM | - | 否 | 'medium' | - | 优先级 |
| status | ENUM | - | 否 | 'todo' | - | 任务状态 |
| due_at | DATETIME | - | 是 | NULL | - | 截止时间 |
| completed_at | DATETIME | - | 是 | NULL | - | 完成时间 |
| created_at | DATETIME | - | 否 | CURRENT_TIMESTAMP | - | 创建时间 |
| updated_at | DATETIME | - | 否 | CURRENT_TIMESTAMP | ON UPDATE | 更新时间 |

**索引**：
- PRIMARY KEY (id)
- FOREIGN KEY (meeting_id) REFERENCES meetings(id)
- FOREIGN KEY (transcript_id) REFERENCES meeting_transcripts(id)
- FOREIGN KEY (assignee_id) REFERENCES users(id)
- FOREIGN KEY (reporter_id) REFERENCES users(id)
- INDEX idx_tasks_meeting_id (meeting_id)
- INDEX idx_tasks_assignee_id (assignee_id)
- INDEX idx_tasks_status (status)
- INDEX idx_tasks_due_at (due_at)

---

**表 5：teams（团队表）**

| 字段名 | 数据类型 | 长度 | 是否可空 | 默认值 | 约束 | 说明 |
|--------|----------|------|----------|--------|------|------|
| id | BIGINT UNSIGNED | - | 否 | AUTO_INCREMENT | PK | 团队唯一标识 |
| name | VARCHAR | 100 | 否 | - | - | 团队名称 |
| description | TEXT | - | 是 | NULL | - | 团队描述 |
| owner_id | BIGINT UNSIGNED | - | 否 | - | FK | 创建者ID |
| is_public | TINYINT | 1 | 否 | 0 | - | 是否公开 |
| max_members | INT | - | 否 | 50 | - | 最大成员数 |
| created_at | DATETIME | - | 否 | CURRENT_TIMESTAMP | - | 创建时间 |
| updated_at | DATETIME | - | 否 | CURRENT_TIMESTAMP | ON UPDATE | 更新时间 |

---

**表 6：team_members（团队成员表）**

| 字段名 | 数据类型 | 长度 | 是否可空 | 默认值 | 约束 | 说明 |
|--------|----------|------|----------|--------|------|------|
| id | BIGINT UNSIGNED | - | 否 | AUTO_INCREMENT | PK | 记录ID |
| team_id | BIGINT UNSIGNED | - | 否 | - | FK | 团队ID |
| user_id | BIGINT UNSIGNED | - | 否 | - | FK | 用户ID |
| role | ENUM | - | 否 | 'member' | - | 成员角色 |
| joined_at | DATETIME | - | 否 | CURRENT_TIMESTAMP | - | 加入时间 |

**唯一约束**：(team_id, user_id)

---

**表 7：team_invitations（团队邀请表）**

| 字段名 | 数据类型 | 长度 | 是否可空 | 默认值 | 约束 | 说明 |
|--------|----------|------|----------|--------|------|------|
| id | BIGINT UNSIGNED | - | 否 | AUTO_INCREMENT | PK | 邀请记录ID |
| team_id | BIGINT UNSIGNED | - | 否 | - | FK | 团队ID |
| inviter_id | BIGINT UNSIGNED | - | 否 | - | FK | 邀请人ID |
| invitee_email | VARCHAR | 120 | 否 | - | - | 被邀请人邮箱 |
| status | ENUM | - | 否 | 'pending' | - | 邀请状态 |
| token | VARCHAR | 64 | 是 | NULL | UNIQUE | 邀请令牌 |
| created_at | DATETIME | - | 否 | CURRENT_TIMESTAMP | - | 创建时间 |
| responded_at | DATETIME | - | 是 | NULL | - | 响应时间 |

---

**表 8：meeting_participants（会议参与者表）**

| 字段名 | 数据类型 | 长度 | 是否可空 | 默认值 | 约束 | 说明 |
|--------|----------|------|----------|--------|------|------|
| id | BIGINT UNSIGNED | - | 否 | AUTO_INCREMENT | PK | 记录ID |
| meeting_id | BIGINT UNSIGNED | - | 否 | - | FK | 会议ID |
| user_id | BIGINT UNSIGNED | - | 否 | - | FK | 用户ID |
| role | ENUM | - | 否 | 'participant' | - | 参与者角色 |
| joined_at | DATETIME | - | 否 | CURRENT_TIMESTAMP | - | 加入时间 |

**唯一约束**：(meeting_id, user_id)

---

**表 9：audit_logs（审计日志表）**

| 字段名 | 数据类型 | 长度 | 是否可空 | 默认值 | 约束 | 说明 |
|--------|----------|------|----------|--------|------|------|
| id | BIGINT UNSIGNED | - | 否 | AUTO_INCREMENT | PK | 日志ID |
| actor_user_id | BIGINT UNSIGNED | - | 是 | NULL | FK | 操作用户ID |
| entity_type | VARCHAR | 50 | 否 | - | - | 实体类型 |
| entity_id | BIGINT UNSIGNED | - | 否 | - | - | 实体ID |
| action | VARCHAR | 50 | 否 | - | - | 操作类型 |
| details | JSON | - | 是 | NULL | - | 详细内容 |
| created_at | DATETIME | - | 否 | CURRENT_TIMESTAMP | - | 操作时间 |

### 5.3 数据字典

| 数据项 | 数据类型 | 取值范围 | 说明 |
|--------|----------|----------|------|
| user.role | ENUM | 'admin', 'member' | 用户角色 |
| meeting.status | ENUM | 'planned', 'ongoing', 'done', 'cancelled' | 会议状态 |
| task.status | ENUM | 'todo', 'in_progress', 'done' | 任务状态 |
| task.priority | ENUM | 'high', 'medium', 'low' | 任务优先级 |
| team_member.role | ENUM | 'owner', 'admin', 'member' | 团队成员角色 |
| participant.role | ENUM | 'organizer', 'participant' | 会议参与者角色 |
| invitation.status | ENUM | 'pending', 'accepted', 'rejected' | 邀请状态 |
| transcript.source | ENUM | 'whisper', 'manual', 'imported' | 转写来源 |

### 5.4 安全保密设计

#### 5.4.1 数据加密

- **密码存储**：使用 PBKDF2-SHA256 算法进行哈希，不存储明文
- **JWT Secret**：存储于环境变量，不提交到代码仓库
- **敏感字段**：API 响应中不返回 password_hash 等敏感字段

#### 5.4.2 访问控制

- **行级安全**：用户只能访问自己有权限的数据（通过 organizer_id, participant 等关联控制）
- **角色权限**：通过 role 字段区分 admin/member 权限

#### 5.4.3 SQL注入防护

- 使用 SQLAlchemy ORM，禁止直接拼接 SQL
- 所有用户输入通过参数化查询处理

---

## 6. 接口设计

### 6.1 用户接口

#### 6.1.1 界面风格

- **设计语言**：现代简约风格，采用 Element Plus 组件库
- **配色方案**：主色调蓝色(#409EFF)，辅助灰色系
- **响应式布局**：适配桌面端（1280px+）和平板端（768px+）

#### 6.1.2 界面要素

**导航结构**：
```
侧边栏导航
├── 仪表盘 (Dashboard)
├── 会议管理 (Meetings)
│   ├── 会议列表
│   └── 会议详情
├── 任务中心 (Tasks)
├── 团队管理 (Teams)
│   ├── 团队列表
│   └── 邀请管理
└── 系统设置 (Settings)
    └── 热词管理
```

### 6.2 外部接口

#### 6.2.1 软件接口

**OpenAI API 接口**：

| 接口地址 | 方法 | 用途 |
|----------|------|------|
| https://api.openai.com/v1/chat/completions | POST | LLM 摘要生成 |

**Ollama API 接口**（本地）：

| 接口地址 | 方法 | 用途 |
|----------|------|------|
| http://host.docker.internal:11434/api/generate | POST | 本地 LLM 调用 |

**Whisper 接口**（本地库）：
```python
import whisper
model = whisper.load_model("base")
result = model.transcribe("audio.mp3")
```

#### 6.2.2 硬件接口

- **文件系统**：音频文件存储于本地文件系统或对象存储
- **网络接口**：HTTP/HTTPS 协议通信

### 6.3 内部接口

#### 6.3.1 RESTful API 规范

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

#### 6.3.2 核心接口清单

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

---

## 7. 界面详细设计

### 7.1 结构

#### 7.1.1 界面结构图

```
SmartMeeting Frontend
│
├── 公共布局 (Layout)
│   ├── 侧边栏导航 (Sidebar)
│   ├── 顶部栏 (Header)
│   └── 主内容区 (Main Content)
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
    └── AppErrorAlert (错误提示)
```

#### 7.1.2 界面与模块关系表

| 界面名称 | 对应模块 | 说明 |
|----------|----------|------|
| LoginView | M01 认证模块 | 用户登录界面 |
| DashboardView | M03 会议模块, M05 任务模块 | 仪表盘展示 |
| MeetingListView | M03 会议模块 | 会议列表管理 |
| MeetingDetailView | M03 会议模块, M04 转写模块, M05 任务模块 | 会议详情工作台 |
| TasksView | M05 任务模块 | 任务中心 |
| TeamsView | M06 团队模块 | 团队管理 |
| InvitationsView | M06 团队模块 | 邀请管理 |

### 7.2 功能说明

#### 7.2.1 登录页 (LoginView)

**功能**：用户登录入口

**布局**：
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

**交互流程**：
1. 用户输入用户名/邮箱和密码
2. 前端进行基本格式校验
3. 调用 POST /api/v1/auth/login
4. 成功后存储 JWT token，跳转仪表盘
5. 失败显示错误提示

#### 7.2.2 仪表盘 (DashboardView)

**功能**：系统概览与快捷入口

**布局**：
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
└──────────┴──────────────────────────────────────────────┘
```

#### 7.2.3 会议详情页 (MeetingDetailView)

**功能**：会议内容管理的核心工作台

**布局**：
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

**标签页说明**：
- **会议纪要**：展示 AI 生成的会议摘要，支持重新生成
- **转写记录**：展示语音转写的分段文本，支持编辑
- **任务列表**：展示从会议提取的任务，支持增删改
- **参与者**：管理会议参与者，添加/移除人员
- **设置**：会议基本信息设置

### 7.3 用户界面设计规则

#### 7.3.1 命名规范

- **组件名**：PascalCase（如 `MeetingDetailView.vue`）
- **组合式函数**：camelCase 前缀 `use`（如 `useMeetingStore.ts`）
- **路由路径**：kebab-case（如 `/meeting-detail`）

#### 7.3.2 交互规范

- **表单提交**：显示加载状态，防止重复提交
- **删除操作**：二次确认对话框
- **错误提示**：全局错误处理，显示友好错误信息
- **成功提示**：操作成功后显示 Toast 提示

---

## 8. 系统出错处理设计

### 8.1 出错信息

| 错误代码 | 错误名称 | 错误说明 | 处理方式 |
|----------|----------|----------|----------|
| E001 | AUTH_INVALID_CREDENTIALS | 用户名或密码错误 | 提示用户重新输入 |
| E002 | AUTH_TOKEN_EXPIRED | Token 已过期 | 跳转到登录页重新登录 |
| E003 | AUTH_TOKEN_INVALID | Token 无效 | 跳转到登录页重新登录 |
| E004 | AUTH_FORBIDDEN | 权限不足 | 提示用户无权限 |
| E101 | MEETING_NOT_FOUND | 会议不存在 | 返回404错误页面 |
| E102 | MEETING_ALREADY_EXISTS | 会议已存在 | 提示用户修改标题 |
| E201 | VALIDATION_ERROR | 参数校验失败 | 返回具体校验错误信息 |
| E301 | DATABASE_ERROR | 数据库操作失败 | 记录日志，返回500错误 |
| E401 | LLM_SERVICE_ERROR | AI 服务调用失败 | 使用规则回退生成 |
| E501 | FILE_UPLOAD_ERROR | 文件上传失败 | 提示用户重新上传 |

### 8.2 补救措施

#### 8.2.1 数据库连接失败

- **现象**：应用无法连接数据库
- **处理**：
  1. 记录错误日志
  2. 返回503服务不可用
  3. 启动健康检查定时重连

#### 8.2.2 LLM 服务不可用

- **现象**：OpenAI/Ollama API 调用失败
- **处理**：
  1. 捕获异常，记录日志
  2. 自动切换到规则回退模式
  3. 基于关键词提取生成简单摘要

#### 8.2.3 文件上传失败

- **现象**：音频文件上传中断或失败
- **处理**：
  1. 清理临时文件
  2. 提示用户重新上传
  3. 支持断点续传（后续扩展）

### 8.3 系统维护设计

#### 8.3.1 日志管理

- **应用日志**：存储于日志文件，按日期轮转
- **审计日志**：存储于数据库 audit_logs 表
- **错误日志**：包含堆栈跟踪，便于排查问题

#### 8.3.2 监控告警

- **关键指标**：API 响应时间、错误率、数据库连接数
- **告警阈值**：错误率 > 5%，响应时间 P95 > 1s
- **告警方式**：邮件/企业微信（后续扩展）

---

## 9. 系统维护设计

### 9.1 程序(模块)的局部存储及随程序永久运行的数据

| 数据项 | 存储位置 | 说明 | 备份策略 |
|--------|----------|------|----------|
| JWT Secret | 环境变量 | 用于签名验证 | 配置管理系统存储 |
| 数据库连接池 | 内存 | SQLAlchemy 连接池 | 无需备份 |
| 热词缓存 | 内存 | 应用启动加载 | 从数据库重建 |
| 音频文件 | 文件系统 | 用户上传的录音 | 定期备份到对象存储 |

### 9.2 性能和精度

#### 9.2.1 性能设计

**数据库性能**：
- 所有外键字段建立索引
- 常用查询条件字段建立索引（status、created_at 等）
- 使用 joinedload 避免 N+1 查询

**缓存策略**：
- 热词列表应用启动时加载到内存
- 用户信息可短期缓存（后续扩展 Redis）

#### 9.2.2 精度设计

- **时间精度**：秒级（DATETIME）
- **音频时间**：毫秒级（DECIMAL(10,3)）
- **货币金额**：分（整数存储，后续扩展）

### 9.3 专用内存的设计

| 用途 | 大小 | 位置 | 说明 |
|------|------|------|------|
| 热词缓存 | ~10KB | 内存 | 热词数量 < 1000 |
| JWT Secret | ~32B | 内存 | 启动时从环境变量加载 |
| 数据库连接池 | 10-20连接 | 内存 | 最大并发连接数 |

### 9.4 覆盖处理

- **Session 覆盖**：JWT 无状态设计，不存在 Session 覆盖问题
- **缓存覆盖**：使用原子操作更新缓存
- **文件覆盖**：上传同名文件时生成唯一文件名

---

## 10. 附录

### 10.1 数据库迁移记录

| 版本 | 文件名 | 说明 | 日期 |
|------|--------|------|------|
| 001 | 001_init_smartmeeting.sql | 初始 schema | 2026-03 |
| 002 | 002_enhance_smartmeeting.sql | 增强字段 | 2026-03 |
| 003 | 003_sp_task_query.sql | 存储过程 | 2026-03 |
| 004 | 004_indexes_perf.sql | 性能索引 | 2026-03 |
| 005 | 005_audit_and_participants.sql | 审计与参与者 | 2026-03 |
| 006 | 006_collaboration_share_fields.sql | 协作分享 | 2026-03 |
| 007 | 007_create_team_invitations.sql | 团队邀请 | 2026-03 |
| ... | ... | ... | ... |
| 018 | 018_create_team_invite_links.sql | 邀请链接 | 2026-04 |

### 10.2 数据库表清单

| 表名 | 中文名 | 记录数(预估) | 说明 |
|------|--------|--------------|------|
| users | 用户表 | 1000 | 系统用户 |
| meetings | 会议表 | 10000 | 会议信息 |
| meeting_transcripts | 会议转写表 | 100000 | 转写文本分段 |
| tasks | 任务表 | 50000 | 任务记录 |
| teams | 团队表 | 100 | 团队信息 |
| team_members | 团队成员表 | 500 | 团队-用户关联 |
| team_invitations | 团队邀请表 | 500 | 邀请记录 |
| meeting_participants | 会议参与者表 | 50000 | 会议-用户关联 |
| audit_logs | 审计日志表 | 1000000 | 操作日志 |

### 10.3 缩略语清单

| 缩略语 | 英文全称 | 中文说明 |
|--------|----------|----------|
| JWT | JSON Web Token | JSON网络令牌 |
| ORM | Object-Relational Mapping | 对象关系映射 |
| ASR | Automatic Speech Recognition | 自动语音识别 |
| LLM | Large Language Model | 大语言模型 |
| REST | Representational State Transfer | 表述性状态转移 |
| API | Application Programming Interface | 应用程序接口 |
| SQL | Structured Query Language | 结构化查询语言 |
| CRUD | Create, Read, Update, Delete | 增删改查 |
| CI/CD | Continuous Integration/Deployment | 持续集成/部署 |
| PK | Primary Key | 主键 |
| FK | Foreign Key | 外键 |
| UI | User Interface | 用户界面 |

### 10.4 引用文档清单

1. 《SmartMeeting 智能会议系统项目立项规划书》
2. 《SmartMeeting 软件需求规格说明书 SRS》
3. GB/T 8567-2006《计算机软件文档编制规范》
4. GB/T 25000.51-2016《系统与软件工程 系统与软件质量要求和评价》
5. IEEE 1016-2009《软件设计描述标准》

---

## 文档结束

---

**本文档依据 GB/T 8567-2006《计算机软件文档编制规范》编制**

**编制单位**：SmartMeeting 开发团队  
**编制日期**：2026年4月6日

*本文档版权归 SmartMeeting 开发团队所有*
