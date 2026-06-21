# RAG Agent KB 部署说明

## 1. 部署方式说明

当前推荐使用 Docker Compose 部署前后端分离版本：

- backend：FastAPI 后端
- frontend：React/Vite 构建后由 Nginx 提供静态页面
- Nginx 负责把 `/api/` 请求反向代理到 `backend:8000`

## 2. 环境要求

- Docker
- Docker Compose
- 可用的 DeepSeek API Key
- 建议至少 10GB-20GB 可用磁盘空间
- 首次构建可能较慢

## 3. 配置环境变量

部署前先复制生产环境配置模板：

```bash
cp .env.production.example .env
```

然后根据实际部署环境修改 `.env`：

- 修改 `LLM_API_KEY`
- 修改 `DEEPSEEK_API_KEY`
- 修改 `JWT_SECRET_KEY`
- 根据部署地址修改 `ALLOWED_ORIGINS`

示例配置：

```env
LLM_PROVIDER=deepseek
LLM_BASE_URL=https://api.deepseek.com
LLM_API_KEY=your_api_key
LLM_MODEL=deepseek-chat
LLM_TEMPERATURE=0.2

EMBEDDING_PROVIDER=huggingface
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
EMBEDDING_DEVICE=cpu

HF_HOME=/app/.cache/huggingface

JWT_SECRET_KEY=replace_with_a_long_random_secret

ALLOWED_ORIGINS=http://localhost

DEEPSEEK_API_KEY=your_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

## 4. 启动服务

```bash
docker compose up -d --build
```

## 5. 查看运行状态

```bash
docker compose ps
```

正常情况下，`backend` 和 `frontend` 都应为 `Up`。

## 6. 访问地址

本地部署：

- 前端页面：http://localhost
- 后端健康检查：http://localhost/api/health

如果部署到服务器，则访问：

- http://服务器IP
- http://服务器IP/api/health

## 7. 默认账号

```text
username: admin
password: admin123
```

首次登录后应立即修改默认密码。

## 8. 常用运维命令

查看后端日志：

```bash
docker compose logs -f backend
```

查看前端日志：

```bash
docker compose logs -f frontend
```

停止服务：

```bash
docker compose down
```

重新构建并启动：

```bash
docker compose up -d --build
```

## 9. 数据持久化目录

`docker-compose.yml` 当前挂载了：

```yaml
./data:/app/data
./logs:/app/logs
./hf_cache:/app/.cache/huggingface
```

目录说明：

- data：SQLite 数据库、上传文件、清洗文件、知识库、Chroma 向量库
- logs：查询日志和审计日志
- hf_cache：HuggingFace Embedding 模型缓存

生产环境需要定期备份 `data` 和 `logs`。

## 10. 注意事项

- 当前版本适合单机部署
- 不建议直接多副本运行 backend，因为 SQLite、本地 Chroma、本地文件目录存在并发限制
- 如果后续要多用户大规模使用，建议迁移 PostgreSQL、对象存储、独立向量数据库
- 如果使用域名和 HTTPS，需要在外层配置 Nginx/Caddy/宝塔等反向代理
- 上传大文件时可调整 `frontend/nginx.conf` 里的 `client_max_body_size`

## Cloudflare Tunnel 公网访问

当前项目可以通过 Cloudflare Tunnel 暴露本地 Docker 服务。

公网访问地址示例：

```text
https://fany.dpdns.org
```

如果需要直接进入聊天页面，可以访问：

```text
https://fany.dpdns.org/#chat
```

推荐将 Cloudflare Tunnel 转发到本地 Docker 前端 Nginx：

```text
http://localhost:80
```

不要转发到 Vite 开发端口 `5173`，也不要单独转发后端 `8000`。

原因：

- Docker 版 frontend 容器已经通过 Nginx 提供静态页面
- Nginx 已经把 `/api/` 请求代理到 `backend:8000`
- 只暴露一个入口更简单
- 可以避免额外 CORS 问题

请求链路：

```text
用户浏览器
  -> Cloudflare
  -> Cloudflare Tunnel
  -> 本机 http://localhost:80
  -> frontend Nginx 容器
  -> React 前端页面
  -> /api/ 请求代理到 backend:8000
```

公网访问需要以下服务保持运行：

- 本机电脑开机并联网
- Docker Desktop 正常运行
- `docker compose` 服务正常运行
- Cloudflare Tunnel 正常运行
- 域名 `fany.dpdns.org` 已正确指向该 Tunnel

验证 Docker 服务状态：

```bash
docker compose ps
```

浏览器访问：

```text
http://localhost/api/health
```

应返回：

```json
{"status":"ok"}
```

公网访问：

```text
https://fany.dpdns.org/api/health
```

也应返回：

```json
{"status":"ok"}
```

常见问题：

- 如果 `http://localhost` 可以访问，但 `https://fany.dpdns.org` 不能访问，优先检查 Cloudflare Tunnel 是否运行
- 如果页面能打开但登录失败，检查 `/api/` 是否被正确代理
- 如果 `/api/health` 本地正常但公网不正常，检查 Tunnel 的 Public Hostname 是否指向 `http://localhost:80`
- 如果电脑休眠或关机，公网链接会失效
- 如果 Docker 容器停止，公网链接也会失效

如果将该地址用于简历展示，需要确保本机、Docker 服务和 Cloudflare Tunnel 在面试官访问期间保持在线。

## 安全初始化说明

生产环境部署时必须修改 `JWT_SECRET_KEY`，不要使用默认开发值或示例占位值。`APP_ENV=production` 时，如果 `JWT_SECRET_KEY` 缺失或仍为开发默认值，后端会拒绝启动。

生产环境部署时必须修改 `ADMIN_PASSWORD`，不要使用默认密码 `admin123`。`APP_ENV=production` 时，如果 `ADMIN_PASSWORD` 缺失或仍为默认密码，后端会拒绝启动。

公开演示或公网部署时，建议设置：

```env
ENABLE_PUBLIC_REGISTER=false
```

这样可以关闭自助注册入口，登录接口和管理员创建用户功能不受影响。

默认管理员只会在用户表为空的首次初始化时创建。如果数据库中已经存在用户，后续修改 `ADMIN_USERNAME` 或 `ADMIN_PASSWORD` 不会自动重置已有 admin 密码；需要在系统内修改密码，或在明确确认数据可重建时重置数据库。
