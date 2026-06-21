# AI Offer 薪酬决策引擎

面向企业招聘场景的 AI Offer 薪酬决策系统 MVP。项目提供候选人管理、市场薪资维护、薪酬策略配置、Offer 推荐、预算与风险评估、薪酬公平性检查、接受率预测、模型注册与治理、异步任务调度、报告生成以及前端工作台。

## 项目能力

- FastAPI 后端服务
- React + Vite + TypeScript 前端工作台
- SQLAlchemy 数据模型与 Alembic 迁移
- 候选人管理 API
- 组织、部门、岗位基础数据 API
- 市场薪资快照管理 API
- 员工薪资与薪酬公平性 API
- 薪酬策略与 CR 计算
- Offer 推荐、保存、查询与结果回填
- 预算控制与综合风险评估
- Offer Markdown 报告生成
- 接受率预测模块
- 模型版本注册、激活、验证、训练、回滚与治理审计
- Celery Worker、Beat 和任务状态查询
- 本地 SQLite 开发数据库
- Redis 支持的异步任务部署
- Docker Compose 本地全栈部署
- 后端单元测试与集成测试
- 前端 Vitest 测试配置

## 技术栈

### 后端

- Python `>=3.12`
- FastAPI
- Uvicorn
- SQLAlchemy 2.x
- Alembic
- Celery
- Redis
- Pydantic Settings
- Pytest

### 前端

- React 18
- TypeScript
- Vite
- React Router
- Ant Design
- Tailwind CSS
- Zustand
- ECharts
- Vitest
- React Testing Library

## 目录结构

```text
.
├── apps
│   ├── api                 # FastAPI 入口与路由
│   └── worker              # Celery 应用与异步任务
├── artifacts               # 模型 artifact 示例与导出产物
├── deployments
│   ├── compose             # Docker Compose 配置
│   └── docker              # API、Worker、Frontend 镜像配置
├── frontend                # React 前端项目
├── migrations              # Alembic 数据库迁移
├── scripts                 # Demo 数据与模型导出脚本
├── src
│   ├── modules             # 业务领域模块
│   └── shared              # 配置、数据库、异常处理等公共能力
├── tests                   # 后端测试
├── alembic.ini
├── pyproject.toml
└── README.md
```

## 环境要求

- Python `3.12+`
- Node.js `22+`，建议使用 `corepack` 管理 `pnpm`
- pnpm
- Docker 与 Docker Compose，可选

## 后端本地开发

在项目根目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .[dev]
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe scripts\seed_demo_data.py
.\.venv\Scripts\python.exe -m uvicorn apps.api.main:app --reload
```

启动后访问：

- API 文档：`http://127.0.0.1:8000/docs`
- OpenAPI JSON：`http://127.0.0.1:8000/api/v1/openapi.json`

`seed_demo_data.py` 会写入组织、部门、岗位、市场薪资、薪酬策略、候选人以及历史 Offer 标签数据，便于本地演示推荐与模型训练流程。

## 前端本地开发

```powershell
cd frontend
pnpm install
pnpm dev --host 127.0.0.1 --port 5173
```

访问：

- 前端工作台：`http://127.0.0.1:5173`
- 数据维护页：`http://127.0.0.1:5173/data-hub`
- Offer 管理页：`http://127.0.0.1:5173/offers`
- 模型治理页：`http://127.0.0.1:5173/governance`
- 任务控制台：`http://127.0.0.1:5173/tasks`

前端开发服务器会通过 `vite.config.ts` 将 `/api` 代理到 `http://127.0.0.1:8000`。

## 一键 Docker Compose 启动

```powershell
docker compose -f deployments\compose\docker-compose.local.yml up --build
```

启动后访问：

- 前端：`http://127.0.0.1:3000`
- API 文档：`http://127.0.0.1:8000/docs`

Compose 包含以下服务：

- `frontend`：Nginx 托管前端静态资源，并代理 `/api`
- `api`：FastAPI 服务
- `worker`：Celery Worker
- `beat`：Celery Beat 定时任务
- `redis`：Celery broker/result backend

Compose 会覆盖本地默认的 Celery eager 配置，使用 Redis 执行真实异步任务。API、Worker、Beat 会共享 SQLite 数据卷与模型 artifact 数据卷。

## 环境变量

示例配置位于 `.env.example`。

| 变量 | 默认值 | 说明 |
|---|---|---|
| `APP_NAME` | `AI Offer Compensation Decision Engine` | 应用名称 |
| `APP_ENV` | `local` | 运行环境 |
| `API_PREFIX` | `/api/v1` | API 路由前缀 |
| `DATABASE_URL` | `sqlite:///./offer_engine.db` | 数据库连接地址 |
| `CELERY_BROKER_URL` | `memory://` | Celery broker 地址 |
| `CELERY_RESULT_BACKEND` | `cache+memory://` | Celery 结果后端 |
| `CELERY_TASK_ALWAYS_EAGER` | `true` | 是否同步执行任务 |
| `CELERY_TASK_STORE_EAGER_RESULT` | `true` | eager 模式下是否保存结果 |
| `MARKET_SYNC_SCHEDULE_MINUTES` | `30` | 市场同步任务间隔 |
| `CORS_ALLOW_ORIGINS` | `http://127.0.0.1:5173,http://localhost:5173` | 允许跨域访问的前端来源 |

