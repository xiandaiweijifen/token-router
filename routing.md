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