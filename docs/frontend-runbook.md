# SmartMeeting Frontend Runbook

## 1. 环境准备

- Node.js 18+
- 后端服务已启动: `python -m uvicorn backend.main:app --reload`

## 2. 安装与启动

```bash
npm --prefix frontend install --cache "D:\SmartMeeting\.npm-cache"
npm --prefix frontend run dev
```

- 默认前端地址: `http://127.0.0.1:5173`
- Vite 代理配置见: `frontend/vite.config.ts`

## 3. 页面与联调流程

### 3.1 会议总览

- 路径: `/`
- 功能: 拉取会议列表，点击进入会议详情

### 3.2 会议详情

- 路径: `/meetings/{id}`
- 功能:
  - 上传音频并触发转写
  - 触发后处理（摘要+任务）
  - 查看转写列表与任务列表

## 4. 常见问题

### 4.1 上传接口报错 Form data requires python-multipart

- 后端缺依赖，执行:

```bash
python -m pip install -r backend/requirements.txt
```

### 4.2 npm install 权限错误（EPERM）

- 使用项目内缓存目录安装:

```bash
npm --prefix frontend install --cache "D:\SmartMeeting\.npm-cache"
```

### 4.3 Typecheck 报第三方库类型错误

- 当前前端 `tsconfig` 已启用 `skipLibCheck: true` 规避三方类型噪音

## 5. 验证命令

```bash
npm --prefix frontend run typecheck
npm --prefix frontend run build
pytest backend/tests/test_api.py -v
```
