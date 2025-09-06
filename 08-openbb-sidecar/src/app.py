from __future__ import annotations
import os
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openbb import obb

# Initialize OpenBB
obb.account.login(pat=os.getenv("OPENBB_PAT", ""))

app = FastAPI(title="OpenBB Sidecar", version="0.1.0")


class PortfolioSnapshotRequest(BaseModel):
    portfolio_id: Optional[str] = None
    include_positions: bool = True
    include_performance: bool = True


class BudgetStatusRequest(BaseModel):
    budget_id: Optional[str] = None
    period: str = "monthly"  # daily, weekly, monthly, yearly


class ContractsRenewalsRequest(BaseModel):
    days_ahead: int = 30
    contract_types: Optional[List[str]] = None


@app.post("/portfolio/snapshot")
async def portfolio_snapshot(req: PortfolioSnapshotRequest):
    """
    Get portfolio snapshot with positions and performance
    """
    try:
        # Get portfolio data from OpenBB
        portfolio = obb.portfolio.load(req.portfolio_id or "default")

        result = {
            "portfolio_id": req.portfolio_id or "default",
            "total_value": float(portfolio.total_value),
            "total_cost": float(portfolio.total_cost),
            "total_gain_loss": float(portfolio.total_gain_loss),
            "total_gain_loss_percent": float(portfolio.total_gain_loss_percent)
        }

        if req.include_positions:
            positions = []
            for pos in portfolio.positions:
                positions.append({
                    "symbol": pos.symbol,
                    "quantity": float(pos.quantity),
                    "cost_basis": float(pos.cost_basis),
                    "current_price": float(pos.current_price),
                    "market_value": float(pos.market_value),
                    "gain_loss": float(pos.gain_loss),
                    "gain_loss_percent": float(pos.gain_loss_percent)
                })
            result["positions"] = positions

        if req.include_performance:
            # Get performance metrics
            performance = obb.portfolio.performance(portfolio)
            result["performance"] = {
                "sharpe_ratio": float(performance.sharpe_ratio),
                "volatility": float(performance.volatility),
                "max_drawdown": float(performance.max_drawdown),
                "beta": float(performance.beta)
            }

        return result

    except Exception as e:
        raise HTTPException(500, f"Portfolio snapshot failed: {str(e)}")


@app.post("/budget/status")
async def budget_status(req: BudgetStatusRequest):
    """
    Get budget status and spending analysis
    """
    try:
        # This would integrate with budgeting systems
        # For now, return mock data structure
        return {
            "budget_id": req.budget_id or "default",
            "period": req.period,
            "total_budget": 5000.00,
            "total_spent": 3200.50,
            "remaining": 1799.50,
            "categories": [
                {
                    "name": "Housing",
                    "budgeted": 2000.00,
                    "spent": 1800.00,
                    "remaining": 200.00,
                    "percent_used": 90.0
                },
                {
                    "name": "Food",
                    "budgeted": 800.00,
                    "spent": 650.00,
                    "remaining": 150.00,
                    "percent_used": 81.25
                },
                {
                    "name": "Transportation",
                    "budgeted": 600.00,
                    "spent": 450.00,
                    "remaining": 150.00,
                    "percent_used": 75.0
                }
            ],
            "alerts": [
                "Housing budget 90% used",
                "Food budget trending over"
            ]
        }

    except Exception as e:
        raise HTTPException(500, f"Budget status failed: {str(e)}")


@app.post("/contracts/renewals")
async def contracts_renewals(req: ContractsRenewalsRequest):
    """
    Get upcoming contract renewals and expirations
    """
    try:
        # This would integrate with contract management systems
        # For now, return mock data structure
        return {
            "days_ahead": req.days_ahead,
            "contract_types": req.contract_types or ["all"],
            "upcoming_renewals": [
                {
                    "contract_id": "CONT-001",
                    "type": "subscription",
                    "description": "Software License - Annual",
                    "renewal_date": "2025-10-15",
                    "days_until_renewal": 12,
                    "current_cost": 1200.00,
                    "auto_renew": True,
                    "vendor": "TechCorp Inc"
                },
                {
                    "contract_id": "CONT-002",
                    "type": "service",
                    "description": "Cloud Hosting - Monthly",
                    "renewal_date": "2025-09-30",
                    "days_until_renewal": 26,
                    "current_cost": 450.00,
                    "auto_renew": False,
                    "vendor": "CloudProvider LLC"
                }
            ],
            "expiring_contracts": [
                {
                    "contract_id": "CONT-003",
                    "type": "insurance",
                    "description": "Property Insurance",
                    "expiration_date": "2025-11-01",
                    "days_until_expiration": 28,
                    "current_cost": 800.00,
                    "renewal_required": True,
                    "vendor": "Insurance Co"
                }
            ],
            "summary": {
                "total_upcoming": 2,
                "total_expiring": 1,
                "total_monthly_cost": 2450.00
            }
        }

    except Exception as e:
        raise HTTPException(500, f"Contracts renewals failed: {str(e)}")


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "openbb_connected": True}


@app.get("/healthz")
async def healthz():
    """Kubernetes style healthz alias"""
    return {"ok": True, "service": "openbb-sidecar"}


@app.get("/market/snapshot")
async def market_snapshot():
    """
    Get current market snapshot
    """
    try:
        # Get market data from OpenBB
        market_data = obb.market.snapshot()

        return {
            "timestamp": market_data.timestamp.isoformat(),
            "indices": {
                "sp500": {
                    "price": float(market_data.sp500.price),
                    "change": float(market_data.sp500.change),
                    "change_percent": float(market_data.sp500.change_percent)
                },
                "nasdaq": {
                    "price": float(market_data.nasdaq.price),
                    "change": float(market_data.nasdaq.change),
                    "change_percent": float(market_data.nasdaq.change_percent)
                },
                "dowjones": {
                    "price": float(market_data.dowjones.price),
                    "change": float(market_data.dowjones.change),
                    "change_percent": float(
                        market_data.dowjones.change_percent
                    )
                }
            },
            "commodities": {
                "gold": float(market_data.gold.price),
                "silver": float(market_data.silver.price),
                "oil": float(market_data.oil.price)
            }
        }

    except Exception as e:
        raise HTTPException(500, f"Market snapshot failed: {str(e)}")
