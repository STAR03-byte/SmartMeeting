# SmartMeeting Frontend Runbook

## 1. 环境准备

- Node.js 18+
- 后端服务已启动: `python -m uvicorn backend.main:app --reload`

## 2. 安装与启动

推荐使用一条命令启动（仓库根目录执行）：

```bash
npm run dev
```

该命令会自动安装/更新依赖，并同时启动后端与前端。

如需手动分开启动：

```bash
npm --prefix frontend install --cache "D:\SmartMeeting\.npm-cache"
npm --prefix frontend run dev
```

- 默认前端地址: `http://127.0.0.1:5173`
- Vite 代理配置见: `frontend/vite.config.ts`
- 默认后端代理目标: `http://127.0.0.1:8000`
- 如后端运行在其他端口（例如 8888），启动前设置：`set SMARTMEETING_DEV_BACKEND_URL=http://127.0.0.1:8888`

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
  - 生成并复制会议分享链接
  - 查看转写列表与任务列表

#### 3.2.1 在线录音使用说明

1. 进入会议详情页，点击“开始录音”。
2. 浏览器首次会请求麦克风权限，允许后进入“录音中”。
3. 可根据需要点击“暂停录音”与“继续录音”。
4. 点击“停止并转写”后，系统会自动：
   - 将录音文件上传到当前会议
   - 触发后端转写流程
   - 刷新转写与任务数据

#### 3.2.2 会议分享链接

1. 先确保会议已生成摘要。
2. 在会议详情页点击“生成分享链接”。
3. 链接会自动复制到剪贴板，格式为 `/shared/meetings/{token}`。
4. 若接收者未登录，系统会先跳转登录页，登录成功后自动回到原分享页。
5. 分享页仅只读展示摘要、转写与任务。

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
