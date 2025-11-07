# token-router

Token allocation service with per-node quota, concurrency safety, and 429 overload handling.

## Getting Started

1. 创建虚拟环境（可选）: `python -m venv .venv && source .venv/bin/activate`
2. 安装依赖: `pip install -r requirements.txt`
3. 启动开发服务器: `uvicorn app.main:app --reload`

服务启动后可通过 `GET /health` 验证运行状态。

## Configuration

| 环境变量 | 说明 | 默认值 |
| --- | --- | --- |
| `TOKEN_ROUTER_NODE_COUNT` | 集群节点数量 N | `3` |
| `TOKEN_ROUTER_NODE_QUOTA` | 每个节点可分配的 token 预算 M | `300` |

示例：`TOKEN_ROUTER_NODE_COUNT=2 TOKEN_ROUTER_NODE_QUOTA=300 uvicorn app.main:app --reload`

## API Usage

```bash
# 申请 80 tokens
curl -X POST http://localhost:8000/alloc \
  -H "Content-Type: application/json" \
  -d '{"request_id":"req-1","token_count":80}'

# 释放 request
curl -X POST http://localhost:8000/free \
  -H "Content-Type: application/json" \
  -d '{"request_id":"req-1"}'
```

## Sample Replay

`scripts/run_sample.sh` 可重放 `routing.md` 中的示例输入（N=2, M=300），运行前请先在另一个终端启动服务并配置环境变量：

```bash
TOKEN_ROUTER_NODE_COUNT=2 TOKEN_ROUTER_NODE_QUOTA=300 uvicorn app.main:app --reload
BASE_URL=http://localhost:8000 ./scripts/run_sample.sh
```

脚本按顺序发送 10 条 `/alloc`、`/free` 请求，输出每次的 JSON 响应，用于回归验证。

## 规格说明

任务背景、接口语义与实现记录详见 `routing.md`，其中的 `Implementation Notes` 会随着开发阶段持续更新。
