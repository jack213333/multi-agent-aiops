"""故障报告 Agent — LLM 生成自然语言事故复盘报告

核心功能：
1. 汇总 Monitor / RCA / Heal / Change 四个环节的结构化结果
2. 调用 LLM 生成中文 Markdown 复盘报告（摘要/告警/根因/自愈/审批/复盘建议）
3. 报告作为 ReportEvent 发布到事件总线并写回全局状态

降级策略：
- 未配置 API Key 时跳过生成（工作流节点条件路由直接 SKIPPED）
- LLM 调用失败时抛出异常，交给编排器的重试机制处理
"""

import json
import logging
from typing import Any, Optional

from agents.base_agent import BaseAgent
from core.event_bus import EventBus
from models.events import AgentType, IncidentState, ReportEvent

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "你是一名资深 SRE 工程师，负责撰写故障复盘报告。"
    "基于提供的结构化故障数据，生成一份简洁、专业、可执行的中文 Markdown 报告，"
    "包含以下章节：## 摘要 / ## 告警详情 / ## 根因分析 / ## 自愈动作 / ## 审批结论 / ## 复盘建议。"
    "只输出报告本身，不要输出任何其他内容。"
)


class ReportAgent(BaseAgent):
    """故障报告 Agent — 工作流最后一个节点"""

    def __init__(self, event_bus: EventBus, llm: Any = None):
        super().__init__(AgentType.REPORT, event_bus, "ReportAgent")
        # llm 支持注入（测试用）；None 时按配置惰性创建 ChatOpenAI
        self._llm = llm

    @staticmethod
    def is_available() -> bool:
        """是否具备 LLM 生成条件（用于工作流节点条件路由）"""
        from config.settings import settings

        return settings.openai_api_key is not None

    async def process(self, state: IncidentState) -> IncidentState:
        if state.alert_event is None:
            logger.warning("[ReportAgent] No alert event, nothing to report")
            return state

        llm = self._llm or self._build_llm()
        if llm is None:
            logger.warning(
                "[ReportAgent] LLM 未配置（AIOPS_OPENAI_API_KEY 为空），跳过报告生成"
            )
            return state

        messages = self._build_prompt(state)
        response = await llm.ainvoke(messages)
        content = response.content

        report_event = ReportEvent(
            content=content,
            model=self._model_name(),
            correlation_id=state.incident_id,
        )
        state.report_event = report_event
        await self.event_bus.publish("aiops.reports", report_event)

        logger.info(f"[ReportAgent] Report generated ({len(content)} chars)")
        return state

    def _build_llm(self):
        """按配置惰性创建 ChatOpenAI（OpenAI 兼容接口，默认 DeepSeek）"""
        from config.settings import settings
        from langchain_openai import ChatOpenAI

        if not settings.openai_api_key:
            return None
        return ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            temperature=0.3,
            timeout=settings.llm_timeout_seconds,
        )

    @staticmethod
    def _model_name() -> str:
        from config.settings import settings

        return settings.openai_model

    def _build_prompt(self, state: IncidentState) -> list[dict[str, str]]:
        """把四个环节的结构化结果序列化为 JSON，交给 LLM 生成报告"""
        data = {
            "incident_id": state.incident_id,
            "alert": self._serialize_alert(state.alert_event),
            "rca": self._serialize_rca(state.rca_event),
            "heal": self._serialize_heal(state.heal_event),
            "change": self._serialize_change(state.change_event),
        }
        user_prompt = (
            "以下是本次故障的结构化数据（JSON）：\n"
            f"{json.dumps(data, ensure_ascii=False, indent=2)}\n\n"
            "请生成故障复盘报告。"
        )
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

    @staticmethod
    def _serialize_alert(event) -> Optional[dict[str, Any]]:
        if not event:
            return None
        return {
            "alert_name": event.alert_name,
            "severity": event.severity.value,
            "target_service": event.target_service,
            "metric_name": event.metric_name,
            "metric_value": event.metric_value,
            "threshold": event.threshold,
            "description": event.description,
        }

    @staticmethod
    def _serialize_rca(event) -> Optional[dict[str, Any]]:
        if not event:
            return None
        return {
            "root_cause": event.root_cause,
            "confidence": event.confidence,
            "affected_services": event.affected_services,
            "evidence": event.evidence,
            "suggested_actions": event.suggested_actions,
        }

    @staticmethod
    def _serialize_heal(event) -> Optional[dict[str, Any]]:
        if not event:
            return None
        return {
            "heal_level": event.heal_level.value,
            "action_type": event.action_type,
            "target_service": event.target_service,
            "estimated_impact": event.estimated_impact,
            "blast_radius": event.blast_radius,
            "dry_run_result": event.dry_run_result,
            "execution_result": event.execution_result,
        }

    @staticmethod
    def _serialize_change(event) -> Optional[dict[str, Any]]:
        if not event:
            return None
        return {
            "risk_score": event.risk_score,
            "approval_status": event.approval_status,
            "approver": event.approver,
            "reason": event.reason,
        }
