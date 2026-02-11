from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import (
    auth,
    companies,
    contracts,
    dashboard,
    engineers,
    invoices,
    jobs,
    matching,
    orders,
    projects,
    quotations,
    reconciliation,
    reports,
    slack,
)

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["認証"])
app.include_router(companies.router, prefix="/api/v1/companies", tags=["企業"])
app.include_router(engineers.router, prefix="/api/v1/engineers", tags=["エンジニア"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["案件"])
app.include_router(quotations.router, prefix="/api/v1/quotations", tags=["見積"])
app.include_router(orders.router, prefix="/api/v1/orders", tags=["発注"])
app.include_router(contracts.router, prefix="/api/v1/contracts", tags=["契約"])
app.include_router(invoices.router, prefix="/api/v1/invoices", tags=["請求"])
app.include_router(matching.router, prefix="/api/v1/matching", tags=["マッチング"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["処理ジョブ"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["ダッシュボード"])
app.include_router(reconciliation.router, prefix="/api/v1/reconciliation", tags=["入金消込"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["レポート"])
app.include_router(slack.router, prefix="/api/v1/slack", tags=["Slack連携"])


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
