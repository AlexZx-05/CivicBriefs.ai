# app/api/routes/agents.py
from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse
from app.agents.news_agent import NewsAgent
from app.agents.planner_agent import PlannerAgent
from app.api.routes.auth import _current_user
from app.services.report_store import report_store


router = APIRouter(prefix="/agents", tags=["agents"])

@router.post("/news")
def run_news_agent():
    """
    Trigger the NewsAgent to fetch and embed UPSC-relevant news.
    """
    agent = NewsAgent(
        query="UPSC OR civil services OR current affairs OR Indian polity",
        fetch_limit=10
    )
    agent.run()
    return {"status": "success", "message": "NewsAgent executed successfully ✅"}


@router.post("/planner")
def generate_planner(payload: dict = Body(...)):
    """Generate a personalized UPSC planner from the provided performance JSON.

    Example request body:
    {
        "user_id": "U_45",
        "performance": {"History":52, "Polity":72, "Geography":35}
    }
    """
    perf = payload.get("performance") if isinstance(payload.get("performance"), dict) else payload

    if not isinstance(perf, dict):
        raise HTTPException(status_code=400, detail="performance must be a dict mapping subjects to scores")

    user_id = payload.get("user_id") if isinstance(payload, dict) else None
    user_email = None
    if isinstance(payload, dict):
        user_email = payload.get("user_email") or payload.get("email")

    planner = PlannerAgent()
    out = planner.generate(perf, user_id=user_id, user_email=user_email)
    return JSONResponse(content={"status": "success", "planner": out})


@router.get("/planner/test")
def create_planner_test(questions_per_section: int = 15):
    agent = PlannerAgent()
    try:
        test = agent.prepare_test(questions_per_section=questions_per_section)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return JSONResponse(content={"status": "success", "test": test})


@router.post("/planner/test/submit")
def submit_planner_test(payload: dict = Body(...)):
    user_id = payload.get("user_id")
    answers = payload.get("answers")

    if answers is None:
        answers = {}
    if not isinstance(answers, dict):
        raise HTTPException(status_code=400, detail="answers must be a mapping of question_id to selected option")

    agent = PlannerAgent()

    try:
        result = agent.evaluate_test(user_id=user_id, answers=answers)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return JSONResponse(content={"status": "success", "result": result})


@router.get("/planner/report/latest")
def latest_planner_report(context=Depends(_current_user)):
    user, _ = context
    latest = report_store.latest_for_user(user_id=user.get("id"), user_email=user.get("email"))
    if latest is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No planner reports available yet.")
    return JSONResponse(content={"status": "success", "report": latest})


@router.get("/planner/report/history")
def planner_report_history(limit: int = 20, context=Depends(_current_user)):
    user, _ = context
    history = report_store.history_for_user(
        user_id=user.get("id"),
        user_email=user.get("email"),
        limit=limit,
    )
    return JSONResponse(content={"status": "success", "history": history})