## 数据库迁移

升级到最新版本：

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

查看当前版本：

```powershell
.\.venv\Scripts\python.exe -m alembic current
```

Alembic 会读取应用的 `DATABASE_URL`，确保迁移和应用使用同一个数据库配置。

## 运行 Worker 和 Beat

本地默认配置下 Celery 使用 eager/memory 模式，便于测试。若要使用真实异步队列，请配置 Redis，并设置：

```powershell
$env:CELERY_BROKER_URL="redis://127.0.0.1:6379/0"
$env:CELERY_RESULT_BACKEND="redis://127.0.0.1:6379/1"
$env:CELERY_TASK_ALWAYS_EAGER="false"
```

启动 Worker：

```powershell
.\.venv\Scripts\python.exe -m celery -A apps.worker.celery_app:celery_app worker -l info
```

启动 Beat：

```powershell
.\.venv\Scripts\python.exe -m celery -A apps.worker.celery_app:celery_app beat -l info
```

## 模型注册与 Artifact

默认模型族：`baseline-offer-acceptance`

内置和示例 artifact：

- `artifacts/acceptance_prediction/baseline-offer-acceptance-0.3.0.json`
- `artifacts/acceptance_prediction/baseline-offer-acceptance-0.3.0.pkl`
- `artifacts/acceptance_prediction/baseline-offer-acceptance-0.4.0.json`
- `artifacts/acceptance_prediction/baseline-offer-acceptance-0.4.0.pkl`
- `artifacts/acceptance_prediction/baseline-offer-acceptance-0.5.0.json`
- `artifacts/acceptance_prediction/baseline-offer-acceptance-0.5.0.pkl`
- `artifacts/acceptance_prediction/baseline-offer-acceptance-0.6.0.json`
- `artifacts/acceptance_prediction/baseline-offer-acceptance-0.6.0.pkl`
- `artifacts/acceptance_prediction/baseline-offer-acceptance-0.7.0.json`
- `artifacts/acceptance_prediction/baseline-offer-acceptance-0.7.0.pkl`

模型注册字段包括：

- `framework`
- `artifactUri`
- `config`
- `metrics`

Offer 推荐会通过模型注册服务加载当前激活版本。模型验证接口会检查 artifact 运行时元数据，并返回 `loadedRuntime`。

## 导出模型 Artifact

从内置 demo 数据导出：

```powershell
.\.venv\Scripts\python.exe scripts\export_acceptance_model_artifact.py --source demo --model-version 0.7.0
```

从数据库中已完成的 Offer 结果导出：

```powershell
.\.venv\Scripts\python.exe scripts\export_acceptance_model_artifact.py --source db --model-version 0.6.0
```

导出命令会生成标准 JSON manifest 和 pickle 模型文件。manifest 包含运行时元数据、指标摘要和训练数据摘要。

## 训练模型任务

```powershell
curl -Method POST http://127.0.0.1:8000/api/v1/tasks/models/train `
  -ContentType "application/json" `
  -Body '{"modelName":"baseline-offer-acceptance","framework":"xgboost","source":"demo","activationMode":"if_better","operator":"ml-ops"}'
```

说明：

- `modelVersion` 可选，未传时自动生成下一个 patch 版本
- `activationMode=always`：始终激活新版本
- `activationMode=if_better`：基于 `trainingAccuracy` 和 `trainingLogLoss` 与当前激活版本比较后决定是否激活
- `activationMode=never`：只注册，不激活
- `operator` 会写入治理时间线，用于审计
- 可通过 `GET /api/v1/tasks/{task_id}` 查询任务状态

## 模型训练审计与回滚

查询训练记录：

```powershell
curl "http://127.0.0.1:8000/api/v1/models/training-runs?modelName=baseline-offer-acceptance"
```

查询治理事件：

```powershell
curl "http://127.0.0.1:8000/api/v1/models/governance-events?modelName=baseline-offer-acceptance&eventType=ROLLBACK&operator=risk-officer"
```

查询治理告警：

```powershell
curl "http://127.0.0.1:8000/api/v1/models/governance-alerts?modelName=baseline-offer-acceptance&operator=risk-officer"
```

同步回滚：

```powershell
curl -Method POST http://127.0.0.1:8000/api/v1/models/rollback `
  -ContentType "application/json" `
  -Body '{"modelName":"baseline-offer-acceptance","operator":"risk-officer"}'
```

审批待处理回滚事件：

```powershell
curl -Method POST http://127.0.0.1:8000/api/v1/models/governance-events/{eventId}/review `
  -ContentType "application/json" `
  -Body '{"action":"APPROVE","reviewer":"director","comment":"Approved after governance review.","approvalTicket":"APR-2001"}'
```

