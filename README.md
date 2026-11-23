# rain.api

**LogShield** 安全日志分析平台后端：提供用户注册登录（JWT 鉴权）、日志事件上报与查询、按级别统计与 24 小时趋势分析的 REST API。

## 功能列表

- 用户注册 / 登录，JWT 令牌鉴权，密码 bcrypt 哈希存储
- 日志事件创建、分页列表（支持按级别 / 来源筛选）、详情、删除
- 数据隔离：每个用户只能访问自己的日志
- 统计：按级别聚合计数、最近 24 小时逐小时趋势
- 健康检查端点与自动生成的接口文档（`/docs`）

## 技术栈

FastAPI · SQLAlchemy 2.0 · Pydantic v2 · python-jose（JWT）· passlib/bcrypt · pytest + TestClient · Docker

## 快速开始

### 本地运行（默认 SQLite，零配置）

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

启动后打开 http://127.0.0.1:8000/docs 即可在线调试全部接口。

调用示例：

```bash
# 注册并登录拿令牌
curl -X POST localhost:8000/api/auth/register -H 'Content-Type: application/json' \
  -d '{"username":"demo","email":"demo@example.com","password":"secret123"}'
TOKEN=$(curl -s -X POST localhost:8000/api/auth/login \
  -d 'username=demo&password=secret123' | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
# 上报一条日志并查看统计
curl -X POST localhost:8000/api/logs -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"level":"ERROR","source":"firewall","message":"blocked port scan"}'
curl localhost:8000/api/stats/summary -H "Authorization: Bearer $TOKEN"
```

### Docker Compose 运行（app + MySQL）

```bash
docker compose up --build
```

compose 会以 `DATABASE_URL=mysql+pymysql://...` 覆盖默认的 SQLite 连接串，应用代码无需任何改动。

### 运行测试

```bash
pip install -r requirements-dev.txt
pytest -q
```

## 接口清单

| 方法 | 路径 | 说明 | 鉴权 |
|---|---|---|---|
| GET | /health | 健康检查 | 否 |
| POST | /api/auth/register | 用户注册 | 否 |
| POST | /api/auth/login | 登录，返回 JWT | 否 |
| GET | /api/users/me | 当前用户信息 | 是 |
| POST | /api/logs | 创建日志事件 | 是 |
| GET | /api/logs | 分页列表，可按 level / source 筛选 | 是 |
| GET | /api/logs/{id} | 日志详情（仅本人） | 是 |
| DELETE | /api/logs/{id} | 删除日志（仅本人） | 是 |
| GET | /api/stats/summary | 按级别聚合计数 | 是 |
| GET | /api/stats/trend | 最近 24 小时逐小时趋势 | 是 |

## 项目结构

```
app/
├── main.py            # 应用入口：建表、挂载路由
├── api/               # 路由层：只做参数校验与响应组装
│   ├── auth.py  users.py  logs.py  stats.py
├── services/          # 业务逻辑层：用户与日志的实际处理
│   ├── users.py  log_events.py
├── models/            # SQLAlchemy ORM 模型
│   ├── user.py  log_event.py
├── schemas/           # Pydantic 请求/响应模型
│   ├── user.py  log_event.py  stats.py
└── core/              # 基础设施：配置、安全、依赖、数据库
    ├── config.py  security.py  deps.py  database.py
tests/                 # pytest 端到端测试（内存 SQLite 隔离）
```

## 设计要点

- **分层**：路由层只负责 HTTP 语义，业务规则集中在 services 层，数据访问由 SQLAlchemy 模型与会话承担；换接口形式或加新业务时互不牵扯。
- **鉴权**：登录后签发 JWT（HS256，24 小时过期），`get_current_user` 依赖统一解析令牌并加载用户；日志的详情与删除按 owner_id 过滤，他人资源一律返回 404，避免泄露资源存在性。
- **配置管理**：所有配置走 pydantic-settings 读取环境变量，数据库连接串、密钥、令牌有效期均可通过 `.env` 覆盖（见 `.env.example`）；默认 SQLite 开箱即跑，改一行连接串即可切换 MySQL，ORM 层无方言耦合。
- **测试隔离**：测试使用内存 SQLite + 依赖覆盖，每个用例前重建表，互不污染，也不触碰开发数据库。
