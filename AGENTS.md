# AGENTS.md - SmartMeeting 开发规范

## 项目概述

SmartMeeting 是一个智能会议管理系统，采用 **FastAPI + Vue3 + MySQL + Whisper + LLM** 技术栈。

## 目录结构

```
SmartMeeting/
├── backend/          # FastAPI 后端 (Python)
│   ├── app/
│   │   ├── api/      # API 路由
│   │   ├── models/   # Pydantic 模型
│   │   ├── services/ # 业务逻辑
│   │   └── utils/    # 工具函数
│   ├── main.py       # 入口文件
│   └── requirements.txt
├── frontend/         # Vue3 前端
│   ├── src/
│   │   ├── views/    # 页面
│   │   ├── components/ # 组件
│   │   ├── stores/   # Pinia 状态
│   │   └── api/      # 接口封装
│   └── package.json
├── database/         # 数据库脚本
└── docs/             # 文档
```

## 1. 构建与测试命令

### 后端 (Python/FastAPI)

```bash
# 安装依赖
cd backend
pip install -r requirements.txt

# 运行开发服务器
python -m uvicorn main:app --reload

# 运行单个测试
pytest tests/test_api.py::TestMeeting::test_create_meeting -v

# 运行所有测试
pytest

# 代码检查
flake8 app/ --max-line-length=100
ruff check app/
mypy app/

# 格式化
black app/
isort app/
```

### 前端 (Vue3/TypeScript)

```bash
# 安装依赖
cd frontend
npm install

# 开发模式
npm run dev

# 构建生产版本
npm run build

# 运行单元测试
npm run test:unit

# 运行单个测试文件
npm run test:unit -- tests/api/meeting.spec.ts

# Lint 检查
npm run lint
npm run lint:fix

# 类型检查
npm run typecheck
```

## 2. 代码规范

### 2.1 Python 后端

**命名规范**
- 模块/函数: `snake_case` (如 `get_meeting_list`)
- 类名: `PascalCase` (如 `MeetingService`)
- 常量: `UPPER_SNAKE_CASE` (如 `MAX_UPLOAD_SIZE`)
- 私有方法: `_private_method`

**类型注解**
```python
from typing import Optional, List

def get_meeting(id: int) -> Optional[Meeting]:
    ...

def create_meeting(data: CreateMeetingDTO) -> Meeting:
    ...
```

**错误处理**
```python
from fastapi import HTTPException

@app.get("/meetings/{id}")
async def get_meeting(id: int) -> Meeting:
    meeting = await service.get(id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting
```

**API 响应格式**
```python
from pydantic import BaseModel

class ApiResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[Any] = None
```

**Imports 顺序**
1. 标准库 (`from typing import ...`)
2. 第三方库 (`from fastapi import ...`)
3. 本地模块 (`from .models import ...`)

### 2.2 Vue3 前端

**命名规范**
- 组件文件: `PascalCase` (如 `MeetingList.vue`)
- 组合式函数: `useXxx.ts` (如 `useMeeting.ts)
- 工具函数: `camelCase` (如 `formatDate.ts)
- CSS 类: `kebab-case`

**TypeScript 类型**
```typescript
interface Meeting {
  id: number;
  title: string;
  createdAt: string;
}

const props = defineProps<{
  meetings: Meeting[];
}>();
```

**API 封装**
```typescript
// src/api/meeting.ts
import axios from './axios';

export const getMeetingList = (params: QueryParams) =>
  axios.get<ApiResponse<Meeting[]>>('/meetings', { params });
```

**组件编写**
```vue
<template>
  <div class="meeting-card">
    {{ meeting.title }}
  </div>
</template>

<script setup lang="ts">
interface Props {
  meeting: Meeting;
}

const props = defineProps<Props>();
</script>

<style scoped>
.meeting-card {
  padding: 16px;
}
</style>
```

**Pinia Store**
```typescript
// src/stores/meeting.ts
import { defineStore } from 'pinia';

export const useMeetingStore = defineStore('meeting', {
  state: () => ({
    meetings: [] as Meeting[],
  }),
  actions: {
    async fetchMeetings() {
      const res = await getMeetingList();
      this.meetings = res.data;
    },
  },
});
```

### 2.3 数据库

**表命名**: `snake_case` (如 `meeting_records`)
**字段命名**: `snake_case` (如 `created_at`)
**主键**: `id` (INT, 自增)
**时间戳**: `created_at`, `updated_at` (DATETIME)

### 2.4 Git 提交规范

```
feat: 新功能
fix: 修复 bug
docs: 文档更新
refactor: 重构
test: 测试
chore: 杂项

示例: feat(meeting): 添加会议创建接口
```

## 3. 开发注意事项

- 优先修改现有代码而非重新生成
- 保持工程结构规范
- 修改后立即提交并推送
- API 接口需有清晰的错误信息
- 前端组件保持单向数据流
- 敏感信息使用环境变量管理