@router.get("/planner/ui", response_class=HTMLResponse)
def planner_ui():
    html = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>CivicBriefs Planner Workspace</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@600;700;800&family=Public+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            color-scheme: light;
            --bg: #e2ebe8;
            --panel: #f8fbfa;
            --panel-strong: #ffffff;
            --accent: #1f7b5e;
            --accent-deep: #165e49;
            --accent-soft: #dbe7e1;
            --text: #16342e;
            --muted: #587069;
            --border: #c8d7d1;
            --error: #dc2626;
            --success: #16a34a;
        }

        * {
            box-sizing: border-box;
        }

        html, body {
            width: 100%;
            max-width: 100%;
            overflow-x: hidden;
        }

        body {
            margin: 0;
            min-height: 100vh;
            font-family: 'Public Sans', 'Segoe UI', sans-serif;
            background:
                radial-gradient(circle at 10% 8%, rgba(255,255,255,0.55), transparent 34%),
                radial-gradient(circle at 88% 6%, rgba(255,255,255,0.45), transparent 30%),
                linear-gradient(165deg, #d7e3de 0%, #e5eeea 48%, #d0ddd8 100%);
            color: var(--text);
            -webkit-font-smoothing: antialiased;
            text-rendering: optimizeLegibility;
        }

        body.modal-open {
            overflow: hidden;
        }

        .page {
            width: min(100vw, 100%);
            max-width: none;
            margin: 0;
            padding: 28px clamp(8px, 1.2vw, 18px) 40px;
        }

        header {
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin-bottom: 24px;
        }

        header h1 {
            font-size: 28px;
            font-weight: 800;
            letter-spacing: -0.02em;
            margin: 0;
            font-family: 'Manrope', 'Public Sans', sans-serif;
        }

        header p {
            margin: 0;
            color: var(--muted);
            font-size: 15px;
            max-width: 720px;
        }

        .card {
            background: var(--panel);
            border-radius: 16px;
            box-shadow: 0 24px 50px rgba(22, 42, 35, 0.11), inset 0 1px 0 rgba(255,255,255,0.8);
            border: 1px solid var(--border);
            padding: 24px;
            margin-bottom: 24px;
        }

        .controls {
            display: grid;
            gap: 16px;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            margin-bottom: 12px;
        }

        label {
            display: flex;
            flex-direction: column;
            gap: 8px;
            font-weight: 500;
            font-size: 14px;
            color: var(--muted);
        }

        input, select {
            padding: 10px 12px;
            border-radius: 10px;
            border: 1px solid var(--border);
            font-size: 15px;
            background: var(--panel-strong);
            color: var(--text);
            transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }

        input:focus, select:focus {
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(31, 123, 94, 0.2);
        }

        button.primary {
            padding: 12px 18px;
            background: linear-gradient(180deg, var(--accent), var(--accent-deep));
            color: #ffffff;
            border: none;
            border-radius: 12px;
            font-size: 15px;
            font-weight: 700;
            font-family: 'Manrope', 'Public Sans', sans-serif;
            cursor: pointer;
            transition: transform 0.1s ease, box-shadow 0.2s ease;
        }

        button.primary:hover {
            transform: translateY(-1px);
            box-shadow: 0 12px 24px rgba(29, 108, 82, 0.28);
        }

        button.secondary {
            padding: 12px 18px;
            background: linear-gradient(180deg, #ffffff, #f3f8f6);
            border: 1px solid var(--border);
            color: var(--text);
            border-radius: 12px;
            font-size: 15px;
            font-weight: 700;
            font-family: 'Manrope', 'Public Sans', sans-serif;
            cursor: pointer;
        }

        .section {
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 20px;
            margin-bottom: 20px;
            background: var(--panel-strong);
        }

        .section h3 {
            margin: 0 0 12px;
            font-size: 20px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .section h3 span {
            background: var(--accent-soft);
            color: var(--accent);
            border-radius: 8px;
            padding: 2px 12px;
            font-size: 13px;
            letter-spacing: 0.06em;
        }

        .question {
            border-radius: 12px;
            border: 1px solid var(--border);
            padding: 16px;
            margin-bottom: 0;
            transition: border-color 0.2s ease;
        }

        .question h4 {
            margin: 0 0 8px;
            font-size: 16px;
            font-weight: 600;
        }

        .meta {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 12px;
            font-size: 13px;
            color: var(--muted);
        }

        .options {
            display: grid;
            gap: 10px;
            grid-template-columns: 1fr;
        }

        .option {
            display: flex;
            align-items: center;
            gap: 10px;
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 12px 14px;
            cursor: pointer;
            transition: border-color 0.2s ease, background 0.2s ease;
            width: 100%;
        }

        .option input {
            margin: 0;
            cursor: pointer;
        }

        .option:hover {
            border-color: var(--accent);
            background: rgba(31, 123, 94, 0.08);
        }

        #statusBar {
            font-size: 14px;
            color: var(--muted);
            margin-top: 12px;
        }

        #statusBar.error {
            color: var(--error);
        }

        #statusBar.success {
            color: var(--success);
        }

        .report-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 18px;
        }

        .insight-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 12px;
            margin-bottom: 14px;
        }

        .insight-tile {
            border: 1px solid var(--border);
            border-radius: 12px;
            background: var(--panel-strong);
            padding: 12px 14px;
        }

        .insight-tile .k {
            margin: 0 0 6px;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: var(--muted);
            font-weight: 700;
        }

        .insight-tile .v {
            margin: 0;
            font-size: 20px;
            font-weight: 800;
            color: var(--text);
            font-family: 'Manrope', 'Public Sans', sans-serif;
        }

        .result-card {
            border: 1px solid var(--border);
            border-radius: 12px;
            background: #ffffff;
            padding: 14px;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.85);
        }

        .result-card h4 {
            margin: 0 0 6px;
            font-size: 16px;
            font-family: 'Manrope', 'Public Sans', sans-serif;
        }

        .result-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
            margin-bottom: 8px;
            font-size: 13px;
            color: var(--muted);
        }

        .result-badge {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 3px 8px;
            font-size: 11px;
            font-weight: 700;
            border: 1px solid transparent;
        }

        .result-badge.strong {
            background: rgba(22, 101, 52, 0.12);
            color: #166534;
            border-color: rgba(22, 101, 52, 0.28);
        }

        .result-badge.average {
            background: rgba(180, 83, 9, 0.12);
            color: #b45309;
            border-color: rgba(180, 83, 9, 0.32);
        }

        .result-badge.weak {
            background: rgba(185, 28, 28, 0.12);
            color: #b91c1c;
            border-color: rgba(185, 28, 28, 0.3);
        }

        .result-progress {
            position: relative;
            height: 8px;
            border-radius: 999px;
            border: 1px solid rgba(190, 209, 201, 0.8);
            background: rgba(20, 75, 61, 0.08);
            overflow: hidden;
        }

        .result-progress > span {
            display: block;
            height: 100%;
            border-radius: 999px;
            background: linear-gradient(90deg, #1f7b5e 0%, #2f9a7a 100%);
        }

        .pill {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 6px 12px;
            background: var(--accent-soft);
            color: var(--accent);
            border-radius: 999px;
            font-size: 13px;
            font-weight: 600;
        }

        .history {
            border-top: 1px solid var(--border);
            padding-top: 16px;
            margin-top: 16px;
        }

        .history-item {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px dashed var(--border);
            font-size: 14px;
        }

        .history-item:last-child {
            border-bottom: none;
        }

        .chart-shell {
            margin-top: 24px;
            border: 1px solid var(--border);
            border-radius: 14px;
            background: var(--panel-strong);
            padding: 14px;
        }

        .chart-canvas-wrap {
            position: relative;
            width: 100%;
            height: clamp(260px, 34vh, 380px);
        }

        .chart-head {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
            flex-wrap: wrap;
            margin-bottom: 10px;
        }

        .chart-head h3 {
            margin: 0;
            font-size: 18px;
            font-family: 'Manrope', 'Public Sans', sans-serif;
        }

        .chart-sub {
            margin: 0;
            color: var(--muted);
            font-size: 13px;
        }

        .report-actions {
            margin-top: 16px;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }

        .hidden {
            display: none;
        }

        canvas {
            max-width: 100%;
        }

        .focus-shell {
            display: grid;
            grid-template-rows: auto 1fr auto;
            min-height: calc(100vh - 20px);
            gap: 14px;
            height: calc(100vh - 20px);
        }

        .focus-topbar {
            border: 1px solid var(--border);
            border-radius: 14px;
            background: var(--panel-strong);
            padding: 14px 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
        }

        .focus-topbar h2 {
            margin: 0;
            font-size: 22px;
            font-family: 'Manrope', 'Public Sans', sans-serif;
        }

        .focus-metrics {
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }

        .timer-pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            border-radius: 999px;
            border: 1px solid var(--border);
            background: #fff;
            color: #143831;
            font-size: 13px;
            font-weight: 700;
            font-family: 'Manrope', 'Public Sans', sans-serif;
        }

        .focus-layout {
            display: grid;
            grid-template-columns: minmax(0, 1fr) 280px;
            gap: 14px;
            align-items: stretch;
            min-height: 0;
            overflow: hidden;
        }

        .focus-main {
            border: 1px solid var(--border);
            border-radius: 14px;
            background: var(--panel-strong);
            padding: 16px;
            min-height: 0;
            display: flex;
            flex-direction: column;
            overflow: auto;
        }

        .focus-question-head {
            display: flex;
            align-items: baseline;
            justify-content: space-between;
            gap: 12px;
            flex-wrap: wrap;
            margin-bottom: 10px;
        }

        .focus-question-head h3 {
            margin: 0;
            font-size: 20px;
            font-family: 'Manrope', 'Public Sans', sans-serif;
        }

        .focus-question-head p {
            margin: 0;
            color: var(--muted);
            font-size: 14px;
            font-weight: 600;
        }

        .focus-sidebar {
            border: 1px solid var(--border);
            border-radius: 14px;
            background: var(--panel-strong);
            padding: 12px;
            position: relative;
            top: auto;
            height: 100%;
            min-height: 100%;
            display: flex;
            flex-direction: column;
            gap: 8px;
            overflow: auto;
        }

        .focus-sidebar h3 {
            margin: 0 0 8px;
            font-size: 15px;
            font-family: 'Manrope', 'Public Sans', sans-serif;
        }

        .palette-section {
            margin-bottom: 8px;
        }

        .palette-title {
            margin: 0 0 5px;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: var(--muted);
            font-weight: 700;
        }

        .palette-grid {
            display: grid;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            gap: 6px;
        }

        .section-tabs {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 6px;
            margin-bottom: 8px;
        }

        .section-tab {
            border: 1px solid var(--border);
            border-radius: 10px;
            background: #fff;
            color: #35554d;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.02em;
            text-transform: uppercase;
            padding: 7px 8px;
            cursor: pointer;
            font-family: 'Manrope', 'Public Sans', sans-serif;
            text-align: center;
            line-height: 1.1;
            min-width: 0;
        }

        .section-tab.active {
            background: linear-gradient(180deg, var(--accent), var(--accent-deep));
            color: #fff;
            border-color: transparent;
            box-shadow: 0 8px 18px rgba(29, 108, 82, 0.2);
        }

        .palette-btn {
            border: 1px solid var(--border);
            border-radius: 9px;
            background: #fff;
            color: #34514a;
            padding: 6px 0;
            font-size: 11px;
            font-weight: 700;
            cursor: pointer;
            font-family: 'Manrope', 'Public Sans', sans-serif;
            min-height: 34px;
        }

        .palette-btn.current {
            background: #176149;
            border-color: #176149;
            color: #fff;
        }

        .palette-btn.answered {
            background: #e4f2ec;
            border-color: #9bc7b6;
            color: #135240;
        }

        .palette-btn.review {
            background: #fff4df;
            border-color: #edc77f;
            color: #8f5d05;
        }

        .palette-legend {
            margin-top: 6px;
            display: grid;
            gap: 4px;
            font-size: 12px;
            color: var(--muted);
        }

        #paletteArea {
            flex: 0 0 auto;
            min-height: auto;
            overflow: visible;
            padding-right: 0;
        }

        .legend-row {
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .legend-dot {
            width: 10px;
            height: 10px;
            border-radius: 999px;
            border: 1px solid var(--border);
            background: #fff;
        }

        .legend-dot.current { background: #176149; border-color: #176149; }
        .legend-dot.answered { background: #cde5dc; border-color: #9bc7b6; }
        .legend-dot.review { background: #ffdf9d; border-color: #edc77f; }

        .focus-footer {
            border: 1px solid var(--border);
            border-radius: 14px;
            background: var(--panel-strong);
            padding: 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
            flex-wrap: wrap;
            position: sticky;
            bottom: max(8px, env(safe-area-inset-bottom));
            z-index: 40;
            box-shadow: 0 12px 28px rgba(22, 42, 35, 0.12);
        }

        #testArea {
            display: grid;
            gap: 12px;
            align-content: start;
        }

        .focus-footer .left,
        .focus-footer .center,
        .focus-footer .right {
            display: flex;
            gap: 10px;
            align-items: center;
        }

        body.exam-mode .page {
            padding: 0;
            height: 100vh;
            overflow: hidden;
        }

        body.exam-mode .page > header,
        body.exam-mode .page > section.card:not(#testCard) {
            display: none !important;
        }

        body.exam-mode #testCard {
            display: block !important;
            margin: 0;
            border-radius: 0;
            border: none;
            box-shadow: none;
            min-height: 100vh;
            height: 100vh;
            padding: 10px;
            background: rgba(241, 247, 244, 0.95);
            overflow: hidden;
        }

        .modal-backdrop {
            position: fixed;
            inset: 0;
            background: rgba(15, 23, 42, 0.45);
            display: none;
            align-items: center;
            justify-content: center;
            padding: 16px;
            z-index: 2000;
        }

        .modal-backdrop.show {
            display: flex;
        }

        .modal {
            width: min(680px, 100%);
            background: var(--panel);
            border-radius: 16px;
            border: 1px solid var(--border);
            box-shadow: 0 24px 50px rgba(22, 42, 35, 0.2);
            padding: 24px;
        }

        .modal h2 {
            margin: 0 0 8px;
            font-size: 24px;
            letter-spacing: -0.01em;
        }

        .modal p {
            margin: 0;
            color: var(--muted);
            font-size: 15px;
        }

        .instruction-list {
            margin: 16px 0 0;
            display: grid;
            gap: 12px;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        }

        .instruction-card {
            border: 1px solid var(--border);
            border-radius: 12px;
            background: var(--panel-strong);
            padding: 12px 13px;
        }

        .instruction-card h4 {
            margin: 0 0 6px;
            font-size: 14px;
            font-family: 'Manrope', 'Public Sans', sans-serif;
            color: #12342d;
        }

        .instruction-card p {
            margin: 0;
            font-size: 13px;
            color: #2f4b45;
            line-height: 1.45;
        }

        .marking-strip {
            margin-top: 12px;
            border: 1px solid var(--border);
            border-radius: 12px;
            background: var(--panel-strong);
            padding: 12px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
        }

        .marking-cell {
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 10px;
            background: #fbfdfc;
        }

        .marking-cell .k {
            margin: 0 0 4px;
            font-size: 12px;
            color: var(--muted);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        .marking-cell .v {
            margin: 0;
            font-size: 18px;
            font-weight: 800;
            color: #12342d;
            font-family: 'Manrope', 'Public Sans', sans-serif;
        }

        .check-row {
            margin-top: 16px;
            display: flex;
            align-items: flex-start;
            gap: 10px;
            font-size: 14px;
            color: #2f4b45;
        }

        .check-row input {
            margin-top: 2px;
        }

        .submit-confirm__stats {
            margin-top: 12px;
            border: 1px solid var(--border);
            border-radius: 12px;
            background: var(--panel-strong);
            padding: 12px;
            display: grid;
            grid-template-columns: repeat(3, minmax(120px, 1fr));
            gap: 8px;
        }

        .submit-confirm__stats .cell {
            border: 1px solid rgba(200, 215, 209, 0.85);
            border-radius: 10px;
            padding: 8px 10px;
            background: #fff;
        }

        .submit-confirm__stats .k {
            margin: 0 0 4px;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--muted);
            font-weight: 700;
        }

        .submit-confirm__stats .v {
            margin: 0;
            font-size: 20px;
            font-weight: 800;
            color: #12372f;
            font-family: 'Manrope', 'Public Sans', sans-serif;
        }

        .submit-confirm__warn {
            margin-top: 10px;
            border: 1px solid rgba(180, 83, 9, 0.28);
            background: rgba(180, 83, 9, 0.08);
            color: #9a4b08;
            border-radius: 10px;
            padding: 10px 12px;
            font-size: 13px;
            line-height: 1.45;
        }

        .submit-confirm__next {
            margin-top: 10px;
            border: 1px solid rgba(31, 123, 94, 0.24);
            background: rgba(31, 123, 94, 0.07);
            color: #14473a;
            border-radius: 10px;
            padding: 10px 12px;
            font-size: 13px;
            line-height: 1.45;
        }

        .submit-confirm__next strong {
            display: inline-block;
            margin-bottom: 5px;
            color: #0f4b3b;
        }

        .submit-confirm__next ul {
            margin: 0;
            padding-left: 18px;
            display: grid;
            gap: 3px;
        }

        .post-submit-card {
            border: 1px solid rgba(31, 123, 94, 0.3);
            border-radius: 12px;
            background: linear-gradient(180deg, rgba(246, 252, 249, 1), rgba(236, 247, 242, 1));
            padding: 12px 14px;
            margin-bottom: 14px;
        }

        .post-submit-card h4 {
            margin: 0 0 6px;
            font-size: 15px;
            font-family: 'Manrope', 'Public Sans', sans-serif;
            color: #123d32;
        }

        .post-submit-card ul {
            margin: 0;
            padding-left: 18px;
            color: #245247;
            font-size: 13px;
            line-height: 1.45;
            display: grid;
            gap: 3px;
        }

        .modal-actions {
            margin-top: 18px;
            display: flex;
            justify-content: flex-end;
            gap: 10px;
            flex-wrap: wrap;
        }

        @media (max-width: 640px) {
            header h1 {
                font-size: 24px;
            }

            .card {
                padding: 20px;
            }

            .section {
                padding: 16px;
            }

            .options {
                grid-template-columns: 1fr;
            }

            .focus-layout {
                grid-template-columns: 1fr;
            }

            .focus-sidebar {
                position: static;
                height: auto;
                min-height: 0;
                overflow: visible;
            }

            .section-tabs {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }

            .palette-grid {
                grid-template-columns: repeat(5, minmax(0, 1fr));
            }

            .focus-main {
                min-height: auto;
            }

            .focus-footer {
                position: static;
            }

            .chart-canvas-wrap {
                height: 240px;
            }

            .submit-confirm__stats {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="page">
        <header>
            <h1>CivicBriefs Planner Lab</h1>
            <p>Launch an adaptive sectional mock, track accuracy in real time, and review personalised feedback with a study plan tailored to your latest attempt.</p>
        </header>

        <section class="card" id="setupCard">
            <div class="controls">
                <label>
                    User identifier (email, phone or Mongo _id)
                    <input id="userId" placeholder="Optional" autocomplete="off" />
                </label>
                <label>
                    Questions per section
                    <select id="qCount">
                        <option value="10">10</option>
                        <option value="15" selected>15</option>
                        <option value="20">20</option>
                    </select>
                </label>
            </div>
            <div style="display:flex; gap:12px; flex-wrap:wrap;">
                <button class="primary" id="startBtn">Start Fresh Test</button>
                <button class="secondary" id="resetBtn">Clear Answers</button>
            </div>
            <div id="statusBar"></div>
        </section>

        <section class="card" id="testCard" style="display:none;">
            <div class="focus-shell">
                <div class="focus-topbar">
                    <h2>CivicBriefs Mock Test</h2>
                    <div class="focus-metrics">
                        <div class="pill" id="progressPill">0% completed</div>
                        <div class="timer-pill" id="timerPill">Time left: 00:00:00</div>
                    </div>
                </div>
                <div class="focus-layout">
                    <div class="focus-main">
                        <div class="focus-question-head">
                            <h3 id="questionSectionLabel">Section</h3>
                            <p id="questionIndexLabel">Question 1 of 1</p>
                        </div>
                        <div id="testArea"></div>
                    </div>
                    <aside class="focus-sidebar">
                        <h3>Question Palette</h3>
                        <div class="section-tabs" id="sectionTabs"></div>
                        <div id="paletteArea"></div>
                        <div class="palette-legend">
                            <div class="legend-row"><span class="legend-dot current"></span><span>Current</span></div>
                            <div class="legend-row"><span class="legend-dot answered"></span><span>Answered</span></div>
                            <div class="legend-row"><span class="legend-dot review"></span><span>Marked for review</span></div>
                        </div>
                    </aside>
                </div>
                <div class="focus-footer">
                    <div class="left">
                        <button class="secondary" id="markReviewBtn">Mark for review</button>
                    </div>
                    <div class="center">
                        <button class="secondary" id="prevBtn">Previous</button>
                        <button class="secondary" id="nextBtn">Next</button>
                    </div>
                    <div class="right">
                        <button class="primary" id="submitBtn">Submit Test</button>
                    </div>
                </div>
            </div>
        </section>

        <section class="card hidden" id="reportCard">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
                <h2 style="margin:0; font-size:22px;">Performance Insights</h2>
                <div class="pill" id="overallScore"></div>
            </div>
            <p id="resultNarrative" style="margin:0 0 14px; color: var(--muted);"></p>
            <div id="postSubmitSummary" class="post-submit-card"></div>
            <div class="insight-grid" id="resultSummaryGrid"></div>
            <div class="section" id="sectionHealthBlock">
                <h3 style="margin:0 0 10px; font-size:18px;">Section Strength Analysis</h3>
                <div id="sectionHealthContent" style="display:grid; gap:8px;"></div>
            </div>
            <div class="section" id="focusTopicsBlock">
                <h3 style="margin:0 0 10px; font-size:18px;">Priority Focus Topics</h3>
                <div id="focusTopicsContent" style="display:grid; gap:8px;"></div>
            </div>
            <div class="report-grid" id="sectionGrid"></div>
            <div class="section" id="answerReviewBlock">
                <h3 style="margin:0 0 10px; font-size:18px;">Answer Review (Right/Wrong)</h3>
                <div id="answerReviewContent" style="display:grid; gap:8px;"></div>
            </div>
            <div class="chart-shell">
                <div class="chart-head">
                    <div>
                        <h3>You vs Topper Benchmark</h3>
                        <p class="chart-sub">Section-wise comparison against 95% target benchmark.</p>
                    </div>
                    <button class="secondary" id="downloadAttemptBtn" type="button">Download Test Paper</button>
                </div>
                <div class="chart-canvas-wrap">
                    <canvas id="progressChart"></canvas>
                </div>
            </div>
            <div class="history" id="historyBlock"></div>
            <div class="report-actions">
                <a href="/dashboard" class="secondary" style="text-decoration:none; display:inline-flex; align-items:center;">Back to Home</a>
            </div>
        </section>

        <section class="card hidden" id="planCard">
            <h2 style="margin:0 0 16px; font-size:22px;">Recommended Study Plan</h2>
            <div id="planContent" style="display:grid; gap:16px;"></div>
        </section>

        <section class="card hidden" id="jsonCard">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <h2 style="margin:0; font-size:22px;">Raw Test Report (JSON)</h2>
                <button class="secondary" id="downloadJsonBtn" style="white-space:nowrap;">Download JSON</button>
            </div>
            <pre id="jsonContent" style="max-height:320px; overflow:auto; background:#0f172a; color:#e2e8f0; padding:16px; border-radius:12px; font-size:13px; line-height:1.45;"></pre>
        </section>
    </div>

    <div class="modal-backdrop" id="instructionModal" aria-hidden="true">
        <div class="modal" role="dialog" aria-modal="true" aria-labelledby="instructionTitle">
            <h2 id="instructionTitle">Read Instructions Before Starting</h2>
            <p>Please review the test rules carefully. Once started, attempt all questions in one flow for best evaluation quality.</p>
            <div class="marking-strip">
                <div class="marking-cell">
                    <p class="k">Awarded per correct</p>
                    <p class="v">+1 mark</p>
                </div>
                <div class="marking-cell">
                    <p class="k">Deduction per wrong</p>
                    <p class="v">0 mark</p>
                </div>
                <div class="marking-cell">
                    <p class="k">Unanswered</p>
                    <p class="v">0 mark</p>
                </div>
                <div class="marking-cell">
                    <p class="k">Per section marks</p>
                    <p class="v"><span id="instrSectionMarks">15</span> marks</p>
                </div>
            </div>
            <div class="instruction-list">
                <div class="instruction-card">
                    <h4>Section Pattern</h4>
                    <p>Each section has <strong><span id="instrQCount">15</span> questions</strong>. All sections carry equal weight in final accuracy.</p>
                </div>
                <div class="instruction-card">
                    <h4>Answer Policy</h4>
                    <p>Select exactly one option per question. You can change your selected option before final submit.</p>
                </div>
                <div class="instruction-card">
                    <h4>Submission Rule</h4>
                    <p>Use "Review unanswered" before submit. A submitted attempt is used to generate your report and study plan.</p>
                </div>
                <div class="instruction-card">
                    <h4>Attempt Discipline</h4>
                    <p>Do not refresh or close the tab during an active test attempt to avoid losing progress.</p>
                </div>
            </div>
            <label class="check-row">
                <input type="checkbox" id="instructionAgree" />
                <span>I have read and understood the instructions.</span>
            </label>
            <div class="modal-actions">
                <button class="secondary" id="instructionCancelBtn" type="button">Cancel</button>
                <button class="primary" id="instructionBeginBtn" type="button" disabled>Begin Test</button>
            </div>
        </div>
    </div>

    <div class="modal-backdrop" id="submitConfirmModal" aria-hidden="true">
        <div class="modal" role="dialog" aria-modal="true" aria-labelledby="submitConfirmTitle">
            <h2 id="submitConfirmTitle">Submit Test?</h2>
            <p>Please confirm before submitting. After submit, your attempt will be locked and report generation will begin.</p>
            <div class="submit-confirm__stats" id="submitConfirmStats"></div>
            <div class="submit-confirm__warn" id="submitConfirmWarn"></div>
            <div class="submit-confirm__next" id="submitConfirmNext"></div>
            <div class="modal-actions">
                <button class="secondary" id="submitConfirmCloseBtn" type="button">Cancel</button>
                <button class="primary" id="submitConfirmProceedBtn" type="button">Yes, Submit</button>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js" integrity="sha384-NrKB+u6Ts6AtkIhwPixiKTzgSKNblyhlk0Sohlgar9UHUBzai/sgnNNWWd291xqt" crossorigin="anonymous"></script>
    <script>
    (function () {
        const state = {
            test: null,
            answers: {},
            chart: null,
            lastResult: null,
            isSubmitting: false,
            flatQuestions: [],
            questionOrderBySection: {},
            currentQuestionIndex: 0,
            reviewFlags: {},
            timerRef: null,
            remainingSeconds: 0,
            activeSection: null,
        };

        const els = {
            setupCard: document.getElementById('setupCard'),
            userId: document.getElementById('userId'),
            qCount: document.getElementById('qCount'),
            startBtn: document.getElementById('startBtn'),
            resetBtn: document.getElementById('resetBtn'),
            submitBtn: document.getElementById('submitBtn'),
            markReviewBtn: document.getElementById('markReviewBtn'),
            prevBtn: document.getElementById('prevBtn'),
            nextBtn: document.getElementById('nextBtn'),
            statusBar: document.getElementById('statusBar'),
            testCard: document.getElementById('testCard'),
            testArea: document.getElementById('testArea'),
            progressPill: document.getElementById('progressPill'),
            timerPill: document.getElementById('timerPill'),
            paletteArea: document.getElementById('paletteArea'),
            sectionTabs: document.getElementById('sectionTabs'),
            questionSectionLabel: document.getElementById('questionSectionLabel'),
            questionIndexLabel: document.getElementById('questionIndexLabel'),
            reportCard: document.getElementById('reportCard'),
            overallScore: document.getElementById('overallScore'),
            resultNarrative: document.getElementById('resultNarrative'),
            postSubmitSummary: document.getElementById('postSubmitSummary'),
            resultSummaryGrid: document.getElementById('resultSummaryGrid'),
            sectionHealthContent: document.getElementById('sectionHealthContent'),
            focusTopicsContent: document.getElementById('focusTopicsContent'),
            sectionGrid: document.getElementById('sectionGrid'),
            answerReviewContent: document.getElementById('answerReviewContent'),
            planCard: document.getElementById('planCard'),
            planContent: document.getElementById('planContent'),
            historyBlock: document.getElementById('historyBlock'),
            chartCanvas: document.getElementById('progressChart'),
            jsonCard: document.getElementById('jsonCard'),
            jsonContent: document.getElementById('jsonContent'),
            downloadJsonBtn: document.getElementById('downloadJsonBtn'),
            downloadAttemptBtn: document.getElementById('downloadAttemptBtn'),
            instructionModal: document.getElementById('instructionModal'),
            instructionAgree: document.getElementById('instructionAgree'),
            instructionCancelBtn: document.getElementById('instructionCancelBtn'),
            instructionBeginBtn: document.getElementById('instructionBeginBtn'),
            submitConfirmModal: document.getElementById('submitConfirmModal'),
            submitConfirmStats: document.getElementById('submitConfirmStats'),
            submitConfirmWarn: document.getElementById('submitConfirmWarn'),
            submitConfirmNext: document.getElementById('submitConfirmNext'),
            submitConfirmCloseBtn: document.getElementById('submitConfirmCloseBtn'),
            submitConfirmProceedBtn: document.getElementById('submitConfirmProceedBtn'),
        };

        function setStatus(message, tone = '') {
            els.statusBar.textContent = message;
            els.statusBar.className = tone ? tone : '';
        }

        function pickIdentifier(user) {
            if (!user || typeof user !== 'object') {
                return '';
            }
            return user.email || user.phone_number || user.id || '';
        }

        function prefillFromLocalProfile() {
            try {
                const raw = localStorage.getItem('cb_user');
                if (!raw) {
                    return '';
                }
                const user = JSON.parse(raw);
                const identifier = pickIdentifier(user);
                if (identifier) {
                    els.userId.value = identifier;
                    return identifier;
                }
            } catch (err) {
                console.warn('Could not read local profile for planner prefill', err);
            }
            return '';
        }

        function updateInstructionMetrics() {
            const qCount = parseInt(els.qCount.value, 10) || 15;
            const qCountNode = document.getElementById('instrQCount');
            const sectionMarksNode = document.getElementById('instrSectionMarks');
            if (qCountNode) {
                qCountNode.textContent = String(qCount);
            }
            if (sectionMarksNode) {
                sectionMarksNode.textContent = String(qCount);
            }
        }

        async function hydrateIdentifierFromSession() {
            try {
                const token = localStorage.getItem('cb_token');
                if (!token) {
                    return '';
                }
                const res = await fetch('/auth/session', {
                    headers: { Authorization: 'Bearer ' + token },
                });
                if (!res.ok) {
                    return '';
                }
                const data = await res.json();
                const identifier = pickIdentifier(data.user || {});
                if (identifier) {
                    els.userId.value = identifier;
                    try {
                        localStorage.setItem('cb_user', JSON.stringify(data.user || {}));
                    } catch (storageErr) {
                        console.warn('Could not persist refreshed profile', storageErr);
                    }
                    return identifier;
                }
            } catch (err) {
                console.warn('Session profile fetch failed for planner prefill', err);
            }
            return '';
        }

        function calcCompletion() {
            if (!state.flatQuestions.length) {
                return 0;
            }
            const total = state.flatQuestions.length;
            const answered = Object.keys(state.answers).length;
            return Math.round((answered / total) * 100) || 0;
        }

        function updateProgress() {
            const pct = calcCompletion();
            els.progressPill.textContent = pct + '% completed';
        }

        function clearUI() {
            document.body.classList.remove('exam-mode');
            closeSubmitConfirmModal();
            state.test = null;
            state.answers = {};
            state.flatQuestions = [];
            state.questionOrderBySection = {};
            state.currentQuestionIndex = 0;
            state.reviewFlags = {};
            state.remainingSeconds = 0;
            state.activeSection = null;
            state.lastResult = null;
            state.isSubmitting = false;
            if (els.setupCard) {
                els.setupCard.classList.remove('hidden');
            }
            if (state.timerRef) {
                clearInterval(state.timerRef);
                state.timerRef = null;
            }
            els.testArea.innerHTML = '';
            els.paletteArea.innerHTML = '';
            els.sectionTabs.innerHTML = '';
            els.timerPill.textContent = 'Time left: 00:00:00';
            els.reportCard.classList.add('hidden');
            els.planCard.classList.add('hidden');
            els.historyBlock.innerHTML = '';
            els.overallScore.textContent = '';
            if (els.resultNarrative) {
                els.resultNarrative.textContent = '';
            }
            if (els.postSubmitSummary) {
                els.postSubmitSummary.innerHTML = '';
            }
            if (els.resultSummaryGrid) {
                els.resultSummaryGrid.innerHTML = '';
            }
            if (els.sectionHealthContent) {
                els.sectionHealthContent.innerHTML = '';
            }
            if (els.focusTopicsContent) {
                els.focusTopicsContent.innerHTML = '';
            }
            if (els.answerReviewContent) {
                els.answerReviewContent.innerHTML = '';
            }
            els.jsonCard.classList.add('hidden');
            els.jsonContent.textContent = '';
            els.testCard.style.display = 'none';
            if (els.submitBtn) {
                els.submitBtn.disabled = false;
                els.submitBtn.textContent = 'Submit Test';
            }
            if (state.chart) {
                state.chart.destroy();
                state.chart = null;
            }
        }

        function formatDuration(totalSeconds) {
            const safe = Math.max(0, totalSeconds || 0);
            const h = Math.floor(safe / 3600).toString().padStart(2, '0');
            const m = Math.floor((safe % 3600) / 60).toString().padStart(2, '0');
            const s = Math.floor(safe % 60).toString().padStart(2, '0');
            return h + ':' + m + ':' + s;
        }

        function refreshTimer() {
            els.timerPill.textContent = 'Time left: ' + formatDuration(state.remainingSeconds);
        }

        function stopTimer() {
            if (state.timerRef) {
                clearInterval(state.timerRef);
                state.timerRef = null;
            }
        }

        function startTimer() {
            stopTimer();
            const totalQuestions = state.flatQuestions.length || 1;
            state.remainingSeconds = Math.max(20 * 60, totalQuestions * 75);
            refreshTimer();
            state.timerRef = setInterval(async () => {
                state.remainingSeconds -= 1;
                refreshTimer();
                if (state.remainingSeconds <= 0) {
                    stopTimer();
                    setStatus('Time up. Submitting your test...');
                    await submitTest(true);
                }
            }, 1000);
        }

        function flattenQuestions() {
            state.flatQuestions = [];
            state.questionOrderBySection = {};

            Object.entries(state.test.sections || {}).forEach(([sectionKey, section]) => {
                const label = section.label || sectionKey;
                state.questionOrderBySection[label] = [];
                (section.questions || []).forEach((question) => {
                    const idx = state.flatQuestions.push({
                        ...question,
                        sectionKey,
                        sectionLabel: label,
                    }) - 1;
                    state.questionOrderBySection[label].push(idx);
                });
            });
            const firstSection = Object.keys(state.questionOrderBySection)[0];
            state.activeSection = firstSection || null;
        }

        function renderSectionTabs() {
            els.sectionTabs.innerHTML = '';
            Object.entries(state.questionOrderBySection).forEach(([label, indexes]) => {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'section-tab' + (state.activeSection === label ? ' active' : '');
                const shortLabel = label.replace('Science & Tech', 'Sci & Tech');
                btn.textContent = shortLabel + ' (' + indexes.length + ')';
                btn.addEventListener('click', () => {
                    state.activeSection = label;
                    if (indexes.length) {
                        state.currentQuestionIndex = indexes[0];
                    }
                    renderFocusedQuestion();
                });
                els.sectionTabs.appendChild(btn);
            });
        }

        function getPaletteIndexes() {
            if (state.activeSection && state.questionOrderBySection[state.activeSection]) {
                return state.questionOrderBySection[state.activeSection];
            }
            return state.flatQuestions.map((_, idx) => idx);
        }

        function questionStatus(index) {
            const question = state.flatQuestions[index];
            if (!question) {
                return '';
            }
            if (index === state.currentQuestionIndex) {
                return 'current';
            }
            if (state.reviewFlags[question.question_id]) {
                return 'review';
            }
            if (state.answers[question.question_id]) {
                return 'answered';
            }
            return '';
        }

        function renderPalette() {
            els.paletteArea.innerHTML = '';
            renderSectionTabs();

            const indexes = getPaletteIndexes();
            const wrap = document.createElement('div');
            wrap.className = 'palette-section';

            const title = document.createElement('p');
            title.className = 'palette-title';
            title.textContent = (state.activeSection || 'Questions').toUpperCase();
            wrap.appendChild(title);

            const grid = document.createElement('div');
            grid.className = 'palette-grid';

            indexes.forEach((idx) => {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'palette-btn ' + questionStatus(idx);
                btn.textContent = String(idx + 1);
                btn.addEventListener('click', () => {
                    state.currentQuestionIndex = idx;
                    renderFocusedQuestion();
                });
                grid.appendChild(btn);
            });

            wrap.appendChild(grid);
            els.paletteArea.appendChild(wrap);
        }

        function renderFocusedQuestion() {
            if (!state.flatQuestions.length) {
                return;
            }

            const question = state.flatQuestions[state.currentQuestionIndex];
            if (!question) {
                return;
            }

            els.questionSectionLabel.textContent = question.sectionLabel;
            if (state.activeSection !== question.sectionLabel) {
                state.activeSection = question.sectionLabel;
            }
            els.questionIndexLabel.textContent = 'Question ' + (state.currentQuestionIndex + 1) + ' of ' + state.flatQuestions.length;

            const wrapper = document.createElement('article');
            wrapper.className = 'question';
            wrapper.dataset.questionId = question.question_id;

            const title = document.createElement('h4');
            title.textContent = (state.currentQuestionIndex + 1) + '. ' + question.question;
            wrapper.appendChild(title);

            const meta = document.createElement('div');
            meta.className = 'meta';
            meta.innerHTML = '<span>Topic: ' + (question.topic || 'NA') + '</span><span>Difficulty: ' + (question.difficulty || 'NA') + '</span>';
            wrapper.appendChild(meta);

            const opts = document.createElement('div');
            opts.className = 'options';

            ['A', 'B', 'C', 'D'].forEach((key) => {
                if (!question.options || !question.options[key]) {
                    return;
                }
                const option = document.createElement('label');
                option.className = 'option';

                const input = document.createElement('input');
                input.type = 'radio';
                input.name = question.question_id;
                input.value = key;
                input.checked = state.answers[question.question_id] === key;
                input.addEventListener('change', () => {
                    state.answers[question.question_id] = key;
                    updateProgress();
                    renderPalette();
                });

                const span = document.createElement('span');
                span.textContent = key + '. ' + question.options[key];

                option.appendChild(input);
                option.appendChild(span);
                opts.appendChild(option);
            });

            wrapper.appendChild(opts);
            els.testArea.innerHTML = '';
            els.testArea.appendChild(wrapper);

            const marked = !!state.reviewFlags[question.question_id];
            els.markReviewBtn.textContent = marked ? 'Unmark review' : 'Mark for review';
            els.prevBtn.disabled = state.currentQuestionIndex === 0;
            els.nextBtn.disabled = state.currentQuestionIndex === state.flatQuestions.length - 1;

            updateProgress();
            renderPalette();
        }

        function enterExamMode() {
            document.body.classList.add('exam-mode');
            els.testCard.style.display = 'block';
        }

        function exitExamMode() {
            document.body.classList.remove('exam-mode');
            stopTimer();
        }

        function openInstructionsModal() {
            return new Promise((resolve) => {
                const modal = els.instructionModal;
                const agree = els.instructionAgree;
                const beginBtn = els.instructionBeginBtn;
                const cancelBtn = els.instructionCancelBtn;
                updateInstructionMetrics();

                function cleanup() {
                    agree.checked = false;
                    beginBtn.disabled = true;
                    modal.classList.remove('show');
                    modal.setAttribute('aria-hidden', 'true');
                    document.body.classList.remove('modal-open');
                    agree.removeEventListener('change', onAgreeToggle);
                    beginBtn.removeEventListener('click', onBegin);
                    cancelBtn.removeEventListener('click', onCancel);
                    modal.removeEventListener('click', onBackdropClick);
                    document.removeEventListener('keydown', onEscClose);
                }

                function close(result) {
                    cleanup();
                    resolve(result);
                }

                function onAgreeToggle() {
                    beginBtn.disabled = !agree.checked;
                }

                function onBegin() {
                    if (!agree.checked) {
                        return;
                    }
                    close(true);
                }

                function onCancel() {
                    close(false);
                }

                function onBackdropClick(event) {
                    if (event.target === modal) {
                        close(false);
                    }
                }

                function onEscClose(event) {
                    if (event.key === 'Escape') {
                        close(false);
                    }
                }

                agree.addEventListener('change', onAgreeToggle);
                beginBtn.addEventListener('click', onBegin);
                cancelBtn.addEventListener('click', onCancel);
                modal.addEventListener('click', onBackdropClick);
                document.addEventListener('keydown', onEscClose);

                modal.classList.add('show');
                modal.setAttribute('aria-hidden', 'false');
                document.body.classList.add('modal-open');
                agree.focus();
            });
        }

        async function startTest() {
            const confirmed = await openInstructionsModal();
            if (!confirmed) {
                setStatus('Please read the instructions before starting the test.');
                return;
            }

            clearUI();
            setStatus('Loading questions...');
            const qCount = parseInt(els.qCount.value, 10) || 15;
            try {
                const res = await fetch('/agents/planner/test?questions_per_section=' + qCount);
                if (!res.ok) {
                    throw new Error('Unable to generate test');
                }
                const data = await res.json();
                state.test = data.test;
                flattenQuestions();
                state.currentQuestionIndex = 0;
                enterExamMode();
                renderFocusedQuestion();
                startTimer();
                setStatus('Test ready. Best of luck!', 'success');
            } catch (err) {
                console.error(err);
                setStatus(err.message || 'Failed to load test', 'error');
                els.testCard.style.display = 'none';
            }
        }

        function reviewUnanswered() {
            if (!state.test) {
                return;
            }
            const idx = state.flatQuestions.findIndex((question) => !state.answers[question.question_id]);
            if (idx >= 0) {
                state.currentQuestionIndex = idx;
                renderFocusedQuestion();
            }
        }

        function renderHistory(history) {
            if (!history.available) {
                els.historyBlock.innerHTML = '<p style="margin:0; color: var(--muted);">No prior attempts found for this user.</p>';
                return;
            }

            const fragment = document.createDocumentFragment();
            const title = document.createElement('h3');
            title.style.margin = '0 0 12px';
            title.textContent = 'Recent attempts';
            fragment.appendChild(title);

            history.entries.forEach((entry) => {
                const row = document.createElement('div');
                row.className = 'history-item';

                const date = document.createElement('span');
                const formatted = new Date(entry.date).toLocaleString();
                date.textContent = formatted;

                const scores = document.createElement('span');
                const parts = Object.keys(entry.sections || {}).map((key) => key + ': ' + entry.sections[key] + '%');
                scores.textContent = parts.join(' | ');

                row.appendChild(date);
                row.appendChild(scores);
                fragment.appendChild(row);
            });

            els.historyBlock.innerHTML = '';
            els.historyBlock.appendChild(fragment);
        }

        function renderSections(sectionReport) {
            els.sectionGrid.innerHTML = '';
            Object.values(sectionReport).forEach((section) => {
                const accuracy = Number(section.accuracy || 0);
                const total = Number(section.total || 0);
                const correct = Number(section.correct || 0);
                const wrong = Math.max(0, total - correct);
                const tag = accuracy >= 75 ? 'strong' : (accuracy >= 60 ? 'average' : 'weak');
                const tagLabel = accuracy >= 75 ? 'Strong' : (accuracy >= 60 ? 'Average' : 'Weak');
                const block = document.createElement('div');
                block.className = 'result-card';
                block.innerHTML = `
                    <h4>${section.label}</h4>
                    <div class="result-row">
                        <span>Accuracy ${accuracy}%</span>
                        <span class="result-badge ${tag}">${tagLabel}</span>
                    </div>
                    <div class="result-progress"><span style="width:${Math.max(0, Math.min(100, accuracy))}%"></span></div>
                    <div class="result-row" style="margin-top:8px; margin-bottom:0;">
                        <span>Correct ${correct} / ${total}</span>
                        <span>Wrong ${wrong}</span>
                    </div>
                `;

                if (section.incorrect_questions && section.incorrect_questions.length) {
                    const review = document.createElement('details');
                    const summary = document.createElement('summary');
                    summary.textContent = 'Review incorrect questions (' + section.incorrect_questions.length + ')';
                    review.appendChild(summary);

                    section.incorrect_questions.forEach((item) => {
                        const para = document.createElement('p');
                        para.style.margin = '6px 0';
                        para.style.fontSize = '13px';
                        para.textContent = item.question;
                        review.appendChild(para);
                    });
                    block.appendChild(review);
                }
                if (!total) {
                    const none = document.createElement('p');
                    none.style.margin = '8px 0 0';
                    none.style.color = 'var(--muted)';
                    none.style.fontSize = '13px';
                    none.textContent = 'No questions attempted in this section.';
                    block.appendChild(none);
                }

                els.sectionGrid.appendChild(block);
            });
        }

        function renderResultSummary(summary, sectionReport) {
            if (!els.resultSummaryGrid) {
                return;
            }
            const overall = Number(summary.overall_accuracy || 0);
            const totalQuestions = Number(summary.total_questions || 0);
            const totalCorrect = Number(summary.total_correct || 0);
            const totalWrong = Math.max(0, totalQuestions - totalCorrect);
            const topperBenchmark = 95;
            const topperGap = Math.max(0, (topperBenchmark - overall)).toFixed(2);

            const sections = Object.values(sectionReport || {});
            let strongest = 'NA';
            let weakest = 'NA';
            if (sections.length) {
                const sorted = sections
                    .filter((section) => section && section.accuracy !== undefined && section.accuracy !== null)
                    .sort((a, b) => Number(b.accuracy || 0) - Number(a.accuracy || 0));
                if (sorted.length) {
                    strongest = `${sorted[0].label} (${sorted[0].accuracy}%)`;
                    weakest = `${sorted[sorted.length - 1].label} (${sorted[sorted.length - 1].accuracy}%)`;
                }
            }

            const tiles = [
                { key: 'Overall Score', value: `${overall}%` },
                { key: 'Topper Gap', value: `${topperGap}%` },
                { key: 'Right / Wrong', value: `${totalCorrect} / ${totalWrong}` },
                { key: 'Strongest Section', value: strongest },
                { key: 'Weakest Section', value: weakest },
            ];

            els.resultSummaryGrid.innerHTML = '';
            tiles.forEach((tile) => {
                const div = document.createElement('div');
                div.className = 'insight-tile';
                div.innerHTML = `<p class="k">${tile.key}</p><p class="v">${tile.value}</p>`;
                els.resultSummaryGrid.appendChild(div);
            });
        }

        function renderFocusTopics(sectionReport) {
            if (!els.focusTopicsContent) {
                return;
            }
            const sections = Object.values(sectionReport || {})
                .filter((section) => section && section.accuracy !== undefined && section.accuracy !== null)
                .sort((a, b) => Number(a.accuracy || 0) - Number(b.accuracy || 0));

            els.focusTopicsContent.innerHTML = '';
            if (!sections.length) {
                els.focusTopicsContent.innerHTML = '<p style="margin:0; color: var(--muted);">Focus topics will appear after submission.</p>';
                return;
            }

            sections.slice(0, 3).forEach((section, index) => {
                const row = document.createElement('div');
                row.style.border = '1px solid var(--border)';
                row.style.borderRadius = '10px';
                row.style.padding = '10px 12px';
                row.style.background = '#fff';
                row.innerHTML = `<strong>${index + 1}. ${section.label}</strong> - Accuracy ${section.accuracy}%`;
                els.focusTopicsContent.appendChild(row);
            });
        }

        function renderSectionHealth(sectionReport) {
            if (!els.sectionHealthContent) {
                return;
            }
            const sections = Object.values(sectionReport || {})
                .filter((section) => section && section.accuracy !== undefined && section.accuracy !== null)
                .sort((a, b) => Number(a.accuracy || 0) - Number(b.accuracy || 0));

            els.sectionHealthContent.innerHTML = '';
            if (!sections.length) {
                els.sectionHealthContent.innerHTML = '<p style="margin:0; color: var(--muted);">Section strength analysis will appear after submission.</p>';
                return;
            }

            sections.forEach((section) => {
                const score = Number(section.accuracy || 0);
                let tag = 'Average';
                let tagClass = 'average';
                let color = '#b45309';
                let guidance = 'Build consistency with daily MCQs and revision.';
                if (score >= 75) {
                    tag = 'Strong';
                    tagClass = 'strong';
                    color = '#166534';
                    guidance = 'Maintain this advantage. Use these topics for high-confidence scoring.';
                } else if (score < 50) {
                    tag = 'Weak';
                    tagClass = 'weak';
                    color = '#b91c1c';
                    guidance = 'High-priority repair zone. Revise fundamentals and solve targeted PYQs.';
                }

                const card = document.createElement('div');
                card.className = 'result-card';
                card.innerHTML = `
                    <div class="result-row" style="margin-bottom:6px;">
                        <strong>${section.label}</strong>
                        <span class="result-badge ${tagClass}" style="color:${color};">${tag}</span>
                    </div>
                    <div class="result-row" style="margin-bottom:8px;">
                        <span>Accuracy ${score}%</span>
                    </div>
                    <div class="result-progress"><span style="width:${Math.max(0, Math.min(100, score))}%"></span></div>
                    <p style="margin:8px 0 0; color:var(--muted); font-size:13px;">${guidance}</p>
                `;
                els.sectionHealthContent.appendChild(card);
            });
        }

        function renderAnswerReview(sectionReport) {
            if (!els.answerReviewContent) {
                return;
            }
            const sections = Object.values(sectionReport || {});
            const reviewRows = [];
            sections.forEach((section) => {
                const incorrect = Array.isArray(section.incorrect_questions) ? section.incorrect_questions : [];
                const total = Number(section.total || 0);
                const correct = Number(section.correct || 0);
                const wrong = Math.max(0, total - correct);
                reviewRows.push({
                    label: section.label || 'Section',
                    correct,
                    wrong,
                    incorrect,
                });
            });

            els.answerReviewContent.innerHTML = '';
            if (!reviewRows.length) {
                els.answerReviewContent.innerHTML = '<p style="margin:0; color: var(--muted);">No review data available.</p>';
                return;
            }

            reviewRows.forEach((row) => {
                const card = document.createElement('div');
                card.style.border = '1px solid var(--border)';
                card.style.borderRadius = '10px';
                card.style.padding = '10px 12px';
                card.style.background = '#fff';

                const title = document.createElement('p');
                title.style.margin = '0 0 6px';
                title.innerHTML = `<strong>${row.label}</strong> - Right ${row.correct}, Wrong ${row.wrong}`;
                card.appendChild(title);

                if (!row.incorrect.length) {
                    const ok = document.createElement('p');
                    ok.style.margin = '0';
                    ok.style.color = 'var(--muted)';
                    ok.textContent = 'No incorrect questions in this section.';
                    card.appendChild(ok);
                } else {
                    const details = document.createElement('details');
                    const summary = document.createElement('summary');
                    summary.textContent = `Review wrong questions (${row.incorrect.length})`;
                    details.appendChild(summary);
                    row.incorrect.slice(0, 10).forEach((item) => {
                        const p = document.createElement('p');
                        p.style.margin = '6px 0 0';
                        p.style.fontSize = '13px';
                        p.textContent = `${item.question} | Selected: ${item.selected_answer || '-'} | Correct: ${item.correct_answer || '-'}`;
                        details.appendChild(p);
                    });
                    card.appendChild(details);
                }

                els.answerReviewContent.appendChild(card);
            });
        }

        function renderChart(sectionReport) {
            const labels = [];
            const scores = [];
            Object.values(sectionReport).forEach((section) => {
                labels.push(section.label);
                scores.push(Number(section.accuracy || 0));
            });
            const topperScores = labels.map(() => 95);

            if (state.chart) {
                state.chart.destroy();
            }

            state.chart = new Chart(els.chartCanvas, {
                type: 'bar',
                data: {
                    labels,
                    datasets: [
                        {
                            label: 'Your Score %',
                            data: scores,
                            borderRadius: 6,
                            backgroundColor: 'rgba(31, 123, 94, 0.82)',
                            borderColor: 'rgba(20, 90, 70, 1)',
                            borderWidth: 1.2,
                            barPercentage: 0.62,
                            categoryPercentage: 0.72,
                        },
                        {
                            label: 'Topper Benchmark %',
                            data: topperScores,
                            borderRadius: 6,
                            backgroundColor: 'rgba(220, 38, 38, 0.22)',
                            borderColor: 'rgba(220, 38, 38, 0.95)',
                            borderWidth: 1.2,
                            barPercentage: 0.62,
                            categoryPercentage: 0.72,
                        },
                    ],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            grid: { display: false },
                            ticks: {
                                color: '#4a625b',
                                font: { size: 11, weight: 600 },
                                maxRotation: 20,
                                minRotation: 0,
                                autoSkip: false,
                            },
                        },
                        y: {
                            beginAtZero: true,
                            max: 100,
                            ticks: {
                                stepSize: 10,
                                color: '#4a625b',
                                font: { size: 11 },
                            },
                            grid: {
                                color: 'rgba(22, 52, 46, 0.08)',
                            },
                        },
                    },
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top',
                            align: 'end',
                            labels: {
                                boxWidth: 14,
                                boxHeight: 14,
                                color: '#27443d',
                                font: { size: 12, weight: 600 },
                            },
                        },
                        tooltip: {
                            callbacks: {
                                label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y}%`,
                            },
                        },
                    },
                },
            });
        }

        function _escapeHtml(text) {
            return String(text || '')
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#39;');
        }

        function downloadAttemptPaper() {
            if (!state.flatQuestions.length) {
                setStatus('No attempt data available to download.', 'error');
                return;
            }
            const result = state.lastResult || {};
            const sectionReport = result.section_report || {};
            const wrongMap = {};
            Object.values(sectionReport).forEach((section) => {
                (section.incorrect_questions || []).forEach((item) => {
                    wrongMap[item.question_id] = item;
                });
            });

            const rows = state.flatQuestions.map((q, idx) => {
                const selected = state.answers[q.question_id] || '-';
                const wrong = wrongMap[q.question_id];
                const status = selected === '-' ? 'Unanswered' : (wrong ? 'Wrong' : 'Correct');
                const correct = wrong ? (wrong.correct_answer || '-') : (status === 'Correct' ? selected : '-');
                const options = Object.entries(q.options || {}).map(([k, v]) => `${k}. ${v}`).join('<br/>');
                return `
                    <tr>
                        <td>${idx + 1}</td>
                        <td>${_escapeHtml(q.sectionLabel || q.section || '')}</td>
                        <td>${_escapeHtml(q.question || '')}<div style="margin-top:6px;color:#536b64;font-size:12px;">${options}</div></td>
                        <td>${_escapeHtml(selected)}</td>
                        <td>${_escapeHtml(correct)}</td>
                        <td>${_escapeHtml(status)}</td>
                    </tr>
                `;
            }).join('');

            const overall = result.test_summary?.overall_accuracy ?? '-';
            const generatedAt = new Date().toLocaleString();
            const html = `<!doctype html>
<html><head><meta charset="utf-8"><title>CivicBriefs Test Paper</title>
<style>
body{font-family:Segoe UI,Arial,sans-serif;margin:24px;color:#143831}
h1{margin:0 0 8px} .meta{margin:0 0 16px;color:#4d645e}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{border:1px solid #c8d7d1;padding:8px;vertical-align:top}
th{background:#ecf4f1;text-align:left}
.ok{color:#166534}.bad{color:#b91c1c}
</style></head><body>
<h1>CivicBriefs Mock Test - Attempt Paper</h1>
<p class="meta">Generated: ${_escapeHtml(generatedAt)} | Overall Accuracy: ${_escapeHtml(overall)}%</p>
<table>
<thead><tr><th>#</th><th>Section</th><th>Question</th><th>Your Answer</th><th>Correct Answer</th><th>Status</th></tr></thead>
<tbody>${rows}</tbody>
</table>
</body></html>`;

            const blob = new Blob([html], { type: 'text/html' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'civicbriefs-test-paper.html';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }

        function renderResultNarrative(summary) {
            if (!els.resultNarrative) {
                return;
            }
            const overall = Number(summary.overall_accuracy || 0);
            if (overall >= 85) {
                els.resultNarrative.textContent = 'Excellent attempt. You are in a high-scoring zone. Protect strong sections and close residual weak spots to push closer to topper range.';
                return;
            }
            if (overall >= 65) {
                els.resultNarrative.textContent = 'Good base score. With focused work on weak sections and consistent revision, you can achieve significantly higher marks in upcoming tests.';
                return;
            }
            els.resultNarrative.textContent = 'Foundation phase detected. Prioritize weak sections first, revise core concepts daily, and practice timed MCQs to improve your score quickly.';
        }

        function renderPostSubmitSummary(summary, sectionReport) {
            if (!els.postSubmitSummary) {
                return;
            }
            const overall = Number(summary.overall_accuracy || 0);
            const totalQuestions = Number(summary.total_questions || 0);
            const totalCorrect = Number(summary.total_correct || 0);
            const wrong = Math.max(0, totalQuestions - totalCorrect);
            const sections = Object.values(sectionReport || {})
                .filter((s) => s && s.accuracy !== undefined && s.accuracy !== null)
                .sort((a, b) => Number(a.accuracy || 0) - Number(b.accuracy || 0));

            const weak = sections.slice(0, 2).map((s) => s.label);
            const strong = sections.slice(-2).reverse().map((s) => s.label);
            const nextTarget = Math.min(95, Math.ceil((overall + 8) / 5) * 5);

            const bullets = [
                `Score snapshot: ${overall}% accuracy (${totalCorrect} correct, ${wrong} wrong).`,
                weak.length ? `Primary improvement zone: ${weak.join(', ')}.` : 'Primary improvement zone will appear once section data is available.',
                strong.length ? `Strength to retain: ${strong.join(', ')}.` : 'Strength indicators will appear after section coverage improves.',
                `Next mock target: ${nextTarget}% with timed practice and one revision cycle before reattempt.`,
            ];

            els.postSubmitSummary.innerHTML = '<h4>What to improve next</h4><ul>' + bullets.map((item) => `<li>${item}</li>`).join('') + '</ul>';
        }

        function renderPlan(plan, weeklySchedule) {
            els.planContent.innerHTML = '';

            const classification = document.createElement('div');
            classification.style.border = '1px solid var(--border)';
            classification.style.borderRadius = '12px';
            classification.style.padding = '16px';
            classification.innerHTML = '<h3 style="margin:0 0 8px; font-size:18px;">Classification</h3>';
            const list = document.createElement('ul');
            list.style.paddingLeft = '18px';
            Object.entries(plan.classification || {}).forEach(([subject, tag]) => {
                const li = document.createElement('li');
                li.textContent = subject + ': ' + tag;
                list.appendChild(li);
            });
            classification.appendChild(list);
            els.planContent.appendChild(classification);

            const sevenDay = document.createElement('div');
            sevenDay.style.border = '1px solid var(--border)';
            sevenDay.style.borderRadius = '12px';
            sevenDay.style.padding = '16px';
            sevenDay.innerHTML = '<h3 style="margin:0 0 8px; font-size:18px;">7 Day Focus</h3>';
            const sevenList = document.createElement('ul');
            sevenList.style.paddingLeft = '18px';
            (plan['7_day_plan'] || []).forEach((item) => {
                const li = document.createElement('li');
                li.textContent = item.day + ': ' + item.plan;
                sevenList.appendChild(li);
            });
            sevenDay.appendChild(sevenList);
            els.planContent.appendChild(sevenDay);

            const month = document.createElement('div');
            month.style.border = '1px solid var(--border)';
            month.style.borderRadius = '12px';
            month.style.padding = '16px';
            month.innerHTML = '<h3 style="margin:0 0 8px; font-size:18px;">30 Day Roadmap</h3>';
            const monthList = document.createElement('ul');
            monthList.style.paddingLeft = '18px';
            Object.entries(plan['30_day_plan'] || {}).forEach(([week, planText]) => {
                const li = document.createElement('li');
                li.textContent = week + ': ' + planText;
                monthList.appendChild(li);
            });
            month.appendChild(monthList);
            els.planContent.appendChild(month);

            const summary = document.createElement('div');
            summary.style.border = '1px solid var(--border)';
            summary.style.borderRadius = '12px';
            summary.style.padding = '16px';
            summary.innerHTML = '<h3 style="margin:0 0 8px; font-size:18px;">Daily Routine & PYQ Strategy</h3>' +
                '<p style="margin:0 0 6px;">Daily Plan: MCQs ' + (plan.daily_plan ? plan.daily_plan.mcq_per_day : '-') + ', revision ' + (plan.daily_plan ? plan.daily_plan.revision_minutes : '-') + ' minutes.</p>' +
                '<p style="margin:0;">Strategy: ' + (plan.pyq_strategy || 'Focus on latest PYQs') + '</p>';
            els.planContent.appendChild(summary);

            if (weeklySchedule && (weeklySchedule.schedule_text || weeklySchedule.summary)) {
                const schedule = document.createElement('div');
                schedule.style.border = '1px solid var(--border)';
                schedule.style.borderRadius = '12px';
                schedule.style.padding = '16px';

                const title = document.createElement('h3');
                title.style.margin = '0 0 8px';
                title.style.fontSize = '18px';
                title.textContent = 'LLM Weekly Schedule';
                schedule.appendChild(title);

                if (weeklySchedule.summary) {
                    const summaryLine = document.createElement('p');
                    summaryLine.style.margin = '0 0 10px';
                    summaryLine.style.color = 'var(--muted)';
                    summaryLine.textContent = weeklySchedule.summary;
                    schedule.appendChild(summaryLine);
                }

                const scheduleBody = document.createElement('div');
                scheduleBody.style.whiteSpace = 'pre-line';
                scheduleBody.style.fontFamily = "'SFMono-Regular', 'Consolas', 'Liberation Mono', monospace";
                scheduleBody.style.fontSize = '14px';
                scheduleBody.style.lineHeight = '1.45';
                scheduleBody.textContent = weeklySchedule.schedule_text || 'Schedule not available.';
                schedule.appendChild(scheduleBody);

                if (weeklySchedule.allocations) {
                    const allocTitle = document.createElement('p');
                    allocTitle.style.margin = '12px 0 4px';
                    allocTitle.style.fontWeight = '600';
                    allocTitle.textContent = 'Weekly hour allocations:';
                    schedule.appendChild(allocTitle);

                    const allocList = document.createElement('ul');
                    allocList.style.margin = '0';
                    allocList.style.paddingLeft = '18px';
                    Object.entries(weeklySchedule.allocations).forEach(([subject, hours]) => {
                        const li = document.createElement('li');
                        li.textContent = subject + ': ' + hours + ' hrs';
                        allocList.appendChild(li);
                    });
                    schedule.appendChild(allocList);
                }

                els.planContent.appendChild(schedule);
            }
        }

        function handleReport(data) {
            exitExamMode();
            state.lastResult = data || null;
            els.testCard.style.display = 'none';
            if (els.setupCard) {
                els.setupCard.classList.add('hidden');
            }
            els.reportCard.classList.remove('hidden');
            els.planCard.classList.remove('hidden');

            els.overallScore.textContent = 'Overall accuracy ' + data.test_summary.overall_accuracy + '%';
            renderResultNarrative(data.test_summary || {});
            renderPostSubmitSummary(data.test_summary || {}, data.section_report || {});
            renderResultSummary(data.test_summary || {}, data.section_report || {});
            renderSectionHealth(data.section_report || {});
            renderFocusTopics(data.section_report || {});
            renderSections(data.section_report);
            renderAnswerReview(data.section_report || {});
            renderChart(data.section_report);
            renderHistory(data.history);
            renderPlan(data.study_plan, data.weekly_schedule);
            renderJson(data);
            els.reportCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }

        function renderJson(data) {
            if (!data) {
                els.jsonCard.classList.add('hidden');
                return;
            }

            const serialized = JSON.stringify(data, null, 2);
            els.jsonContent.textContent = serialized;
            els.jsonCard.classList.remove('hidden');

            if (els.downloadJsonBtn) {
                els.downloadJsonBtn.onclick = () => {
                    const blob = new Blob([serialized], { type: 'application/json' });
                    const url = URL.createObjectURL(blob);
                    const anchor = document.createElement('a');
                    anchor.href = url;
                    anchor.download = 'planner-test-report.json';
                    document.body.appendChild(anchor);
                    anchor.click();
                    document.body.removeChild(anchor);
                    URL.revokeObjectURL(url);
                };
            }
        }

        function closeSubmitConfirmModal() {
            if (!els.submitConfirmModal) {
                return;
            }
            els.submitConfirmModal.classList.remove('show');
            els.submitConfirmModal.setAttribute('aria-hidden', 'true');
            document.body.classList.remove('modal-open');
        }

        function openSubmitConfirmModal() {
            if (!els.submitConfirmModal || !state.test) {
                return;
            }
            const totalQuestions = state.flatQuestions.length;
            const answered = Object.keys(state.answers).length;
            const unanswered = Math.max(0, totalQuestions - answered);
            const completion = totalQuestions ? Math.round((answered / totalQuestions) * 100) : 0;

            if (els.submitConfirmStats) {
                els.submitConfirmStats.innerHTML = `
                    <div class="cell"><p class="k">Total</p><p class="v">${totalQuestions}</p></div>
                    <div class="cell"><p class="k">Answered</p><p class="v">${answered}</p></div>
                    <div class="cell"><p class="k">Unanswered</p><p class="v">${unanswered}</p></div>
                `;
            }
            if (els.submitConfirmWarn) {
                if (answered === 0) {
                    els.submitConfirmWarn.textContent = 'No questions answered yet. You can still submit now to generate your baseline score and improvement plan.';
                } else if (unanswered > 0) {
                    els.submitConfirmWarn.textContent = `You still have ${unanswered} unanswered question(s). You can still submit now or go back and complete them.`;
                } else {
                    els.submitConfirmWarn.textContent = 'All questions are attempted. Click "Yes, Submit" to generate your detailed performance report.';
                }
            }
            if (els.submitConfirmNext) {
                els.submitConfirmNext.innerHTML = `
                    <strong>After submission, you will instantly get:</strong>
                    <ul>
                        <li>Your overall score and section-wise accuracy report</li>
                        <li>Weak vs strong section diagnosis with wrong-question review</li>
                        <li>Priority focus topics and a practical improvement plan</li>
                        <li>Current attempt completion: ${completion}% (max possible score from attempted set)</li>
                    </ul>
                `;
            }
            if (els.submitConfirmProceedBtn) {
                els.submitConfirmProceedBtn.disabled = false;
            }
            els.submitConfirmModal.classList.add('show');
            els.submitConfirmModal.setAttribute('aria-hidden', 'false');
            document.body.classList.add('modal-open');
        }

        async function submitTest(forceSubmit = false) {
            if (!state.test) {
                return;
            }
            if (state.isSubmitting) {
                return;
            }
            setStatus('Submitting attempt...');
            state.isSubmitting = true;
            els.submitBtn.disabled = true;
            const prevSubmitText = els.submitBtn.textContent;
            els.submitBtn.textContent = 'Submitting...';
            closeSubmitConfirmModal();

            const payload = {
                user_id: els.userId.value || null,
                answers: state.answers,
            };

            try {
                const res = await fetch('/agents/planner/test/submit', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                });

                const data = await res.json();
                if (!res.ok) {
                    throw new Error(data.detail || 'Submission failed');
                }

                handleReport(data.result);
                setStatus('Attempt recorded. Review the insights below.', 'success');
            } catch (err) {
                console.error(err);
                setStatus(err.message || 'Could not submit attempt', 'error');
                state.isSubmitting = false;
                els.submitBtn.disabled = false;
                els.submitBtn.textContent = prevSubmitText;
            }
        }

        async function applyDeepLink() {
            const params = new URLSearchParams(window.location.search);
            const section = (params.get('section') || '').toLowerCase();

            if (section !== 'mock-test') {
                return;
            }

            const target = document.getElementById('testCard');
            if (target && target.style.display !== 'none') {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }

        els.startBtn.addEventListener('click', startTest);
        els.resetBtn.addEventListener('click', () => {
            state.answers = {};
            state.reviewFlags = {};
            if (state.test) {
                renderFocusedQuestion();
            }
            setStatus('Selections cleared.');
        });
        els.submitBtn.addEventListener('click', (event) => {
            event.preventDefault();
            if (!state.test || state.isSubmitting) {
                return;
            }
            openSubmitConfirmModal();
        });
        if (els.submitConfirmCloseBtn) {
            els.submitConfirmCloseBtn.addEventListener('click', closeSubmitConfirmModal);
        }
        if (els.submitConfirmProceedBtn) {
            els.submitConfirmProceedBtn.addEventListener('click', () => submitTest(true));
        }
        if (els.submitConfirmModal) {
            els.submitConfirmModal.addEventListener('click', (event) => {
                if (event.target === els.submitConfirmModal) {
                    closeSubmitConfirmModal();
                }
            });
        }
        els.markReviewBtn.addEventListener('click', () => {
            if (!state.flatQuestions.length) {
                return;
            }
            const question = state.flatQuestions[state.currentQuestionIndex];
            if (!question) {
                return;
            }
            if (state.reviewFlags[question.question_id]) {
                delete state.reviewFlags[question.question_id];
            } else {
                state.reviewFlags[question.question_id] = true;
            }
            renderFocusedQuestion();
        });
        els.prevBtn.addEventListener('click', () => {
            if (state.currentQuestionIndex > 0) {
                state.currentQuestionIndex -= 1;
                renderFocusedQuestion();
            }
        });
        els.nextBtn.addEventListener('click', () => {
            if (state.currentQuestionIndex < state.flatQuestions.length - 1) {
                state.currentQuestionIndex += 1;
                renderFocusedQuestion();
            }
        });
        if (els.downloadAttemptBtn) {
            els.downloadAttemptBtn.addEventListener('click', downloadAttemptPaper);
        }
        prefillFromLocalProfile();
        hydrateIdentifierFromSession();
        applyDeepLink();
    })();
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html)
