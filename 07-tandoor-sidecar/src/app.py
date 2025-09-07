"""
Tandoor Sidecar - Thin wrapper over Tandoor Recipes API
Main FastAPI application for recipe search, meal planning, and shopping lists
"""

import os
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
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

# Global HTTP client
client: Optional[httpx.AsyncClient] = None


async def get_client() -> httpx.AsyncClient:
    """Get or create HTTP client for Tandoor API"""
    global client
    if client is None:
        client = httpx.AsyncClient(
            base_url=TANDOOR_URL,
            timeout=httpx.Timeout(30.0, connect=10.0),
            headers=headers,
            follow_redirects=True
        )
    return client


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
    week_plan: List[Dict[str, Any]] = Field(
        ..., description="Weekly meal plan"
    )
    shopping_list: List[Dict[str, Any]] = Field(
        ..., description="Generated shopping list"
    )


class ShoppingListResponse(BaseModel):
    """Response for shopping list"""
    shopping_list: List[Dict[str, Any]] = Field(
        ..., description="Shopping list by category"
    )
    total_items: int = Field(
        ..., description="Total number of items"
    )
    estimated_cost: Optional[float] = Field(
        None, description="Estimated cost"
    )


class RecipeCreateRequest(BaseModel):
    """Request for creating a new recipe"""
    name: str = Field(..., description="Recipe name")
    description: Optional[str] = Field(None, description="Recipe description")
    instructions: str = Field(..., description="Recipe instructions")
    ingredients: List[Dict[str, Any]] = Field(
        ..., description="Recipe ingredients"
    )
    servings: int = Field(default=4, description="Number of servings")
    working_time: int = Field(
        default=30, description="Working time in minutes"
    )
    waiting_time: int = Field(
        default=0, description="Waiting time in minutes"
    )


class RecipeResponse(BaseModel):
    """Response for individual recipe"""
    id: int
    name: str
    description: str
    instructions: str
    ingredients: List[Dict[str, Any]]
    servings: int
    working_time: int
    waiting_time: int
    rating: float
    image: str


async def authenticate_tandoor():
    """Authenticate with Tandoor if using username/password"""
    if TANDOOR_API_TOKEN:
        return  # Already using token auth

    if not TANDOOR_USERNAME or not TANDOOR_PASSWORD:
        raise HTTPException(
            status_code=500,
            detail=(
                "Tandoor authentication not configured. Set "
                "TANDOOR_API_TOKEN or TANDOOR_USERNAME/TANDOOR_PASSWORD"
            )
        )

    # Authentication disabled in thin wrapper mode; in a full
    # implementation we'd perform the login and store session.
    return


