# -*- coding: utf-8 -*-
"""
腾讯云 AI Agent 出海经营合规决策看板 v04
定位：不是普通图表展示，而是围绕“经营问题 → 数据证据 → 优先级判断 → 解决方案 → 行动清单”的互动决策看板。
"""

from __future__ import annotations

import os
from typing import Dict, Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st


# =========================
# 0. 页面基础设置
# =========================
st.set_page_config(
    page_title="AI 出海经营合规决策看板",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
    :root {
        --ink: #14213D;
        --muted: #667085;
        --blue: #2563EB;
        --blue-dark: #1D4ED8;
        --blue-soft: #EAF2FF;
        --line: #E6EAF2;
        --card: #FFFFFF;
        --page: #F6F8FC;
    }
    .stApp {
        background: radial-gradient(circle at top left, #EEF5FF 0, #F8FAFF 26%, #FFFFFF 58%);
        color: var(--ink);
    }
    .main .block-container {
        padding-top: 1.35rem;
        padding-bottom: 2.2rem;
        max-width: 1520px;
    }

    /* Sidebar: make the filter area look like a product dashboard instead of default Streamlit controls */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #F4F7FB 0%, #EEF3F9 100%) !important;
        border-right: 1px solid #E2E8F0;
    }
    section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {
        color: #162033 !important;
        font-weight: 800 !important;
    }
    section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] p {
        color: #4B5563 !important;
    }
    section[data-testid="stSidebar"] [data-baseweb="select"] > div {
        background: #FFFFFF !important;
        border: 1px solid #D7E2F2 !important;
        border-radius: 12px !important;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03) !important;
    }

    /* Streamlit multiselect selected values. Use broad selectors because Streamlit/BaseWeb DOM changes across versions. */
    [data-baseweb="tag"],
    [data-baseweb="tag"] > span,
    [data-baseweb="tag"] div,
    [data-baseweb="tag"] span {
        background-color: #EAF2FF !important;
        color: #1D4ED8 !important;
        border-color: #BFD7FF !important;
    }
    [data-baseweb="tag"] {
        border: 1px solid #BFD7FF !important;
        border-radius: 999px !important;
        box-shadow: none !important;
    }
    [data-baseweb="tag"] svg,
    [data-baseweb="tag"] svg path,
    [data-baseweb="tag"] button svg,
    [data-baseweb="tag"] button svg path {
        fill: #1D4ED8 !important;
        color: #1D4ED8 !important;
    }
    [data-baseweb="tag"] button {
        background: transparent !important;
        color: #1D4ED8 !important;
    }

    .hero {
        border: 1px solid #E2E8F0;
        border-radius: 22px;
        padding: 22px 26px;
        background:
            linear-gradient(135deg, rgba(239,246,255,0.95) 0%, rgba(255,255,255,0.98) 48%, rgba(245,243,255,0.95) 100%);
        margin-bottom: 14px;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
    }
    .hero-title {
        font-size: 31px;
        font-weight: 850;
        color: #111827;
        letter-spacing: -0.02em;
        margin-bottom: 6px;
    }
    .hero-subtitle {font-size: 14px; color: #5C667A; margin-bottom: 14px;}
    .conclusion {
        border-left: 5px solid #2563EB;
        background: linear-gradient(90deg, #EFF6FF 0%, #F8FBFF 100%);
        border-radius: 14px;
        padding: 13px 16px;
        font-size: 15px;
        line-height: 1.75;
        color: #1F2D3D;
    }
    .conclusion b {color:#1D4ED8;}

    .action-card {
        min-height: 168px;
        border: 1px solid #E5EAF3;
        border-radius: 18px;
        padding: 17px 17px 15px 17px;
        background: rgba(255,255,255,0.96);
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.055);
        transition: transform .12s ease, box-shadow .12s ease;
    }
    .action-card:hover {transform: translateY(-1px); box-shadow: 0 14px 28px rgba(15, 23, 42, 0.075);}
    .action-card .tag {
        display:inline-block;
        font-size: 12px;
        color: #2563EB;
        background:#EAF2FF;
        border:1px solid #C7DBFF;
        border-radius:999px;
        padding: 3px 9px;
        margin-bottom: 10px;
        font-weight: 700;
    }
    .action-card .title {font-size: 18px; font-weight: 850; color: #18233A; margin-bottom: 10px;}
    .action-card .body {font-size: 13px; color: #475467; line-height: 1.65; margin-bottom: 9px;}
    .action-card .todo {
        font-size: 13px;
        color: #184E77;
        background:#F1F7FF;
        padding: 9px 10px;
        border-radius: 12px;
        line-height: 1.6;
        border:1px solid #DBEAFF;
    }

    .section-title {font-size: 23px; font-weight: 850; color: #18233A; margin: 22px 0 6px 0; letter-spacing:-0.01em;}
    .section-caption {font-size: 13px; color: #667085; margin-bottom: 11px;}
    .small-note {font-size: 12px; color: #7A8499; line-height: 1.55;}

    div[data-testid="stMetric"] {
        background: rgba(255,255,255,0.98);
        border: 1px solid #E4EAF4;
        padding: 15px 16px;
        border-radius: 17px;
        box-shadow: 0 7px 20px rgba(15,23,42,0.045);
    }
    div[data-testid="stMetricLabel"] {font-size: 13px; color: #667085;}
    div[data-testid="stMetricValue"] {font-size: 28px; color: #162033; font-weight: 800;}

    .solution-strip {
        border: 1px solid #DCE8FF;
        border-radius: 18px;
        padding: 15px 17px;
        background: linear-gradient(90deg, #FFFFFF 0%, #F7FAFF 100%);
        margin: 12px 0 18px 0;
        box-shadow: 0 6px 18px rgba(15,23,42,0.035);
    }
    .solution-title {font-weight: 850; color:#18233A; margin-bottom: 8px;}
    .solution-item {font-size: 13px; line-height: 1.7; color:#344054;}
    .solution-item b {color:#1D4ED8;}

    .playbook-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 14px;
        margin: 10px 0 22px 0;
    }
    .playbook-card {
        border: 1px solid #DDEAFF;
        background: rgba(255,255,255,0.96);
        border-radius: 16px;
        padding: 14px 15px;
        box-shadow: 0 6px 18px rgba(15,23,42,0.035);
    }
    .playbook-card .level {
        display:inline-block;
        color:#1D4ED8;
        background:#EAF2FF;
        border:1px solid #C7DBFF;
        border-radius:999px;
        font-size:12px;
        font-weight:800;
        padding:2px 9px;
        margin-bottom:8px;
    }
    .playbook-card .play-title {font-weight:850; color:#172033; margin-bottom:6px;}
    .playbook-card .play-body {font-size:13px; color:#475467; line-height:1.65;}
    .module-brief {
        border-left: 4px solid #3B82F6;
        background: #F8FBFF;
        border-radius: 12px;
        padding: 10px 12px;
        margin: 6px 0 14px 0;
        color:#344054;
        font-size:13px;
        line-height:1.7;
    }
    .module-brief b {color:#1D4ED8;}


    /* Plotly card spacing */
    div[data-testid="stPlotlyChart"] {
        background: rgba(255,255,255,0.86);
        border-radius: 14px;
    }
    .stTabs [data-baseweb="tab-list"] {gap: 10px;}
    .stTabs [data-baseweb="tab"] {border-radius: 999px; padding: 8px 14px;}
    .stTabs [aria-selected="true"] {background: #EAF2FF; color:#1D4ED8;}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# =========================
# 1. 数据读取与基础清洗
# =========================
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


@st.cache_data(show_spinner=False)
def load_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    metrics_path = os.path.join(DATA_DIR, "ai_oversea_metrics_v02.csv")
    risk_path = os.path.join(DATA_DIR, "ai_compliance_risk_v02.csv")
    request_path = os.path.join(DATA_DIR, "customer_compliance_requests_v02.csv")

    metrics = pd.read_csv(metrics_path)
    risks = pd.read_csv(risk_path)
    requests = pd.read_csv(request_path)

    for df in (metrics, risks, requests):
        df.columns = [c.strip().lower() for c in df.columns]

    if "net_revenue_usd" not in metrics.columns:
        metrics["net_revenue_usd"] = metrics["revenue_usd"].fillna(0) - metrics["refund_usd"].fillna(0)

    metrics["month"] = metrics["month"].astype(str)
    requests["business_value_usd"] = pd.to_numeric(requests["business_value_usd"], errors="coerce").fillna(0)
    metrics["net_revenue_usd"] = pd.to_numeric(metrics["net_revenue_usd"], errors="coerce").fillna(0)

    for col in ["legal_required", "product_required", "need_cross_team", "block_revenue_flag", "is_overdue"]:
        if col in requests.columns:
            requests[col] = pd.to_numeric(requests[col], errors="coerce").fillna(0).astype(int)
    for col in ["legal_required", "product_required", "need_cross_team"]:
        if col in risks.columns:
            risks[col] = pd.to_numeric(risks[col], errors="coerce").fillna(0).astype(int)

    return metrics, risks, requests


metrics_raw, risks_raw, requests_raw = load_data()


# =========================
# 2. 通用工具函数
# =========================
def fmt_money_wan(value_usd: float) -> str:
    return f"{value_usd / 10000:,.1f} 万美元"


def normalize_score(series: pd.Series) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce").fillna(0).astype(float)
    min_v, max_v = s.min(), s.max()
    if max_v == min_v:
        return pd.Series(np.where(s > 0, 100.0, 0.0), index=s.index)
    return (s - min_v) / (max_v - min_v) * 100


def risk_score_value(x: str) -> int:
    return {"高风险": 3, "中风险": 2, "低风险": 1}.get(str(x), 0)


def get_solution_template(request_type: str) -> Dict[str, str]:
    templates = {
        "客户数据是否用于模型训练": {
            "solution": "沉淀客户数据不用于模型训练的标准说明、FAQ、合同补充条款和销售答复口径。",
            "lead_team": "法务",
            "partners": "产品 / 业务",
            "sla": "3 天",
        },
        "日志留存要求": {
            "solution": "输出日志留存周期、客户可配置能力、审计支持范围和产品边界说明。",
            "lead_team": "产品",
            "partners": "法务 / 业务",
            "sla": "5 天",
        },
        "数据处理协议/DPA": {
            "solution": "准备标准 DPA 模板、条款审核路径、常见风险条款答复库和升级机制。",
            "lead_team": "法务",
            "partners": "业务 / 产品",
            "sla": "5 天",
        },
        "专属部署要求": {
            "solution": "形成公有云 API、专属部署、混合云/私有化部署的差异说明、交付周期和成本影响评估。",
            "lead_team": "产品",
            "partners": "业务 / 技术 / 法务",
            "sla": "7 天",
        },
        "数据不出境要求": {
            "solution": "提供数据驻留、区域部署、跨境传输限制和可选架构说明。",
            "lead_team": "产品",
            "partners": "法务 / 技术",
            "sla": "5 天",
        },
        "删除用户数据要求": {
            "solution": "沉淀数据删除流程、响应时限、审计记录和客户自助能力说明。",
            "lead_team": "产品",
            "partners": "法务 / 客成",
            "sla": "5 天",
        },
        "合同责任条款修改": {
            "solution": "建立合同责任边界说明、可接受修改范围和法务审批路径。",
            "lead_team": "法务",
            "partners": "业务",
            "sla": "5 天",
        },
        "内容安全审核要求": {
            "solution": "提供内容安全策略、敏感内容拦截、人工复核和客户侧配置说明。",
            "lead_team": "产品",
            "partners": "法务 / 业务",
            "sla": "5 天",
        },
        "第三方模型调用说明": {
            "solution": "说明第三方模型调用边界、数据流向、供应商责任和客户可选方案。",
            "lead_team": "产品",
            "partners": "法务",
            "sla": "5 天",
        },
        "合规材料/认证文件提供": {
            "solution": "建立认证材料包、标准下载入口和销售可复用材料清单。",
            "lead_team": "业务",
            "partners": "法务 / 安全",
            "sla": "3 天",
        },
    }
    return templates.get(
        request_type,
        {
            "solution": "补充标准答复材料，明确业务可回复范围、产品确认范围和法务升级边界。",
            "lead_team": "业务",
            "partners": "法务 / 产品",
            "sla": "5 天",
        },
    )


def get_customer_action(row: pd.Series) -> Dict[str, str]:
    high_income = row.get("net_revenue_usd", 0) >= row.get("revenue_threshold", 0)
    high_risk = row.get("high_risk_count", 0) >= 1
    overdue = row.get("p0p1_overdue_count", 0) >= 1
    block = row.get("block_count", 0) >= 1

    if high_income and high_risk:
        priority = "P0"
        action = "进入重点客户协同跟进池：业务确认成交/续费节点，法务确认合同与数据处理条款，产品确认日志留存、训练数据使用和部署能力说明。"
        lead = "业务"
        partners = "法务 / 产品"
        sla = "3 天"
    elif block or overdue:
        priority = "P1"
        action = "优先清理阻塞成交/续费或 P0/P1 超期需求，明确责任人和截止时间，避免影响客户转化。"
        lead = "业务"
        partners = "法务 / 产品"
        sla = "5 天"
    elif high_risk:
        priority = "P1"
        action = "纳入合规风险观察清单，提前准备客户可能追问的材料和标准口径。"
        lead = "法务"
        partners = "业务 / 产品"
        sla = "7 天"
    else:
        priority = "P2"
        action = "保持常规跟进，持续监控客户收入、风险事项和合规需求变化。"
        lead = "业务"
        partners = "客户成功"
        sla = "14 天"
    return {"priority": priority, "recommended_action": action, "lead_team": lead, "partners": partners, "sla": sla}


def collaboration_type(row: pd.Series) -> str:
    legal = int(row.get("legal_required", 0)) == 1
    product = int(row.get("product_required", 0)) == 1
    if legal and product:
        return "法务+产品"
    if legal:
        return "仅法务"
    if product:
        return "仅产品"
    return "无需介入"


# =========================
# 3. 侧边栏筛选器与联动过滤
# =========================
st.sidebar.header("筛选器")
st.sidebar.caption("筛选后，经营指标、风险分析、客户优先级和行动清单会同步变化。")

region_options = sorted(metrics_raw["region"].dropna().unique().tolist())
industry_options = sorted(metrics_raw["industry"].dropna().unique().tolist())
product_options = sorted(metrics_raw["product_module"].dropna().unique().tolist())
deploy_options = sorted(metrics_raw["deployment_mode"].dropna().unique().tolist())
risk_level_options = sorted(requests_raw["risk_level"].dropna().unique().tolist())
priority_options = [p for p in ["P0", "P1", "P2"] if p in requests_raw["priority"].unique().tolist()]

selected_regions = st.sidebar.multiselect("地区", region_options, default=region_options)
selected_industries = st.sidebar.multiselect("行业", industry_options, default=industry_options)
selected_products = st.sidebar.multiselect("产品模块", product_options, default=product_options)
selected_deploy = st.sidebar.multiselect("部署模式", deploy_options, default=deploy_options)
selected_risk_levels = st.sidebar.multiselect("需求风险等级", risk_level_options, default=risk_level_options)
selected_priorities = st.sidebar.multiselect("需求优先级", priority_options, default=priority_options)

metrics = metrics_raw.copy()
metrics = metrics[metrics["region"].isin(selected_regions)]
metrics = metrics[metrics["industry"].isin(selected_industries)]
metrics = metrics[metrics["product_module"].isin(selected_products)]
metrics = metrics[metrics["deployment_mode"].isin(selected_deploy)]

valid_customer_ids = set(metrics["customer_id"].dropna().unique().tolist())
risks = risks_raw[risks_raw["customer_id"].isin(valid_customer_ids)].copy()
requests = requests_raw[requests_raw["customer_id"].isin(valid_customer_ids)].copy()

risks = risks[risks["region"].isin(selected_regions) & risks["industry"].isin(selected_industries)]
requests = requests[
    requests["region"].isin(selected_regions)
    & requests["industry"].isin(selected_industries)
    & requests["risk_level"].isin(selected_risk_levels)
    & requests["priority"].isin(selected_priorities)
]


# =========================
# 4. 聚合表与评分规则
# =========================
def build_customer_summary(m: pd.DataFrame, r: pd.DataFrame, q: pd.DataFrame) -> pd.DataFrame:
    base = (
        m.groupby("customer_id", as_index=False)
        .agg(
            customer_name=("customer_name", "first"),
            region=("region", "first"),
            industry=("industry", "first"),
            product_module=("product_module", lambda x: x.mode().iat[0] if not x.mode().empty else x.iloc[0]),
            deployment_mode=("deployment_mode", lambda x: x.mode().iat[0] if not x.mode().empty else x.iloc[0]),
            net_revenue_usd=("net_revenue_usd", "sum"),
            api_calls=("api_calls", "sum"),
        )
    )
    high_risk = (
        r.assign(high_risk_flag=lambda x: (x["risk_level"] == "高风险").astype(int))
        .groupby("customer_id", as_index=False)
        .agg(high_risk_count=("high_risk_flag", "sum"), risk_total=("risk_id", "count"))
    )
    req_agg = (
        q.assign(
            p0p1_overdue=lambda x: ((x["priority"].isin(["P0", "P1"])) & (x["is_overdue"] == 1)).astype(int),
            block=lambda x: (x["block_revenue_flag"] == 1).astype(int),
            request_value_usd=lambda x: x["business_value_usd"].fillna(0),
        )
        .groupby("customer_id", as_index=False)
        .agg(
            p0p1_overdue_count=("p0p1_overdue", "sum"),
            block_count=("block", "sum"),
            request_count=("ticket_id", "count"),
            request_value_usd=("request_value_usd", "sum"),
        )
    )
    out = base.merge(high_risk, on="customer_id", how="left").merge(req_agg, on="customer_id", how="left")
    for col in ["high_risk_count", "risk_total", "p0p1_overdue_count", "block_count", "request_count", "request_value_usd"]:
        out[col] = out[col].fillna(0)

    revenue_threshold = out["net_revenue_usd"].median() if not out.empty else 0
    out["revenue_threshold"] = revenue_threshold
    out["revenue_score"] = normalize_score(out["net_revenue_usd"])
    out["risk_score"] = normalize_score(out["high_risk_count"])
    out["overdue_score"] = normalize_score(out["p0p1_overdue_count"])
    out["block_score"] = normalize_score(out["block_count"])
    out["customer_priority_score"] = (
        out["revenue_score"] * 0.40
        + out["risk_score"] * 0.25
        + out["overdue_score"] * 0.20
        + out["block_score"] * 0.15
    )
    actions = out.apply(get_customer_action, axis=1, result_type="expand")
    out = pd.concat([out, actions], axis=1)
    return out.sort_values("customer_priority_score", ascending=False)


def build_request_summary(q: pd.DataFrame) -> pd.DataFrame:
    if q.empty:
        return pd.DataFrame(
            columns=[
                "request_type", "request_count", "business_value_usd", "p0p1_count", "block_count", "dual_team_count", "avg_risk_score",
                "standardization_score", "solution", "lead_team", "partners", "sla"
            ]
        )
    tmp = q.copy()
    tmp["risk_score_num"] = tmp["risk_level"].apply(risk_score_value)
    tmp["p0p1_flag"] = tmp["priority"].isin(["P0", "P1"]).astype(int)
    tmp["dual_team_flag"] = ((tmp["legal_required"] == 1) & (tmp["product_required"] == 1)).astype(int)
    tmp["block_flag"] = (tmp["block_revenue_flag"] == 1).astype(int)
    summary = (
        tmp.groupby("request_type", as_index=False)
        .agg(
            request_count=("ticket_id", "count"),
            business_value_usd=("business_value_usd", "sum"),
            p0p1_count=("p0p1_flag", "sum"),
            block_count=("block_flag", "sum"),
            dual_team_count=("dual_team_flag", "sum"),
            avg_risk_score=("risk_score_num", "mean"),
        )
    )
    summary["freq_score"] = normalize_score(summary["request_count"])
    summary["value_score"] = normalize_score(summary["business_value_usd"])
    summary["block_score"] = normalize_score(summary["block_count"])
    summary["dual_score"] = normalize_score(summary["dual_team_count"])
    summary["standardization_score"] = (
        summary["freq_score"] * 0.25
        + summary["value_score"] * 0.30
        + summary["block_score"] * 0.25
        + summary["dual_score"] * 0.20
    ).round(1)
    solution_rows = summary["request_type"].apply(get_solution_template).apply(pd.Series)
    summary = pd.concat([summary, solution_rows], axis=1)
    return summary.sort_values("standardization_score", ascending=False)


customer_summary = build_customer_summary(metrics, risks, requests)
request_summary = build_request_summary(requests)


# =========================
# 5. 顶部行动结论与 KPI
# =========================
top_region = metrics.groupby("region")["net_revenue_usd"].sum().sort_values(ascending=False).index[0] if not metrics.empty else "暂无"

industry_revenue = metrics.groupby("industry")["net_revenue_usd"].sum().rename("net_revenue_usd")
industry_high_risk = (
    risks.assign(high_risk_flag=(risks["risk_level"] == "高风险").astype(int))
    .groupby("industry")["high_risk_flag"].sum()
    if not risks.empty else pd.Series(dtype=float)
)
industry_joint = pd.concat([industry_revenue, industry_high_risk.rename("high_risk_count")], axis=1).fillna(0)
if not industry_joint.empty:
    industry_joint["joint_score"] = normalize_score(industry_joint["net_revenue_usd"]) * 0.6 + normalize_score(industry_joint["high_risk_count"]) * 0.4
    top_industry = industry_joint["joint_score"].sort_values(ascending=False).index[0]
else:
    top_industry = "暂无"

top_issue = request_summary.iloc[0]["request_type"] if not request_summary.empty else "暂无"
top_block_issue = (
    request_summary.sort_values(["block_count", "business_value_usd"], ascending=False).iloc[0]["request_type"]
    if not request_summary.empty else "暂无"
)

key_conclusion = (
    f"关键判断：当前筛选范围内，收入重点市场为 **{top_region}**，高价值高风险行业重点关注 **{top_industry}**；"
    f"客户层面应优先处理右上象限的高收入高风险客户；需求层面，**{top_issue}** 的标准化优先级最高，"
    f"其中 **{top_block_issue}** 对成交/续费阻塞影响最突出，建议优先沉淀标准 FAQ、合同条款说明、产品能力说明和法务升级路径。"
)
key_conclusion_html = (
    f"关键判断：当前筛选范围内，收入重点市场为 <b>{top_region}</b>，"
    f"高价值高风险行业重点关注 <b>{top_industry}</b>；客户层面应优先处理右上象限的高收入高风险客户；"
    f"需求层面，<b>{top_issue}</b> 的标准化优先级最高，其中 <b>{top_block_issue}</b> 对成交/续费阻塞影响最突出。"
    "建议优先沉淀标准 FAQ、合同条款说明、产品能力说明和法务升级路径。"
)

st.markdown(
    f"""
    <div class="hero">
      <div class="hero-title">腾讯云 AI Agent 出海经营合规决策看板</div>
      <div class="hero-subtitle">经营表现 × 合规风险 × 客户需求响应 × 落地行动清单｜模拟数据作品集 v04｜决策闭环优化版</div>
      <div class="conclusion">{key_conclusion_html}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.expander("查看动态结论文本", expanded=False):
    st.markdown(key_conclusion)

card_cols = st.columns(4)
action_cards = [
    ("市场策略", f"收入重点市场：{top_region}", "识别短期商业化重点市场。", f"继续追踪 {top_region} 高收入客户的产品模块、部署模式和续费状态。"),
    ("行业风险", f"高价值高风险行业：{top_industry}", "高收入行业往往伴随更复杂的客户合规要求。", "提前准备 DPA、日志留存、模型训练数据使用说明，降低售前沟通成本。"),
    ("客户优先级", "优先跟进：右上象限客户", "高收入且高风险客户需要业务、法务、产品共同介入。", "生成重点客户清单，设置 P0/P1 需求 SLA，避免合规问题阻塞成交或续费。"),
    ("标准化建设", f"优先标准化：{top_issue}", "高频、高价值、高阻塞的问题不应反复人工处理。", "沉淀标准 FAQ、合同条款说明、产品能力边界和升级路径。"),
]
for col, (tag, title, body, todo) in zip(card_cols, action_cards):
    with col:
        st.markdown(
            f"""
            <div class="action-card">
                <div class="tag">{tag}</div>
                <div class="title">{title}</div>
                <div class="body">{body}</div>
                <div class="todo"><b>落地动作：</b>{todo}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown(
    f"""
    <div class="solution-strip">
      <div class="solution-title">本轮落地解法｜从“发现问题”到“处理机制”</div>
      <div class="solution-item">
        <b>客户侧：</b>优先处理右上象限高收入高风险客户，形成重点客户跟进清单与 SLA；
        <b>问题侧：</b>优先标准化 {top_issue}、{top_block_issue} 等高频高价值问题；
        <b>组织侧：</b>将客户问题拆成销售可回复、产品需确认、法务需升级三层处理路径，减少重复沟通与临时拉群。
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="playbook-grid">
      <div class="playbook-card">
        <div class="level">L1｜业务可直接回复</div>
        <div class="play-title">沉淀销售 FAQ 与标准话术</div>
        <div class="play-body">适用于认证材料、基础日志说明、常见数据使用边界等重复问题，目标是让业务一线可快速响应。</div>
      </div>
      <div class="playbook-card">
        <div class="level">L2｜产品需确认</div>
        <div class="play-title">输出产品能力与配置边界</div>
        <div class="play-body">适用于日志留存、专属部署、数据不出境、第三方模型调用等问题，明确“能做什么、不能承诺什么”。</div>
      </div>
      <div class="playbook-card">
        <div class="level">L3｜法务需升级</div>
        <div class="play-title">建立合同条款与 DPA 审核路径</div>
        <div class="play-body">适用于模型训练数据使用、DPA、合同责任条款等高风险问题，形成升级机制与 SLA。</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div class='section-title'>经营健康概览｜先看规模，再找风险摩擦点</div>", unsafe_allow_html=True)
st.markdown("<div class='section-caption'>本模块先判断业务盘子是否值得投入，再识别收入背后的合规压力和成交摩擦点。</div>", unsafe_allow_html=True)

k1, k2, k3, k4, k5 = st.columns(5)
net_revenue = metrics["net_revenue_usd"].sum() if not metrics.empty else 0
customer_count = metrics["customer_id"].nunique() if not metrics.empty else 0
high_risk_count = int((risks["risk_level"] == "高风险").sum()) if not risks.empty else 0
p0p1_overdue_count = int(((requests["priority"].isin(["P0", "P1"])) & (requests["is_overdue"] == 1)).sum()) if not requests.empty else 0
block_count = int((requests["block_revenue_flag"] == 1).sum()) if not requests.empty else 0
k1.metric("净收入", fmt_money_wan(net_revenue))
k2.metric("客户数", f"{customer_count:,}")
k3.metric("高风险事项", f"{high_risk_count:,}")
k4.metric("P0/P1 超期需求", f"{p0p1_overdue_count:,}")
k5.metric("阻塞成交/续费工单", f"{block_count:,}")


# =========================
# 6. 图表区：经营诊断
# =========================
st.markdown("<div class='section-title'>一、收入结构与风险联动诊断</div>", unsafe_allow_html=True)
st.markdown("<div class='section-caption'>业务问题：收入来自哪里？趋势是否健康？高收入行业是否同步带来高合规风险？</div>", unsafe_allow_html=True)
st.markdown("<div class='module-brief'><b>经营解读：</b>这一组图用于判断资源投放方向：先看地区收入贡献，再看月度波动，最后把行业收入与高风险事项放在一起，避免只追高收入而忽略合规成本。</div>", unsafe_allow_html=True)

c1, c2 = st.columns([1.05, 1.25])
with c1:
    region_rev = metrics.groupby("region", as_index=False)["net_revenue_usd"].sum().sort_values("net_revenue_usd", ascending=True)
    fig_region = px.bar(
        region_rev,
        x="net_revenue_usd",
        y="region",
        orientation="h",
        text=region_rev["net_revenue_usd"].apply(lambda x: f"{x/10000:.1f}万"),
        title="地区净收入排行：识别重点市场",
        labels={"net_revenue_usd": "净收入（美元）", "region": "地区"},
    )
    fig_region.update_traces(textposition="outside", marker_line_width=0)
    fig_region.update_layout(height=350, margin=dict(l=10, r=30, t=50, b=20), xaxis_tickformat=",.0f")
    st.plotly_chart(fig_region, use_container_width=True)

with c2:
    month_rev = metrics.groupby("month", as_index=False)["net_revenue_usd"].sum().sort_values("month")
    fig_month = px.line(
        month_rev,
        x="month",
        y="net_revenue_usd",
        markers=True,
        title="月度净收入趋势：判断收入波动",
        labels={"month": "月份", "net_revenue_usd": "净收入（美元）"},
    )
    fig_month.update_traces(text=[f"{x/10000:.1f}万" for x in month_rev["net_revenue_usd"]], textposition="top center")
    fig_month.update_layout(height=350, margin=dict(l=10, r=20, t=50, b=20), yaxis_tickformat=",.0f")
    st.plotly_chart(fig_month, use_container_width=True)

industry_df = industry_joint.reset_index().rename(columns={"index": "industry"}) if not industry_joint.empty else pd.DataFrame(columns=["industry", "net_revenue_usd", "high_risk_count"])
if not industry_df.empty:
    industry_df = industry_df.sort_values("net_revenue_usd", ascending=False)
    fig_industry = make_subplots(specs=[[{"secondary_y": True}]])
    fig_industry.add_trace(
        go.Bar(x=industry_df["industry"], y=industry_df["net_revenue_usd"], name="净收入", text=[f"{v/10000:.1f}万" for v in industry_df["net_revenue_usd"]], textposition="outside"),
        secondary_y=False,
    )
    fig_industry.add_trace(
        go.Scatter(x=industry_df["industry"], y=industry_df["high_risk_count"], name="高风险事项数", mode="lines+markers+text", text=industry_df["high_risk_count"].astype(int), textposition="top center"),
        secondary_y=True,
    )
    fig_industry.update_layout(title="行业收入与高风险事项：识别高价值高风险行业", height=420, margin=dict(l=10, r=20, t=60, b=40), legend=dict(orientation="h", y=1.12))
    fig_industry.update_yaxes(title_text="净收入（美元）", secondary_y=False, tickformat=",.0f")
    fig_industry.update_yaxes(title_text="高风险事项数", secondary_y=True)
    st.plotly_chart(fig_industry, use_container_width=True)


# =========================
# 7. 客户优先级引擎
# =========================
st.markdown("<div class='section-title'>二、重点客户协同跟进池</div>", unsafe_allow_html=True)
st.markdown("<div class='section-caption'>业务问题：哪些客户既有业务价值又存在合规复杂度？右上象限客户优先进入业务、法务、产品协同跟进池。</div>", unsafe_allow_html=True)
st.markdown("<div class='module-brief'><b>决策规则：</b>客户优先级分 = 收入得分 40% + 高风险事项 25% + P0/P1 超期 20% + 阻塞工单 15%。分数越高，越应进入重点客户跟进清单。</div>", unsafe_allow_html=True)

if customer_summary.empty:
    st.info("当前筛选条件下暂无客户数据。")
else:
    left, right = st.columns([1.45, 1.0])
    scatter_df = customer_summary.copy()
    scatter_df["net_revenue_wan"] = scatter_df["net_revenue_usd"] / 10000
    scatter_df["pressure_size"] = scatter_df["p0p1_overdue_count"] + scatter_df["block_count"] + 1
    fig_customer = px.scatter(
        scatter_df,
        x="net_revenue_wan",
        y="high_risk_count",
        size="pressure_size",
        color="industry",
        hover_name="customer_id",
        hover_data={
            "customer_name": True,
            "region": True,
            "net_revenue_wan": ":.2f",
            "p0p1_overdue_count": True,
            "block_count": True,
            "customer_priority_score": ":.1f",
            "pressure_size": False,
        },
        title="客户优先级矩阵：高收入 × 高风险",
        labels={"net_revenue_wan": "客户净收入（万美元）", "high_risk_count": "高风险事项数", "industry": "行业"},
    )
    fig_customer.add_vline(x=scatter_df["net_revenue_wan"].mean(), line_dash="dash", line_color="gray", annotation_text="平均收入")
    fig_customer.add_hline(y=scatter_df["high_risk_count"].mean(), line_dash="dash", line_color="gray", annotation_text="平均风险")
    fig_customer.update_layout(height=520, margin=dict(l=10, r=20, t=60, b=40))
    with left:
        st.plotly_chart(fig_customer, use_container_width=True)

    with right:
        top_customer_ids = scatter_df.head(10)["customer_id"].tolist()
        selected_customer = st.selectbox("选择重点客户查看行动建议", top_customer_ids)
        row = scatter_df[scatter_df["customer_id"] == selected_customer].iloc[0]
        st.markdown("#### 客户行动建议")
        st.write(f"**客户 ID：** {row['customer_id']} ｜ **客户名称：** {row['customer_name']}")
        st.write(f"**地区/行业：** {row['region']} / {row['industry']}")
        st.write(f"**净收入：** {fmt_money_wan(row['net_revenue_usd'])}")
        st.write(f"**高风险事项：** {int(row['high_risk_count'])} ｜ **P0/P1 超期：** {int(row['p0p1_overdue_count'])} ｜ **阻塞工单：** {int(row['block_count'])}")
        st.write(f"**客户优先级分：** {row['customer_priority_score']:.1f}")
        st.info(row["recommended_action"])
        st.write(f"**牵头团队：** {row['lead_team']} ｜ **协同团队：** {row['partners']} ｜ **建议 SLA：** {row['sla']}")


# =========================
# 8. 合规问题标准化优先级
# =========================
st.markdown("<div class='section-title'>三、标准化响应优先级与方案沉淀</div>", unsafe_allow_html=True)
st.markdown("<div class='section-caption'>业务问题：哪些客户合规问题不应反复人工处理？用频次、业务价值、阻塞程度和协同成本计算标准化优先级。</div>", unsafe_allow_html=True)
st.markdown("<div class='module-brief'><b>决策规则：</b>标准化优先级分 = 需求频次 25% + 业务价值 30% + 阻塞次数 25% + 双团队介入 20%。高分问题优先沉淀 FAQ、合同条款说明和产品能力说明。</div>", unsafe_allow_html=True)

if request_summary.empty:
    st.info("当前筛选条件下暂无客户合规需求数据。")
else:
    a, b = st.columns([1.25, 1.0])
    req_plot = request_summary.copy()
    req_plot["business_value_wan"] = req_plot["business_value_usd"] / 10000
    fig_req_matrix = px.scatter(
        req_plot,
        x="business_value_wan",
        y="request_count",
        size="p0p1_count",
        color="avg_risk_score",
        hover_name="request_type",
        hover_data={"block_count": True, "dual_team_count": True, "standardization_score": ":.1f", "business_value_wan": ":.2f"},
        title="标准化优先级矩阵：高价值 × 高频次",
        labels={"business_value_wan": "总业务价值（万美元）", "request_count": "需求频次", "avg_risk_score": "平均风险等级"},
        color_continuous_scale="OrRd",
    )
    fig_req_matrix.add_vline(x=req_plot["business_value_wan"].mean(), line_dash="dash", line_color="gray", annotation_text="平均价值")
    fig_req_matrix.add_hline(y=req_plot["request_count"].mean(), line_dash="dash", line_color="gray", annotation_text="平均频次")
    fig_req_matrix.update_layout(height=500, margin=dict(l=10, r=20, t=60, b=40))
    with a:
        st.plotly_chart(fig_req_matrix, use_container_width=True)

    with b:
        st.markdown("#### Top 5 标准化问题")
        top_issue_table = req_plot.head(5)[["request_type", "standardization_score", "request_count", "business_value_usd", "block_count", "dual_team_count", "solution", "lead_team", "partners", "sla"]].copy()
        top_issue_table["business_value_usd"] = top_issue_table["business_value_usd"].apply(fmt_money_wan)
        top_issue_table = top_issue_table.rename(columns={
            "request_type": "需求类型",
            "standardization_score": "标准化优先级分",
            "request_count": "需求数",
            "business_value_usd": "业务价值",
            "block_count": "阻塞数",
            "dual_team_count": "双团队介入",
            "solution": "建议解决方案",
            "lead_team": "牵头团队",
            "partners": "协同团队",
            "sla": "建议 SLA",
        })
        st.dataframe(top_issue_table, use_container_width=True, height=390)


# =========================
# 9. 阻塞问题与协同压力
# =========================
st.markdown("<div class='section-title'>四、成交/续费阻塞与跨团队处理机制</div>", unsafe_allow_html=True)
st.markdown("<div class='section-caption'>业务问题：哪些合规问题正在影响商业转化？哪些问题需要提前定义销售、产品、法务的处理边界？</div>", unsafe_allow_html=True)

x1, x2 = st.columns([1, 1])
with x1:
    if not request_summary.empty:
        block_df = request_summary.sort_values(["block_count", "business_value_usd"], ascending=True).tail(10)
        fig_block = px.bar(
            block_df,
            x="block_count",
            y="request_type",
            orientation="h",
            text=[f"{int(c)}个｜{v/10000:.1f}万" for c, v in zip(block_df["block_count"], block_df["business_value_usd"])],
            title="阻塞成交/续费问题排行",
            labels={"block_count": "阻塞工单数量", "request_type": "需求类型"},
        )
        fig_block.update_traces(textposition="outside")
        fig_block.update_layout(height=450, margin=dict(l=10, r=60, t=60, b=30))
        st.plotly_chart(fig_block, use_container_width=True)

with x2:
    if not requests.empty:
        collab_tmp = requests.copy()
        collab_tmp["协同类型"] = collab_tmp.apply(collaboration_type, axis=1)
        collab_tmp = collab_tmp[collab_tmp["协同类型"].isin(["仅法务", "仅产品", "法务+产品"])]
        collab_df = collab_tmp.groupby(["request_type", "协同类型"], as_index=False)["ticket_id"].count().rename(columns={"ticket_id": "工单数"})
        top_types = collab_df.groupby("request_type")["工单数"].sum().sort_values(ascending=False).head(10).index.tolist()
        collab_df = collab_df[collab_df["request_type"].isin(top_types)]
        fig_collab = px.bar(
            collab_df,
            x="工单数",
            y="request_type",
            color="协同类型",
            orientation="h",
            title="协同压力分析：法务 × 产品",
            labels={"request_type": "需求类型"},
        )
        fig_collab.update_layout(height=450, margin=dict(l=10, r=20, t=60, b=30), legend=dict(orientation="h", y=1.12))
        st.plotly_chart(fig_collab, use_container_width=True)


# =========================
# 10. 行动清单与下载
# =========================
st.markdown("<div class='section-title'>五、可执行行动清单与下载</div>", unsafe_allow_html=True)
st.markdown("<div class='section-caption'>把图表结论落到执行层：优先处理谁、处理什么、为什么处理、由谁牵头、建议 SLA 是多少。</div>", unsafe_allow_html=True)

tab_customer, tab_issue, tab_block = st.tabs(["重点客户跟进清单", "标准化需求处理清单", "阻塞成交/续费清单"])

with tab_customer:
    customer_action = customer_summary.head(15)[[
        "priority", "customer_id", "customer_name", "region", "industry", "net_revenue_usd", "high_risk_count", "p0p1_overdue_count", "block_count", "customer_priority_score", "recommended_action", "lead_team", "partners", "sla"
    ]].copy()
    customer_action["net_revenue_usd"] = customer_action["net_revenue_usd"].apply(fmt_money_wan)
    customer_action = customer_action.rename(columns={
        "priority": "优先级", "customer_id": "客户ID", "customer_name": "客户名称", "region": "地区", "industry": "行业",
        "net_revenue_usd": "净收入", "high_risk_count": "高风险事项", "p0p1_overdue_count": "P0/P1超期", "block_count": "阻塞工单",
        "customer_priority_score": "客户优先级分", "recommended_action": "建议动作", "lead_team": "牵头团队", "partners": "协同团队", "sla": "建议SLA"
    })
    st.dataframe(customer_action, use_container_width=True, height=430)
    st.download_button("下载重点客户跟进清单 CSV", data=customer_action.to_csv(index=False).encode("utf-8-sig"), file_name="重点客户跟进清单.csv", mime="text/csv")

with tab_issue:
    issue_action = request_summary[[
        "request_type", "standardization_score", "request_count", "business_value_usd", "p0p1_count", "block_count", "dual_team_count", "solution", "lead_team", "partners", "sla"
    ]].copy()
    issue_action["business_value_usd"] = issue_action["business_value_usd"].apply(fmt_money_wan)
    issue_action = issue_action.rename(columns={
        "request_type": "需求类型", "standardization_score": "标准化优先级分", "request_count": "需求数", "business_value_usd": "业务价值",
        "p0p1_count": "P0/P1数", "block_count": "阻塞数", "dual_team_count": "双团队介入", "solution": "建议解决方案",
        "lead_team": "牵头团队", "partners": "协同团队", "sla": "建议SLA"
    })
    st.dataframe(issue_action, use_container_width=True, height=430)
    st.download_button("下载标准化需求处理清单 CSV", data=issue_action.to_csv(index=False).encode("utf-8-sig"), file_name="标准化需求处理清单.csv", mime="text/csv")

with tab_block:
    block_list = requests[requests["block_revenue_flag"] == 1].copy()
    if not block_list.empty:
        block_list["业务价值"] = block_list["business_value_usd"].apply(fmt_money_wan)
        block_list["建议解决方案"] = block_list["request_type"].apply(lambda x: get_solution_template(x)["solution"])
        block_view = block_list[["ticket_id", "customer_id", "customer_name", "region", "industry", "request_type", "priority", "risk_level", "业务价值", "status", "is_overdue", "建议解决方案"]].rename(columns={
            "ticket_id": "工单ID", "customer_id": "客户ID", "customer_name": "客户名称", "region": "地区", "industry": "行业",
            "request_type": "需求类型", "priority": "优先级", "risk_level": "风险等级", "status": "状态", "is_overdue": "是否超期"
        })
    else:
        block_view = pd.DataFrame()
    st.dataframe(block_view, use_container_width=True, height=430)
    st.download_button("下载阻塞成交/续费问题清单 CSV", data=block_view.to_csv(index=False).encode("utf-8-sig"), file_name="阻塞成交续费问题清单.csv", mime="text/csv")


st.markdown("---")
st.markdown(
    "<div class='small-note'>说明：本看板基于模拟数据构建，用于展示 AI 出海经营分析、合规风险识别、客户需求响应和工具化落地能力；不代表腾讯云真实经营数据。</div>",
    unsafe_allow_html=True,
)