治理逻辑说明：

- 高风险回滚请求缺少 `approvalTicket` 时会被写入 `PENDING` 治理事件，不会立即执行
- `APPROVE` 必须提供 `approvalTicket`
- 审批通过会执行回滚并写入审计字段
- 审批拒绝会保留当前激活模型
- 过期待审批事件可批量标记为 `EXPIRED`
- 回滚目标必须处于受保护版本窗口内

## 任务接口示例

异步回滚：

```powershell
curl -Method POST http://127.0.0.1:8000/api/v1/tasks/models/rollback `
  -ContentType "application/json" `
  -Body '{"modelName":"baseline-offer-acceptance","operator":"risk-officer"}'
```

批量过期待审批事件：

```powershell
curl -Method POST http://127.0.0.1:8000/api/v1/tasks/models/governance-expire-pending `
  -ContentType "application/json" `
  -Body '{"modelName":"baseline-offer-acceptance","operator":"governance-bot","limit":50}'
```

治理告警扫描：

```powershell
curl -Method POST http://127.0.0.1:8000/api/v1/tasks/models/governance-alert-scan `
  -ContentType "application/json" `
  -Body '{"modelName":"baseline-offer-acceptance","operator":"risk-officer","limit":50}'
```

治理通知：

```powershell
curl -Method POST http://127.0.0.1:8000/api/v1/tasks/models/governance-alerts/notify `
  -ContentType "application/json" `
  -Body '{"modelName":"baseline-offer-acceptance","operator":"risk-officer","channel":"webhook-payload","destination":"https://notify.example.local/governance","limit":50}'
```

## 测试

后端测试：

```powershell
.\.venv\Scripts\python.exe -m pytest
```

前端测试与构建：

```powershell
cd frontend
pnpm install
pnpm test
pnpm build
```

如果本地 `frontend/node_modules` 损坏，可重新安装：

```powershell
cd frontend
Remove-Item -Recurse -Force .\node_modules
pnpm install --frozen-lockfile
pnpm test
pnpm build
```

## 常用 API

### 候选人与基础数据

- `POST /api/v1/candidates`
- `GET /api/v1/candidates?companyId=...&departmentId=...&positionId=...`
- `GET /api/v1/candidates/{candidate_id}`
- `GET /api/v1/org/companies`
- `GET /api/v1/org/departments?companyId=...`
- `GET /api/v1/org/positions?companyId=...`

### 薪酬与市场数据

- `POST /api/v1/compensation-strategies`
- `GET /api/v1/compensation-strategies?companyId=...`
- `GET /api/v1/compensation-strategies/{strategy_id}`
- `POST /api/v1/employee-salary`
- `GET /api/v1/employee-salary?companyId=...&departmentId=...&level=...`
- `POST /api/v1/market-salary`
- `GET /api/v1/market-salary?positionId=...&city=...`

### Offer

- `POST /api/v1/offers/recommend`
- `POST /api/v1/offers/recommend/by-candidate`
- `POST /api/v1/offers/recommend-and-save`
- `POST /api/v1/offers/{offer_id}/outcome`
- `GET /api/v1/offers?candidateId=...&strategyId=...&riskLevel=...`
- `GET /api/v1/offers/{offer_id}`
- `POST /api/v1/reports/offers/{offer_id}/generate`

### 模型与治理

- `GET /api/v1/models/versions?modelName=...`
- `GET /api/v1/models/active?modelName=...`
- `GET /api/v1/models/training-runs?modelName=...`
- `GET /api/v1/models/governance-events?modelName=...`
- `GET /api/v1/models/governance-alerts?modelName=...`
- `POST /api/v1/models/governance-alerts/notify`
- `POST /api/v1/models/register`
- `POST /api/v1/models/activate`
- `POST /api/v1/models/rollback`
- `POST /api/v1/models/governance-events/expire-pending`
- `POST /api/v1/models/governance-events/{event_id}/review`
- `POST /api/v1/models/validate`

### 任务

- `POST /api/v1/tasks/market-sync`
- `POST /api/v1/tasks/market-sync/batch`
- `POST /api/v1/tasks/models/train`
- `POST /api/v1/tasks/models/rollback`
- `POST /api/v1/tasks/models/governance-expire-pending`
- `POST /api/v1/tasks/models/governance-alert-scan`
- `POST /api/v1/tasks/models/governance-alerts/notify`
- `GET /api/v1/tasks/schedules`
- `GET /api/v1/tasks/{task_id}`

## 当前项目状态

该项目目前适合本地演示、MVP 验证和继续开发。项目已具备完整的核心业务链路、后端测试、前端页面、数据库迁移和本地全栈 Docker 部署能力。

生产化前建议继续补齐：

- 真实认证与授权
- 生产数据库，例如 PostgreSQL
- 真实市场薪资上游数据同步
- CI/CD 流水线
- 覆盖率报告
- 生产日志、监控与告警
- 更严格的安全配置与密钥管理
