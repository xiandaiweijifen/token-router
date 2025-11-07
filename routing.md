基于Token预算的路由服务
背景
集群有 N 个节点，编号 0…N-1，每个节点可以支持的Token数预算为M。
你需要实现一个 HTTP 服务，支持申请与释放 token，并保证任意并发下：
1. 不超卖，也就是任意节点上的分配出来的token预算不会超过M
2. 无法服务时返回 429 Overloaded

具体而言，你需要实现两个接口:
POST /alloc
{"request_id": "<唯一ID>", "token_count": <int>}
返回值:
如果有资源，返回分配选中的节点和它的剩余quota
200 {"node_id": <int>, "remaining_quota": <int>}

如果无资源: 429 {"error": "overloaded"}

POST /free
{"request_id": "<之前申请用过的ID>"}
返回值:
释放成功: 200 {"node_id": <int>}
释放失败: 404 {"error": "not_found"}

并发要求
服务需正确处理任意数量同时到达的 /alloc 与 /free 请求，不得出现负预算或错误释放。

加分项:
在正确实现的基础上，能使得资源利用率达到最高

示例输入(N=2, M=300):
{"method": "POST", "path": "/alloc", "body": {"request_id": "req-1", "token_count": 80}}
{"method": "POST", "path": "/alloc", "body": {"request_id": "req-2", "token_count": 120}}
{"method": "POST", "path": "/free", "body": {"request_id": "req-1"}}
{"method": "POST", "path": "/alloc", "body": {"request_id": "req-3", "token_count": 200}}
{"method": "POST", "path": "/free", "body": {"request_id": "req-2"}}
{"method": "POST", "path": "/alloc", "body": {"request_id": "req-4", "token_count": 300}}
{"method": "POST", "path": "/free", "body": {"request_id": "req-3"}}
{"method": "POST", "path": "/alloc", "body": {"request_id": "req-5", "token_count": 250}}
{"method": "POST", "path": "/free", "body": {"request_id": "req-4"}}
{"method": "POST", "path": "/free", "body": {"request_id": "req-5"}}

## Implementation Notes

### 需求假设
- N、M 在服务启动时通过配置文件或环境变量注入，运行期保持不变。
- `request_id` 全局唯一，重复请求视为幂等操作。
- 服务仅在单实例内存中维护状态，不做跨进程持久化。
- 错误响应必须遵循固定 JSON 格式，客户端可依赖其进行重试或警报。

### 模块划分
- HTTP 层：负责 JSON 解析、参数校验和统一响应。
- 调度/分配模块：维护节点剩余额度与 `request_id -> allocation` 映射，提供 `Alloc` / `Free` 接口。
- 状态存储：跟踪每个节点剩余 token 和历史请求记录。

### 并发控制
- 调度模块通过互斥锁或读写锁保护共享状态，确保原子性。
- `/free` 遇到未知 `request_id` 时立即返回 404，避免错误释放。
- 后续可探索分片锁或 CAS 提升并发度，但首版以正确性为先。

### 开放问题 / TODO
- 多实例场景是否需要共享存储（如 Redis）？
- 节点选择策略是否需优化利用率（最少剩余、轮询等）？
- 是否需要额外的限流、认证或观测指标？

### 实现进度
- 已完成 FastAPI 脚手架与 `/health` 检查。
- 内存版 `TokenAllocator` 实现并配套 Pytest 单测覆盖分配/释放、幂等与异常场景。
- `/alloc`、`/free` HTTP 接口接入核心逻辑，定义请求/响应模型并映射 429/409/404 等错误。
- 新增 API 集成测试，使用 FastAPI `TestClient` 验证成功分配、过载和释放路径。
- 通过 `TOKEN_ROUTER_NODE_COUNT` 与 `TOKEN_ROUTER_NODE_QUOTA` 环境变量配置节点规模和每节点预算。
