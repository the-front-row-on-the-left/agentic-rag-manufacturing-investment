from __future__ import annotations

from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from src.agents.company_summary import CompanySummaryAgent
from src.agents.competitor_analysis import CompetitorAnalysisAgent
from src.agents.investment_decision import InvestmentDecisionAgent
from src.agents.market_analysis import MarketAnalysisAgent
from src.agents.report_writer import ReportWriterAgent
from src.agents.startup_search import StartupSearchAgent
from src.agents.tech_analysis import TechAnalysisAgent
from src.config import Settings
from src.rag.index_builder import VectorStoreManager
from src.rag.retriever import AgenticRAGRetriever
from src.state import GraphState
from src.tools.web_search import TavilySearchTool

STARTUP_SEARCH_NODE = "startup_search"
COMPANY_SUMMARY_NODE = "company_summary"
REPORT_WRITER_NODE = "report_writer"


def startup_router(state: GraphState) -> str:
    # startup_search owns both the initial entry and candidate re-entry path.
    if state.get("selected_startup") is None or state.get("search_done", False):
        return REPORT_WRITER_NODE
    return COMPANY_SUMMARY_NODE


def decision_router(state: GraphState) -> str:
    decision = state.get("investment_decision")
    if not decision:
        return REPORT_WRITER_NODE

    # Once a candidate has been evaluated, the graph keeps iterating until the
    # full candidate list is exhausted, then writes a single final report.
    candidate_startups = state.get("candidate_startups", [])
    current_index = state.get("current_index", -1)
    if current_index + 1 < len(candidate_startups):
        return STARTUP_SEARCH_NODE
    return REPORT_WRITER_NODE


def build_graph(settings: Settings):
    llm = ChatOpenAI(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        temperature=0,
    )
    search_tool = TavilySearchTool(api_key=settings.tavily_api_key)

    vector_store_manager = VectorStoreManager(settings=settings)
    vector_store = vector_store_manager.load_existing()
    rag_retriever = AgenticRAGRetriever(llm=llm, vector_store=vector_store)

    startup_search_agent = StartupSearchAgent(llm, settings, search_tool)
    company_summary_agent = CompanySummaryAgent(llm, settings, search_tool)
    tech_analysis_agent = TechAnalysisAgent(llm, settings, search_tool, rag_retriever)
    market_analysis_agent = MarketAnalysisAgent(
        llm, settings, search_tool, rag_retriever
    )
    competitor_analysis_agent = CompetitorAnalysisAgent(llm, settings, search_tool)
    investment_decision_agent = InvestmentDecisionAgent(llm, settings)
    report_writer_agent = ReportWriterAgent(llm, settings)

    graph = StateGraph(GraphState)

    graph.add_node(STARTUP_SEARCH_NODE, startup_search_agent)
    graph.add_node(COMPANY_SUMMARY_NODE, company_summary_agent)
    graph.add_node("tech_analysis", tech_analysis_agent)
    graph.add_node("market_analysis", market_analysis_agent)
    graph.add_node("competitor_analysis", competitor_analysis_agent)
    graph.add_node("investment_decision", investment_decision_agent)
    graph.add_node(REPORT_WRITER_NODE, report_writer_agent)

    # Every run starts with startup discovery before any downstream analysis.
    graph.add_edge(START, STARTUP_SEARCH_NODE)
    graph.add_conditional_edges(
        STARTUP_SEARCH_NODE,
        startup_router,
        {
            COMPANY_SUMMARY_NODE: COMPANY_SUMMARY_NODE,
            REPORT_WRITER_NODE: REPORT_WRITER_NODE,
        },
    )

    graph.add_edge(COMPANY_SUMMARY_NODE, "tech_analysis")
    graph.add_edge(COMPANY_SUMMARY_NODE, "market_analysis")
    graph.add_edge("tech_analysis", "competitor_analysis")
    graph.add_edge("market_analysis", "competitor_analysis")
    graph.add_edge("competitor_analysis", "investment_decision")
    graph.add_conditional_edges(
        "investment_decision",
        decision_router,
        {
            STARTUP_SEARCH_NODE: STARTUP_SEARCH_NODE,
            REPORT_WRITER_NODE: REPORT_WRITER_NODE,
        },
    )
    graph.add_edge(REPORT_WRITER_NODE, END)

    return graph.compile()
