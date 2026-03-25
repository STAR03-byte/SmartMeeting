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
  - 在线录音（麦克风）：开始录音 / 暂停录音 / 继续录音 / 停止并转写
  - 触发后处理（摘要+任务）
  - 查看转写列表与任务列表

#### 3.2.1 在线录音使用说明

1. 进入会议详情页，点击“开始录音”。
2. 浏览器首次会请求麦克风权限，允许后进入“录音中”。
3. 可根据需要点击“暂停录音”与“继续录音”。
4. 点击“停止并转写”后，系统会自动：
   - 将录音文件上传到当前会议
   - 触发后端转写流程
   - 刷新转写与任务数据

限制说明：

- 首版仅支持麦克风输入（不含系统音）。
- 录音能力依赖浏览器 `MediaRecorder` 与 `getUserMedia` 支持。
- 若权限被拒绝，会提示“无法访问麦克风，请检查浏览器权限”。

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
