# SmartMeeting Frontend

Vue 3 + Vite + TypeScript + Pinia + Vue Router + Element Plus。

## 快速开始

```bash
npm --prefix frontend install --cache "D:\SmartMeeting\.npm-cache"
npm --prefix frontend run dev
```

默认地址：`http://127.0.0.1:5173`

## 入口

- `frontend/src/main.ts`：应用入口，挂载 Pinia、Router、Element Plus
- `frontend/src/router/index.ts`：路由与登录守卫
- `frontend/vite.config.ts`：Vite 代理与构建配置

## 页面路由

- `/`：仪表盘
- `/meetings`：会议列表
- `/meetings/:id`：会议详情
- `/tasks`：任务中心
- `/users`：用户管理
- `/login`：登录页

## 联调代理

Vite 代理：

- `/api` → `http://127.0.0.1:8000`
- `/health` → `http://127.0.0.1:8000`

## 常用命令

```bash
npm --prefix frontend run typecheck
npm --prefix frontend run build
npm --prefix frontend run preview
```

## API 说明

前端统一走 `src/api/`，请求拦截器会自动附加本地 token。

## 备注

- 组件库：Element Plus
- 状态管理：Pinia
- 请求封装：Axios
