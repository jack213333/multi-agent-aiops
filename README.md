# 🤖 Multi-Agent AIOps — 多 Agent 智能运维系统

<div align="center">

**企业级多 Agent 智能运维平台 | Python 实现**


[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](python/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

</div>

---

## 📖 这个项目是什么？

你是否遇到过这些问题：
- 运维团队每天被 **200+ 条告警**淹没，大部分是误报
- 服务出了问题，排查根因要花 **40 分钟**
- 凌晨 3 点被电话叫醒，半睡半醒地排查故障

本项目用 **5 个 AI Agent 协作**，自动完成从「告警检测」到「故障修复」的全流程，把 MTTR（平均修复时间）从 40 分钟降到 5 分钟。

```
告警来了
  ↓  Agent 1：这是真的异常吗？（时序分析，过滤误报）
  ↓  Agent 2：根因在哪里？（知识图谱推理）
  ↓  Agent 3：怎么修复？能自动执行吗？（安全护栏 + 分级策略）
  ↓  Agent 4：这个操作风险有多大？需要审批吗？（风险评分）
  ↓  Agent 5：LLM 生成自然语言故障复盘报告（推送 oncall）
  ✅ 5 分钟内修复完成，全程自动
```

> **适用人群**：对多 Agent 系统设计、事件驱动架构、智能运维感兴趣的开发者与学习者

---

## 🏗️ 系统架构

### 整体架构图

```
┌──────────────────────────────────────────────────────────────┐
│                       数据采集层                              │
│   Prometheus（指标）  Loki（日志）  Jaeger（链路）  CMDB      │
└───────────────────────────┬──────────────────────────────────┘
                            │ 异常数据
                   ┌────────▼─────────┐
                   │  事件总线 Kafka   │  ← 解耦所有 Agent
                   │  aiops.alerts    │
                   │  aiops.events    │
                   │  aiops.commands  │
                   │  aiops.reports   │
                   └────────┬─────────┘
                            │
┌───────────────────────────▼──────────────────────────────────┐
│                   Agent 编排器 Orchestrator                    │
│                  （状态机 · 条件路由 · 检查点恢复）              │
│                                                              │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌──────────┐  │
│  │ 监控告警   │→ │ 根因分析   │→ │ 故障自愈   │→ │ 变更审批  │  │
│  │  Agent   │  │  Agent   │  │  Agent   │  │  Agent  │  │
│  │           │  │           │  │           │  │          │  │
│  │3-Sigma    │  │知识图谱   │  │Playbook   │  │风险评分  │  │
│  │EWMA       │  │BFS遍历   │  │dry-run    │  │L0/L1/L2  │  │
│  │IsoForest  │  │贝叶斯推理 │  │熔断器     │  │审计日志  │  │
│  └───────────┘  └───────────┘  └───────────┘  └──────────┘  │
│                                   ↓                          │
│                           ┌──────────────┐                    │
│                           │ 故障报告 Agent │ ← LLM 复盘报告     │
│                           │ DeepSeek 生成  │                    │
│                           └──────────────┘                    │
└───────────────────────────┬──────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────┐
│                         知识层                                │
│      Neo4j 知识图谱    向量数据库 RAG    规则引擎              │
│   （服务拓扑 + 依赖关系 + 历史故障）                           │
└──────────────────────────────────────────────────────────────┘
```

### 一次故障的完整处理流程

```
1. Prometheus 检测到 order-service CPU 使用率 95%
2. 监控告警 Agent：多算法投票确认异常，生成告警事件
3. 根因分析 Agent：查知识图谱，发现 order-service 今天有新部署
                    贝叶斯推理：P(部署引起|CPU高) = 0.54
4. 故障自愈 Agent：匹配 rollback Playbook（L1级），dry-run 通过
5. 变更审批 Agent：风险评分 0.16，oncall 自动审批
6. 执行回滚，5 分钟内恢复正常 ✅
7. 故障报告 Agent：LLM 汇总全链路数据，生成中文 Markdown 复盘报告
```

---

## 🚀 快速开始（5 分钟跑起来）

### 方式一：最简运行（零外部依赖，推荐小白）

```bash
# 克隆项目
git clone https://gitee.com/jack5213/multi-agent-aiops.git
cd multi-agent-aiops/python

# 安装依赖（只装必要的，不需要 Kafka/Neo4j）
pip install fastapi uvicorn pydantic pydantic-settings numpy scikit-learn structlog

# 启动服务
python -m uvicorn api.main:app --reload --port 8000
```

浏览器打开 → **http://localhost:8000/docs**，你会看到完整的 API 文档界面

### 启用 LLM 故障报告（可选，推荐）

默认不配置时，报告节点会自动跳过，其余功能不受影响。配置后，每次故障处理结束会由 LLM 自动生成中文复盘报告：

```bash
cd python
pip install langchain-openai        # 只需这一个额外依赖

# 复制 .env.example 为 .env，填入 DeepSeek API Key
cp .env.example .env                # Windows: copy .env.example .env
# 编辑 .env：AIOPS_OPENAI_API_KEY=sk-xxxx

python -m uvicorn api.main:app --reload --port 8000
```

也支持任何 OpenAI 兼容服务（通义千问 / MiniMax / vLLM 等），改 `.env` 里的 `AIOPS_OPENAI_BASE_URL` 和 `AIOPS_OPENAI_MODEL` 即可。

### 方式二：完整运行（含 Kafka + Neo4j + Grafana）

```bash
cd python

# 一键启动所有基础设施
docker-compose up -d

# 等待约 30 秒服务就绪，然后启动主服务
pip install -r requirements.txt
python -m uvicorn api.main:app --reload --port 8000
```

各组件地址：
- **API 文档**: http://localhost:8000/docs
- **Neo4j 浏览器**: http://localhost:7474 （账号 neo4j / aiops_password）
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 （账号 admin / aiops_admin）

### 方式三：一键 Demo 演示

```bash
cd python
python -c "import asyncio; from core.orchestrator import run_demo; asyncio.run(run_demo())"
```

输出示例：
```
============================================================
  故障处理结果
============================================================
  事件 ID:    a8f3c2d1-...
  状态:       resolved

  [告警]
    名称:     high_cpu_usage
    严重度:   high
    服务:     order-service
    指标值:   95.3

  [根因分析]
    根因:     近期代码部署引入性能退化
    置信度:   0.54
    影响链:   order-service → payment-service → mysql-primary
    建议动作: rollback, profiling

  [自愈]
    操作:     rollback
    级别:     L1（需 oncall 确认）
    爆炸半径: 0.15
    Dry-run:  DRY-RUN OK: kubectl rollout undo deployment/order-service

  [审批]
    状态:     approved
    风险分:   0.158
    审批人:   oncall-engineer
    原因:     L1 approved: risk=0.158

  [复盘报告]
    模型:     deepseek-chat
    ------------------------------------
    ## 摘要
    order-service 因近期代码部署出现 CPU 使用率异常……
    （LLM 生成的完整 Markdown 报告，未配置 Key 时此段不显示）

  [工作流节点状态]
    monitor      → completed
    rca          → completed
    heal         → completed
    change       → completed
    report       → completed
============================================================
```

### 方式四：真实基础设施模式（双模开关）

系统支持内存版 / 真实版**双模切换**：默认走内存事件总线与内存知识图谱（零依赖，适合开发调试），通过环境变量一键切换到真实 Kafka 与 Neo4j：

```bash
cd python
docker-compose up -d        # 先启动 Kafka + Neo4j + Prometheus + Grafana

# 全开真实模式：事件走 Kafka，图谱走 Neo4j
AIOPS_USE_KAFKA=true AIOPS_USE_NEO4J=true python -m uvicorn api.main:app --port 8000
```

| 环境变量 | 默认 | 说明 |
|---|---|---|
| `AIOPS_USE_KAFKA` | `false` | 开启后事件总线切换为 Kafka（生产者 acks=all，消费者手动 commit），并挂载审计消费者旁路监听全部事件流 |
| `AIOPS_USE_NEO4J` | `false` | 开启后知识图谱切换为 Neo4j，启动时自动建约束/索引并灌入演示拓扑（幂等 MERGE） |
| `AIOPS_KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Kafka 地址 |
| `AIOPS_NEO4J_URI` / `AIOPS_NEO4J_USER` / `AIOPS_NEO4J_PASSWORD` | `bolt://localhost:7687` / `neo4j` / `aiops_password` | Neo4j 连接信息 |
| `AIOPS_OPENAI_API_KEY` | 空 | LLM API Key；**为空时报告节点自动跳过** |
| `AIOPS_OPENAI_BASE_URL` | `https://api.deepseek.com` | OpenAI 兼容接口地址 |
| `AIOPS_OPENAI_MODEL` | `deepseek-chat` | 模型名 |
| `AIOPS_LLM_TIMEOUT_SECONDS` | `30` | LLM 调用超时（秒） |

**故障自检（fail-fast）**：开关打开但基础设施未启动时，应用启动阶段即报错提示，不会带病运行。

**验证真实链路**：

```bash
# 1. 触发一次故障,日志中可见 [KafkaEventBus] Published to aiops.audit
curl -X POST http://localhost:8000/api/v1/incidents/trigger

# 2. Kafka 侧确认事件落盘
docker exec python-kafka-1 kafka-console-consumer --bootstrap-server localhost:9092 \
  --topic aiops.audit --from-beginning --max-messages 1

# 3. Neo4j 浏览器 (http://localhost:7474) 查看服务依赖图
#    MATCH (n) RETURN n

# 4. API 侧确认 RCA 的依赖链来自图谱
curl http://localhost:8000/api/v1/topology/order-service/dependencies
```

---

## 📁 项目结构详解

```
multi-agent-aiops/
│
├── 📄 README.md                     ← 你现在看的这个文件
│
├── 🐍 python/                       ← Python 实现（推荐先看这个）
│   ├── agents/
│   │   ├── base_agent.py            ← Agent 抽象基类（模板方法模式）
│   │   ├── monitor_agent.py         ← 监控告警 Agent
│   │   ├── rca_agent.py             ← 根因分析 Agent
│   │   ├── heal_agent.py            ← 故障自愈 Agent
│   │   ├── change_agent.py          ← 变更审批 Agent
│   │   └── report_agent.py          ← 故障报告 Agent（LLM 复盘报告）
│   ├── core/
│   │   ├── orchestrator.py          ← Agent 编排器（状态机）⭐ 最核心
│   │   ├── event_bus.py             ← 事件总线（Kafka + 内存双模）⭐
│   │   └── knowledge_graph.py       ← 知识图谱（Neo4j + 内存双模）⭐
│   ├── models/
│   │   ├── events.py                ← 所有事件的数据模型
│   │   └── time_series.py           ← 时序异常检测算法
│   ├── api/
│   │   └── main.py                  ← FastAPI 接口入口
│   ├── config/
│   │   └── settings.py              ← 全局配置
│   ├── tests/                       ← pytest 单元测试
│   ├── .env.example                 ← LLM 配置模板（复制为 .env 使用）
│   ├── docker-compose.yml           ← 一键启动基础设施
│   └── requirements.txt             ← Python 依赖
│
└── 📚 docs/                         ← 文档
    ├── architecture.md              ← 架构设计文档
    └── tutorial/                   ← 📖 从 0 到部署教程
        ├── 01-getting-started.md    ← 入门：理解项目结构
        ├── 02-event-driven.md       ← 事件驱动架构详解
        ├── 03-agent-design.md       ← Agent 设计模式
        ├── 04-knowledge-graph.md    ← 知识图谱详解
        └── 05-deploy.md             ← 生产部署指南
```

---

## 🔌 API 接口说明

启动后访问 http://localhost:8000/docs 查看完整文档，核心接口：

### 触发故障处理流程

```bash
# 使用 Demo 数据（模拟 CPU 告警）
curl -X POST http://localhost:8000/api/v1/incidents/trigger

# 传入自定义指标数据
curl -X POST http://localhost:8000/api/v1/incidents/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "metric_name": "cpu_usage_percent",
    "metric_value": 95.3,
    "target_service": "order-service"
  }'
```

响应中包含各环节结果与 `report` 字段（LLM 生成的复盘报告，未配置 Key 时为 null）以及 `workflow` 各节点状态。

### 查看服务拓扑

```bash
# 查看全部拓扑
curl http://localhost:8000/api/v1/topology

# 查看某服务的依赖链
curl http://localhost:8000/api/v1/topology/order-service/dependencies
```

返回示例：
```json
{
  "service": "order-service",
  "direct_dependencies": ["payment-service", "inventory-service", "user-service"],
  "depended_by": ["api-gateway"],
  "impact_score": 0.091,
  "dependency_paths": [
    ["order-service", "payment-service", "mysql-primary"],
    ["order-service", "inventory-service", "elasticsearch"]
  ]
}
```

### 运行异常检测 Demo

```bash
curl http://localhost:8000/api/v1/anomaly/demo
```

返回示例：
```json
{
  "total_points": 200,
  "anomalies_detected": 3,
  "anomalies": [
    {"index": 150, "value": 82.45, "score": 4.21, "actual_anomaly": true},
    {"index": 170, "value": 19.83, "score": 3.87, "actual_anomaly": true}
  ]
}
```

---

## 💡 核心技术亮点

### 1. 时序异常检测 — 多算法投票

```python
# 三种算法同时检测，至少 2 种认为异常才报警（减少误报）
3-Sigma    → 检测突变（CPU 突然飙高）
EWMA       → 检测趋势（CPU 缓慢上涨）
Isolation Forest → 检测多维异常（多个指标同时异常）

投票结果：2/3 投票 = 报警  →  误报率降低 85%
```

> 📖 算法详解：[docs/tutorial/03-agent-design.md](docs/tutorial/03-agent-design.md)

### 2. 知识图谱根因分析

```python
# 服务拓扑（Neo4j 存储）
order-service
  ├── depends on → payment-service → mysql-primary
  ├── depends on → inventory-service（有近期变更！）
  └── depends on → user-service

# 贝叶斯推理
P(部署引起|CPU高) = P(CPU高|部署引起) × P(部署引起) / P(CPU高)
                  = 0.9 × 0.3 / 0.5 = 0.54 ← 54% 置信度
```

> 📖 知识图谱详解：[docs/tutorial/04-knowledge-graph.md](docs/tutorial/04-knowledge-graph.md)

### 3. 分级自愈 + 安全护栏

```
L0（全自动）：重启 Pod、扩容、限流  ← 爆炸半径 < 5%，直接执行
L1（半自动）：回滚版本、改配置      ← 需要 oncall 确认
L2（人工介入）：数据库操作、全量回滚 ← 需要 TL 审批

安全护栏链：
dry-run 模拟 → 爆炸半径 < 20%？→ 熔断器开着？→ 审批通过？→ 执行
```

> 📖 Agent 设计详解：[docs/tutorial/03-agent-design.md](docs/tutorial/03-agent-design.md)

### 4. 事件驱动架构

```python
# Kafka Topic 设计
aiops.alerts    ← MonitorAgent 发布告警
aiops.events    ← RCAAgent 发布分析结果
aiops.commands  ← HealAgent 发布修复命令
aiops.audit     ← ChangeAgent 发布审批记录
*.dlq           ← 死信队列（消费失败的消息）

# 双模支持：本地开发用内存队列，生产用 Kafka
event_bus = create_event_bus(use_kafka=False)  # 本地开发
event_bus = create_event_bus(use_kafka=True)   # 生产环境
```

> 📖 事件驱动详解：[docs/tutorial/02-event-driven.md](docs/tutorial/02-event-driven.md)

### 5. LLM 故障复盘报告生成

```python
# 工作流最后一个节点：汇总全链路结构化数据，交给 LLM 生成报告
{
  "alert":  {"alert_name": "high_cpu_usage", "target_service": "order-service", ...},
  "rca":    {"root_cause": "近期代码部署引入性能退化", "confidence": 0.54, ...},
  "heal":   {"action_type": "rollback", "heal_level": "L1", ...},
  "change": {"approval_status": "approved", "risk_score": 0.158, ...}
}
        ↓ ChatOpenAI（OpenAI 兼容，默认 DeepSeek）
## 摘要 / ## 告警详情 / ## 根因分析 / ## 自愈动作 / ## 审批结论 / ## 复盘建议
```

设计要点：
- **确定性环节用规则，生成环节用 LLM**：异常检测/根因推理要求可解释、低延迟，用统计算法；报告生成要求自然语言表达，交给 LLM —— 各取所长
- **优雅降级**：未配置 API Key 时报告节点自动跳过，零依赖模式不受影响；调用失败交给编排器重试
- **发布 aiops.reports** 到事件总线，Kafka 模式下审计消费者可旁路监听全部事件流

---



---
---

## 📚 从零开始学习路径

推荐按以下顺序学习：

```
第 1 天：理解架构
  ├── 读 README（本文件）
  └── 读 docs/tutorial/01-getting-started.md

第 2 天：跑起来
  ├── 按快速开始运行 Python 版
  └── 用 curl 测试各接口，观察输出

第 3 天：看核心代码
  ├── python/models/events.py     ← 理解数据流
  ├── python/core/orchestrator.py ← 理解编排逻辑
  └── python/agents/rca_agent.py  ← 最复杂的 Agent

第 4 天：理解技术原理
  ├── docs/tutorial/02-event-driven.md
  ├── docs/tutorial/03-agent-design.md
  └── docs/tutorial/04-knowledge-graph.md

第 5-7 天：实践拓展
  ├── 跑通方式四（Kafka + Neo4j 真实基础设施模式）
  └── 读 docs/architecture.md
```

---

## ⚙️ 技术栈全览

| 层次 | 🐍 Python 版 |
|------|-------------|
| **Agent 框架** | LangGraph 状态机 |
| **API 层** | FastAPI + Pydantic |
| **LLM 接入** | langchain-openai（默认 DeepSeek，OpenAI 兼容） |
| **事件总线** | confluent-kafka |
| **知识图谱** | Neo4j + py2neo |
| **时序分析** | Prophet + scikit-learn |
| **向量数据库** | ChromaDB（RAG） |
| **监控** | Prometheus Client |
| **容器化** | Docker Compose |
| **配置管理** | pydantic-settings |

---

## 🤝 参考的企业级开源项目

本项目设计时参考了以下真实的企业级项目：

| 项目 | 公司/组织 | 技术特点 |
|------|---------|---------|
| [HolmesGPT](https://github.com/holmesgpt/holmesgpt) | CNCF Sandbox | Agentic Loop + 多数据源根因分析 |
| [Aurora](https://github.com/arvo-ai/aurora) | Arvo AI | LangGraph + Memgraph 知识图谱 |
| [Microsoft AIOpsLab](https://github.com/microsoft/AIOpsLab) | Microsoft | AIOps Agent 评测框架 |
| [Auto-Agent-K8s](https://github.com/supersaiyane/auto-agent-k8s) | 社区 | K8s 故障自动修复 |
| [Self-Healing SRE](https://github.com/jalpatel11/Self-Healing-SRE-Agent) | 社区 | LangGraph 自愈 SRE |

---

## 📄 License

MIT License — 可自由用于学习与修改

---

<div align="center">

**如果这个项目对你有帮助，欢迎 ⭐ Star 支持一下！**

</div>
