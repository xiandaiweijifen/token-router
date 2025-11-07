# token-router

Token allocation service with per-node quota, concurrency safety, and 429 overload handling.

## Getting Started

1. 创建虚拟环境（可选）: `python -m venv .venv && source .venv/bin/activate`
2. 安装依赖: `pip install -r requirements.txt`
3. 启动开发服务器: `uvicorn app.main:app --reload`

服务启动后可通过 `GET /health` 验证运行状态。

## 规格说明

任务背景、接口语义与实现记录详见 `routing.md`，其中的 `Implementation Notes` 会随着开发阶段持续更新。
