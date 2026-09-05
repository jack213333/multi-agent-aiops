"""ReportAgent 单元测试 — LLM 故障复盘报告生成"""

import pytest

from agents.report_agent import ReportAgent
from core.event_bus import InMemoryEventBus
from core.orchestrator import Orchestrator
from models.events import (
    AlertEvent,
    ChangeEvent,
    HealEvent,
    HealLevel,
    IncidentState,
    RCAEvent,
    Severity,
)


class FakeLLM:
    """测试替身：记录收到的消息并返回固定内容（替代真实的 LLM 网络调用）"""

    def __init__(self, response: str = "# 故障复盘报告\n\n这是测试生成的报告内容。"):
        self.response = response
        self.messages: list = []

    async def ainvoke(self, messages):
        self.messages.append(messages)
        return FakeResponse(self.response)


class FakeResponse:
    def __init__(self, content: str):
        self.content = content


def _build_full_state() -> IncidentState:
    """构造走完 Monitor→RCA→Heal→Change 四个环节的完整状态"""
    state = IncidentState()
    state.alert_event = AlertEvent(
        alert_name="high_cpu_usage",
        severity=Severity.HIGH,
        source="prometheus",
        target_service="order-service",
        metric_name="cpu_usage_percent",
        metric_value=95.3,
        threshold=80.0,
        description="CPU 使用率超过阈值",
        correlation_id=state.incident_id,
    )
    state.rca_event = RCAEvent(
        alert_event_id=state.alert_event.event_id,
        root_cause="近期代码部署引入性能退化",
        confidence=0.54,
        affected_services=["order-service", "payment-service"],
        evidence=[{"type": "recent_change", "source": "cmdb", "detail": "deploy v2.3.1"}],
        suggested_actions=["rollback", "profiling"],
        correlation_id=state.incident_id,
    )
    state.heal_event = HealEvent(
        rca_event_id=state.rca_event.event_id,
        heal_level=HealLevel.L1_SEMI,
        action_type="rollback",
        action_params={"command": "kubectl rollout undo deployment/order-service"},
        target_service="order-service",
        estimated_impact="回滚到上一个稳定版本",
        blast_radius=0.15,
        dry_run_result="DRY-RUN OK",
        correlation_id=state.incident_id,
    )
    state.change_event = ChangeEvent(
        heal_event_id=state.heal_event.event_id,
        risk_score=0.158,
        approval_status="approved",
        approver="oncall-engineer",
        reason="L1 approved: risk=0.158",
        correlation_id=state.incident_id,
    )
    return state


@pytest.mark.asyncio
async def test_report_agent_writes_report_event_to_state_and_bus():
    """ReportAgent 生成报告后应写回 state.report_event 并发布 aiops.reports 事件"""
    bus = InMemoryEventBus()
    fake = FakeLLM()
    agent = ReportAgent(bus, llm=fake)
    state = _build_full_state()

    result = await agent.process(state)

    assert result.report_event is not None
    assert result.report_event.content == fake.response
    assert result.report_event.correlation_id == state.incident_id

    published = bus.get_event_log()
    report_events = [e for e in published if e["topic"] == "aiops.reports"]
    assert len(report_events) == 1
    assert report_events[0]["event"]["event_type"] == "report.generated"


@pytest.mark.asyncio
async def test_report_agent_skips_when_llm_not_configured(monkeypatch):
    """未配置 API Key 且未注入 LLM 时，应跳过生成且不改变 state"""
    from config.settings import settings

    monkeypatch.setattr(settings, "openai_api_key", None)
    bus = InMemoryEventBus()
    agent = ReportAgent(bus)
    state = _build_full_state()

    result = await agent.process(state)

    assert result.report_event is None
    assert bus.get_event_log() == []


@pytest.mark.asyncio
async def test_prompt_contains_structured_incident_data():
    """发给 LLM 的 prompt 应包含告警、根因、自愈、审批四个环节的关键数据"""
    bus = InMemoryEventBus()
    fake = FakeLLM()
    agent = ReportAgent(bus, llm=fake)
    state = _build_full_state()

    await agent.process(state)

    messages = fake.messages[0]
    user_prompt = [m for m in messages if m["role"] == "user"][0]["content"]
    assert "high_cpu_usage" in user_prompt
    assert "order-service" in user_prompt
    assert "近期代码部署引入性能退化" in user_prompt
    assert "rollback" in user_prompt
    assert "approved" in user_prompt


@pytest.mark.asyncio
async def test_orchestrator_skips_report_node_without_api_key(monkeypatch):
    """未配置 API Key 时，工作流第 5 个 report 节点应被条件路由跳过"""
    from config.settings import settings

    monkeypatch.setattr(settings, "openai_api_key", None)
    bus = InMemoryEventBus()
    orchestrator = Orchestrator(bus)

    await orchestrator.run()

    statuses = {n["name"]: n["status"] for n in orchestrator.get_workflow_status()}
    assert statuses["report"] == "skipped"
    assert list(statuses.keys()) == ["monitor", "rca", "heal", "change", "report"]


@pytest.mark.asyncio
async def test_orchestrator_runs_report_node_when_api_key_configured(monkeypatch):
    """配置 API Key 后，完整工作流应执行 report 节点并产出报告"""
    from config.settings import settings

    fake_llm = FakeLLM()
    monkeypatch.setattr(settings, "openai_api_key", "test-key")
    monkeypatch.setattr("langchain_openai.ChatOpenAI", lambda **kwargs: fake_llm)

    bus = InMemoryEventBus()
    orchestrator = Orchestrator(bus)

    state = await orchestrator.run()

    statuses = {n["name"]: n["status"] for n in orchestrator.get_workflow_status()}
    assert statuses["report"] == "completed"
    assert state.report_event is not None
    assert state.report_event.content == fake_llm.response
