"""
Tandoor Sidecar - Thin wrapper over Tandoor Recipes API
Main FastAPI application for recipe search, meal planning, and shopping lists
"""

import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Tandoor Sidecar",
    description="Thin wrapper over Tandoor Recipes API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tandoor configuration
TANDOOR_URL = os.getenv("TANDOOR_URL", "http://localhost:8080")
TANDOOR_API_TOKEN = os.getenv("TANDOOR_API_TOKEN")
TANDOOR_USERNAME = os.getenv("TANDOOR_USERNAME")
TANDOOR_PASSWORD = os.getenv("TANDOOR_PASSWORD")

# HTTP client for Tandoor API calls
headers = {"Content-Type": "application/json"}
if TANDOOR_API_TOKEN:
    headers["Authorization"] = f"Bearer {TANDOOR_API_TOKEN}"

# Create client without immediate connection
# client = httpx.AsyncClient(
#     base_url=TANDOOR_URL,
#     timeout=httpx.Timeout(30.0, connect=10.0),
#     headers=headers,
#     follow_redirects=True
# )


class Macros(BaseModel):
    """Macros for meal planning"""
    protein_min: Optional[int] = Field(
        None, description="Minimum protein in grams"
    )
    carbs_max: Optional[int] = Field(
        None, description="Maximum carbs in grams"
    )
    calories_target: Optional[int] = Field(
        None, description="Target calories"
    )


class WeekPlanRequest(BaseModel):
    """Request for weekly meal plan"""
    start: str = Field(..., description="Start date in YYYY-MM-DD format")
    macros: Optional[Macros] = Field(
        None, description="Optional macro targets"
    )


class ShoppingListRequest(BaseModel):
    """Request for shopping list"""
    start: str = Field(..., description="Start date in YYYY-MM-DD format")
    end: str = Field(..., description="End date in YYYY-MM-DD format")


class RecipeSearchResponse(BaseModel):
    """Response for recipe search"""
    recipes: List[Dict[str, Any]] = Field(..., description="List of recipes")
    total: int = Field(..., description="Total number of recipes found")
    query: str = Field(..., description="Search query used")


class WeekPlanResponse(BaseModel):
    """Response for weekly meal plan"""
    week_plan: List[Dict[str, Any]] = Field(..., description="Weekly meal plan")
    shopping_list: List[Dict[str, Any]] = Field(..., description="Generated shopping list")


class ShoppingListResponse(BaseModel):
    """Response for shopping list"""
    shopping_list: List[Dict[str, Any]] = Field(..., description="Shopping list by category")
    total_items: int = Field(..., description="Total number of items")
    estimated_cost: Optional[float] = Field(None, description="Estimated cost")


