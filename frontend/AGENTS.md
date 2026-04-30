# Frontend AGENTS.md

## OVERVIEW

`frontend/` 是 SmartMeeting 主前端（Vue 3 + TypeScript + Pinia + Vue Router + Axios）。

## STRUCTURE

```text
frontend/
├── src/
│   ├── api/         # API client + typed request wrappers
│   ├── components/  # 复用组件（当前规模小）
│   ├── router/      # 路由定义与页面映射
│   ├── stores/      # Pinia 状态管理
│   ├── views/       # 页面级组件
│   └── main.ts      # 应用入口（createApp/createPinia/router）
├── package.json
├── tsconfig.json
└── vite.config.ts
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| 新增 API 封装 | `src/api/*.ts` | 复用 `src/api/client.ts`，保持类型声明在 `types.ts` |
| 新增页面 | `src/views/*.vue` | 路由同步更新 `src/router/index.ts` |
| 调整全局状态 | `src/stores/*.ts` | 优先 Pinia，不在页面重复持久状态 |
| 联调接口 | `src/api/client.ts` | 统一错误处理与 baseURL 策略 |

## CONVENTIONS

### 通用
- 强制 `<script setup lang="ts">` + Composition API。
- 避免 `any`；props/emits/接口返回都要有类型。
- 业务 API 调用集中在 `src/api/`，页面层不直接拼接 URL。
- 路由集中在 `src/router/index.ts`，避免视图内硬编码导航规则。
- 构建前置类型检查（`vue-tsc --noEmit`）不可绕过。

### 视图层 (views/)
- 页面层职责是编排，不承载底层 HTTP 细节；请求优先经 `src/api/` 或 store action。
- 统一使用 `ElMessage` 做用户可见反馈，失败时输出可理解文案。
- 页面状态（loading/error/列表）优先复用 store，避免跨页面重复状态源。
- 大页面改动优先"拆小函数+保持流程顺序"，避免继续堆叠单函数复杂度。

### 组件层 (components/)
- 组件命名使用 PascalCase。
- 通用组件放 `common/`，业务组件按功能域分目录（`meeting/`, `ai/`, `workbench/`）。

## ANTI-PATTERNS

### 通用
- 直接在 `views` 里写大段请求逻辑并绕开 `src/api/`。
- 在组件内吞掉异常（空 `catch`）或只 `console.log` 不反馈。
- 使用未声明类型的跨组件共享状态（应落到 Pinia）。
- 跳过 `npm --prefix frontend run typecheck` 直接宣称可构建。

### 视图层
- 在 view 内直接 new axios 或手写后端 URL。
- 在多个页面复制同一业务流程（应下沉 store/api）。
- 修改页面流程后不验证关键路径（登录、会议详情、任务状态更新）。

### 组件层
- 组件内直接调用 API 而不通过 store 或 composable。
- 组件职责不单一，同时处理数据获取、业务逻辑和展示。

## COMMANDS

```bash
npm --prefix frontend install --cache "D:\SmartMeeting\.npm-cache"
npm --prefix frontend run dev
npm --prefix frontend run typecheck
npm --prefix frontend run build

# Tests
npx --prefix frontend vitest run
```