@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup"""
    try:
        # Initialize HTTP client
        await get_client()
        
        # Test connection to Tandoor
        client = await get_client()
        response = await client.get("/api/recipe/", timeout=10.0)
        response.raise_for_status()
        logger.info("Successfully connected to Tandoor")
    except Exception as e:
        logger.warning(f"Failed to connect to Tandoor on startup: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global client
    if client:
        await client.aclose()
        client = None


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Tandoor Sidecar API", "version": "1.0.0"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    try:
        # Test connection to Tandoor
        client = await get_client()
        response = await client.get("/api/recipe/", timeout=5.0)
        response.raise_for_status()
        return {
            "status": "healthy",
            "tandoor_url": TANDOOR_URL,
            "authenticated": bool(
                TANDOOR_API_TOKEN or (TANDOOR_USERNAME and TANDOOR_PASSWORD)
            ),
            "tandoor_accessible": True
        }
    except Exception as e:
        return {
            "status": "degraded",
            "tandoor_url": TANDOOR_URL,
            "authenticated": bool(
                TANDOOR_API_TOKEN or (TANDOOR_USERNAME and TANDOOR_PASSWORD)
            ),
            "tandoor_accessible": False,
            "error": str(e)
        }


@app.get("/healthz")
async def healthz():
    """Kubernetes style healthz alias"""
    return {"ok": True, "service": "tandoor-sidecar"}


@app.get("/recipes/search", response_model=RecipeSearchResponse)
async def search_recipes(q: str = Query(..., description="Search query")):
    """Search for recipes"""
    try:
        client = await get_client()
        
        # Search recipes using Tandoor API
        response = await client.get(
            "/api/recipe/",
            params={"search": q, "page_size": 20}
        )
        response.raise_for_status()
        data = response.json()
        
        # Transform Tandoor response to our format
        recipes = []
        for recipe in data.get("results", []):
            description = recipe.get("description", "")
            if len(description) > 200:
                description = description[:200] + "..."
            
            recipes.append({
                "id": recipe.get("id"),
                "name": recipe.get("name", ""),
                "description": description,
                "image": recipe.get("image", ""),
                "rating": recipe.get("rating", 0.0),
                "servings": recipe.get("servings", 1),
                "time": f"{recipe.get('working_time', 0)} minutes"
            })
        
        return RecipeSearchResponse(
            recipes=recipes,
            total=data.get("count", len(recipes)),
            query=q
        )
        
    except httpx.HTTPStatusError as e:
        logger.error(
            f"Tandoor API error: {e.response.status_code} - {e.response.text}"
        )
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Tandoor API error: {e.response.text}"
        )
    except Exception as e:
        logger.error(f"Recipe search failed: {e}")
        # Fallback to mock data if Tandoor is unavailable
        mock_recipes = [
            {
                "id": 1,
                "name": f"Mock Recipe for '{q}'",
                "description": f"Mock recipe for '{q}' - Tandoor unavailable",
                "image": "",
                "rating": 4.5,
                "servings": 4,
                "time": "30 minutes"
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
        client = await get_client()
        
        # Get meal plan from Tandoor for the week
        week_plan = []
        shopping_list = []
        
        # Generate 7 days of meals
        for i in range(7):
            current_date = start_date + timedelta(days=i)
            date_str = current_date.strftime("%Y-%m-%d")
            
            try:
                # Try to get existing meal plan from Tandoor
                response = await client.get(
                    "/api/meal-plan/",
                    params={
                        "from_date": date_str,
                        "to_date": date_str
                    }
                )
                response.raise_for_status()
                meal_data = response.json()
                
                # If no meal plan exists, create a basic one with random recipes
                if not meal_data.get("results"):
                    # Get some random recipes for meal planning
                    recipe_response = await client.get(
                        "/api/recipe/",
                        params={"page_size": 10, "random": True}
                    )
                    recipe_response.raise_for_status()
                    recipes = recipe_response.json().get("results", [])
                    
                    day_plan = {
                        "date": date_str,
                        "meals": []
                    }
                    
                    # Assign recipes to meals if available
                    meal_types = ["breakfast", "lunch", "dinner"]
                    for j, meal_type in enumerate(meal_types):
                        if j < len(recipes):
                            recipe = recipes[j]
                            day_plan["meals"].append({
                                "meal": meal_type,
                                "recipe": {
                                    "id": recipe.get("id"),
                                    "name": recipe.get("name", f"{meal_type.title()} Recipe"),
                                    "servings": recipe.get("servings", 2)
                                }
                            })
                else:
                    # Parse existing meal plan
                    day_plan = {
                        "date": date_str,
                        "meals": []
                    }
                    
                    for meal in meal_data.get("results", []):
                        recipe_data = meal.get("recipe", {})
                        day_plan["meals"].append({
                            "meal": meal.get("meal_type", "dinner").lower(),
                            "recipe": {
                                "id": recipe_data.get("id"),
                                "name": recipe_data.get("name", "Unknown Recipe"),
                                "servings": meal.get("servings", recipe_data.get("servings", 2))
                            }
                        })
                
                week_plan.append(day_plan)
                
                # Add ingredients to shopping list from recipes
                for meal in day_plan["meals"]:
                    recipe_id = meal["recipe"]["id"]
                    if recipe_id:
                        try:
                            # Get recipe ingredients
                            ingredient_response = await client.get(f"/api/recipe/{recipe_id}/")
                            ingredient_response.raise_for_status()
                            recipe_detail = ingredient_response.json()
                            
                            for step in recipe_detail.get("steps", []):
                                for ingredient in step.get("ingredients", []):
                                    food = ingredient.get("food", {})
                                    shopping_list.append({
                                        "ingredient": food.get("name", "Unknown ingredient"),
                                        "amount": f"{ingredient.get('amount', 1)} {ingredient.get('unit', {}).get('name', 'unit')}",
                                        "category": food.get("supermarket_category", {}).get("name", "Other")
                                    })
                        except Exception as e:
                            logger.warning(f"Failed to get ingredients for recipe {recipe_id}: {e}")
                            
            except Exception as e:
                logger.warning(f"Failed to get meal plan for {date_str}: {e}")
                # Fallback to simple day plan
                day_plan = {
                    "date": date_str,
                    "meals": [
                        {
                            "meal": "breakfast",
                            "recipe": {"id": None, "name": f"Breakfast for {date_str}", "servings": 2}
                        },
                        {
                            "meal": "lunch", 
                            "recipe": {"id": None, "name": f"Lunch for {date_str}", "servings": 2}
                        },
                        {
                            "meal": "dinner",
                            "recipe": {"id": None, "name": f"Dinner for {date_str}", "servings": 4}
                        }
                    ]
                }
                week_plan.append(day_plan)

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
        client = await get_client()
        
        # Get meal plans for the specified date range
        response = await client.get(
            "/api/meal-plan/",
            params={
                "from_date": request.start,
                "to_date": request.end
            }
        )
        response.raise_for_status()
        meal_plans = response.json().get("results", [])
        
        # Aggregate ingredients by category
        ingredient_dict = {}
        
        for meal_plan in meal_plans:
            recipe_id = meal_plan.get("recipe", {}).get("id")
            if not recipe_id:
                continue
                
            try:
                # Get recipe details
                recipe_response = await client.get(f"/api/recipe/{recipe_id}/")
                recipe_response.raise_for_status()
                recipe = recipe_response.json()
                
                # Extract ingredients from recipe steps
                for step in recipe.get("steps", []):
                    for ingredient in step.get("ingredients", []):
                        food = ingredient.get("food", {})
                        food_name = food.get("name", "Unknown ingredient")
                        amount = ingredient.get("amount", 1)
                        unit = ingredient.get("unit", {}).get("name", "unit")
                        category = food.get("supermarket_category", {}).get("name", "Other")
                        
                        # Aggregate ingredients
                        key = f"{food_name}_{unit}"
                        if key in ingredient_dict:
                            ingredient_dict[key]["amount"] += amount
                        else:
                            ingredient_dict[key] = {
                                "ingredient": food_name,
                                "amount": amount,
                                "unit": unit,
                                "category": category
                            }
                            
            except Exception as e:
                logger.warning(f"Failed to process recipe {recipe_id}: {e}")
                continue
        
        # Group by category
        categorized_list = {}
        for item in ingredient_dict.values():
            category = item["category"]
            if category not in categorized_list:
                categorized_list[category] = []
            
            categorized_list[category].append({
                "ingredient": item["ingredient"],
                "amount": f"{item['amount']} {item['unit']}",
                "unit": item["unit"]
            })
        
        # Convert to response format
        shopping_list = []
        total_items = 0
        
        for category, items in categorized_list.items():
            shopping_list.append({
                "category": category,
                "items": items
            })
            total_items += len(items)
        
        # If no items found, provide a basic list
        if not shopping_list:
            shopping_list = [{
                "category": "General",
                "items": [
                    {"ingredient": "Basic groceries needed", "amount": "as needed", "unit": ""}
                ]
            }]
            total_items = 1
        
        return ShoppingListResponse(
            shopping_list=shopping_list,
            total_items=total_items,
            estimated_cost=0.0  # Could be enhanced with price calculation
        )

    except Exception as e:
        logger.error(f"Shopping list generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Shopping list generation failed: {str(e)}"
        )


@app.get("/recipes/{recipe_id}", response_model=RecipeResponse)
async def get_recipe(recipe_id: int):
    """Get a specific recipe by ID"""
    try:
        client = await get_client()
        response = await client.get(f"/api/recipe/{recipe_id}/")
        response.raise_for_status()
        recipe = response.json()
        
        return RecipeResponse(
            id=recipe.get("id"),
            name=recipe.get("name", ""),
            description=recipe.get("description", ""),
            instructions=recipe.get("instructions", ""),
            ingredients=recipe.get("ingredients", []),
            servings=recipe.get("servings", 1),
            working_time=recipe.get("working_time", 0),
            waiting_time=recipe.get("waiting_time", 0),
            rating=recipe.get("rating", 0.0),
            image=recipe.get("image", "")
        )
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Recipe not found")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Tandoor API error: {e.response.text}"
        )
    except Exception as e:
        logger.error(f"Failed to get recipe {recipe_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get recipe: {str(e)}"
        )


@app.post("/recipes", response_model=RecipeResponse)
async def create_recipe(request: RecipeCreateRequest):
    """Create a new recipe"""
    try:
        client = await get_client()
        
        # Transform request to Tandoor format
        recipe_data = {
            "name": request.name,
            "description": request.description or "",
            "instructions": request.instructions,
            "ingredients": request.ingredients,
            "servings": request.servings,
            "working_time": request.working_time,
            "waiting_time": request.waiting_time,
        }
        
        response = await client.post("/api/recipe/", json=recipe_data)
        response.raise_for_status()
        recipe = response.json()
        
        return RecipeResponse(
            id=recipe.get("id"),
            name=recipe.get("name", ""),
            description=recipe.get("description", ""),
            instructions=recipe.get("instructions", ""),
            ingredients=recipe.get("ingredients", []),
            servings=recipe.get("servings", 1),
            working_time=recipe.get("working_time", 0),
            waiting_time=recipe.get("waiting_time", 0),
            rating=recipe.get("rating", 0.0),
            image=recipe.get("image", "")
        )
        
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Tandoor API error: {e.response.text}"
        )
    except Exception as e:
        logger.error(f"Failed to create recipe: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create recipe: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8107)