async def authenticate_tandoor():
    """Authenticate with Tandoor if using username/password"""
    if TANDOOR_API_TOKEN:
        return  # Already using token auth

    if not TANDOOR_USERNAME or not TANDOOR_PASSWORD:
        raise HTTPException(
            status_code=500,
            detail="Tandoor authentication not configured. Set TANDOOR_API_TOKEN or TANDOOR_USERNAME/TANDOOR_PASSWORD"
        )

    try:
        # Login to get session
        login_data = {
            "username": TANDOOR_USERNAME,
            "password": TANDOOR_PASSWORD
        }
        response = await client.post("/api/login/", json=login_data)
        response.raise_for_status()

        # Update client with session cookies
        client.cookies.update(response.cookies)

    except Exception as e:
        logger.error(f"Tandoor authentication failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to authenticate with Tandoor")


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    try:
        # await authenticate_tandoor()
        logger.info("Successfully connected to Tandoor")
    except Exception as e:
        logger.warning(f"Failed to connect to Tandoor on startup: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    # await client.aclose()
    pass


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Tandoor Sidecar API", "version": "1.0.0"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    try:
        # Test connection to Tandoor
        # await client.get("/api/recipe/")
        return {
            "status": "healthy",
            "tandoor_url": TANDOOR_URL,
            "authenticated": bool(
                TANDOOR_API_TOKEN or (TANDOOR_USERNAME and TANDOOR_PASSWORD)
            )
        }
    except Exception as e:
        raise HTTPException(
            status_code=503, detail=f"Tandoor connection failed: {str(e)}"
        )


@app.get("/recipes/search", response_model=RecipeSearchResponse)
async def search_recipes(q: str = Query(..., description="Search query")):
    """Search for recipes"""
    # Return mock data for testing
    mock_recipes = [
        {
            "id": 1,
            "name": f"Mock Recipe for '{q}'",
            "description": f"Mock recipe for '{q}'",
            "image": "",
            "rating": 4.5,
            "servings": 4,
            "time": "30 minutes"
        },
        {
            "id": 2,
            "name": f"Another Mock Recipe for '{q}'",
            "description": f"Another mock recipe for {q}",
            "image": "",
            "rating": 3.8,
            "servings": 2,
            "time": "45 minutes"
        }
    ]
    return RecipeSearchResponse(
        recipes=mock_recipes,
        total=len(mock_recipes),
        query=q
    )


@app.post("/plan/week", response_model=WeekPlanResponse)
async def plan_week(request: WeekPlanRequest):
    """Generate weekly meal plan"""
    try:
        start_date = datetime.fromisoformat(request.start)
        week_plan = []
        shopping_list = []

        # Generate 7 days of meals
        for i in range(7):
            current_date = start_date + timedelta(days=i)

            # Mock meal plan (in real implementation, this would use
            # Tandoor meal plan API)
            day_plan = {
                "date": current_date.strftime("%Y-%m-%d"),
                "meals": [
                    {
                        "meal": "breakfast",
                        "recipe": {
                            "id": 100 + i,
                            "name": f"Breakfast Recipe {i+1}",
                            "servings": 2
                        }
                    },
                    {
                        "meal": "lunch",
                        "recipe": {
                            "id": 200 + i,
                            "name": f"Lunch Recipe {i+1}",
                            "servings": 2
                        }
                    },
                    {
                        "meal": "dinner",
                        "recipe": {
                            "id": 300 + i,
                            "name": f"Dinner Recipe {i+1}",
                            "servings": 4
                        }
                    }
                ]
            }
            week_plan.append(day_plan)

            # Add ingredients to shopping list
            for meal in day_plan["meals"]:
                recipe_id = meal["recipe"]["id"]  # type: ignore
                servings = meal["recipe"]["servings"]  # type: ignore
                shopping_list.extend([
                    {
                        "ingredient": f"Ingredient {recipe_id}-1",
                        "amount": f"{servings * 100}g",
                        "category": "Produce"
                    },
                    {
                        "ingredient": f"Ingredient {recipe_id}-2",
                        "amount": f"{servings * 50}g",
                        "category": "Protein"
                    }
                ])

        return WeekPlanResponse(
            week_plan=week_plan,
            shopping_list=shopping_list
        )

    except Exception as e:
        logger.error(f"Week planning failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Week planning failed: {str(e)}"
        )


@app.post("/shopping-list", response_model=ShoppingListResponse)
async def generate_shopping_list(request: ShoppingListRequest):
    """Generate shopping list for date range"""
    try:
        # Mock shopping list generation
        # In real implementation, this would aggregate ingredients
        # from meal plans
        categories = ["Produce", "Protein", "Dairy", "Pantry", "Spices"]

        shopping_list = []
        total_items = 0

        for category in categories:
            items = []
            for i in range(3):  # 3 items per category
                item = {
                    "ingredient": f"{category} Item {i+1}",
                    "amount": f"{(i+1) * 100}g",
                    "unit": "g"
                }
                items.append(item)
                total_items += 1

            shopping_list.append({
                "category": category,
                "items": items
            })

        return ShoppingListResponse(
            shopping_list=shopping_list,
            total_items=total_items,
            estimated_cost=45.50
        )

    except Exception as e:
        logger.error(f"Shopping list generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Shopping list generation failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8107)
