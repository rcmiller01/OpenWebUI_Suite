# Tandoor Sidecar (07-tandoor-sidecar)

## Overview
Thin wrapper over Tandoor Recipes providing a simplified API for recipe search, meal planning, and shopping list generation.

## Architecture
- **Port**: 8107
- **Framework**: FastAPI with async HTTP client
- **Backend**: Tandoor Recipes API integration
- **Authentication**: Tandoor session/API token via environment variables

## API Endpoints

### GET /recipes/search
Search for recipes by query string.

**Parameters**:
- `q` (query string): Search term for recipes

**Response**:
```json
{
  "recipes": [
    {
      "id": 123,
      "name": "Chicken Rice",
      "description": "Delicious chicken rice recipe",
      "image": "https://tandoor.example.com/media/recipe_123.jpg",
      "rating": 4.5,
      "servings": 4,
      "time": "45 minutes"
    }
  ],
  "total": 25,
  "query": "chicken rice"
}
```

### POST /plan/week
Generate a weekly meal plan.

**Request Body**:
```json
{
  "start": "2024-01-15",
  "macros": {
    "protein_min": 100,
    "carbs_max": 200,
    "calories_target": 2000
  }
}
```

**Response**:
```json
{
  "week_plan": [
    {
      "date": "2024-01-15",
      "meals": [
        {
          "meal": "breakfast",
          "recipe": {
            "id": 123,
            "name": "Oatmeal",
            "servings": 1
          }
        },
        {
          "meal": "lunch",
          "recipe": {
            "id": 456,
            "name": "Chicken Salad",
            "servings": 2
          }
        }
      ]
    }
  ],
  "shopping_list": [
    {
      "ingredient": "Chicken breast",
      "amount": "500g",
      "category": "Meat"
    }
  ]
}
```

### POST /shopping-list
Generate a shopping list for a date range.

**Request Body**:
```json
{
  "start": "2024-01-15",
  "end": "2024-01-21"
}
```

**Response**:
```json
{
  "shopping_list": [
    {
      "category": "Produce",
      "items": [
        {
          "ingredient": "Onions",
          "amount": "3",
          "unit": "pieces"
        },
        {
          "ingredient": "Tomatoes",
          "amount": "500",
          "unit": "g"
        }
      ]
    }
  ],
  "total_items": 15,
  "estimated_cost": 45.50
}
```

### GET /health
Health check endpoint.

## Features

### Recipe Search
- Full-text search across recipe names and descriptions
- Pagination support
- Recipe metadata including ratings, servings, and cooking time

### Meal Planning
- Weekly meal plan generation
- Optional macro-based filtering (protein, carbs, calories)
- Automatic shopping list generation
- Recipe scaling based on servings

### Shopping Lists
- Ingredient aggregation across multiple recipes
- Category-based organization
- Amount consolidation for same ingredients
- Cost estimation (if available in Tandoor)

### Authentication
- Environment-based configuration
- Support for both session cookies and API tokens
- Secure credential handling

## Configuration

### Environment Variables
```bash
TANDOOR_URL=https://your-tandoor-instance.com
TANDOOR_API_TOKEN=your_api_token_here
# OR
TANDOOR_USERNAME=your_username
TANDOOR_PASSWORD=your_password
```

### Docker Setup
```yaml
# docker-compose.yml
version: '3.8'
services:
  tandoor:
    image: vabene1111/recipes:latest
    # ... tandoor configuration

  tandoor-sidecar:
    build: .
    ports:
      - "8107:8107"
    environment:
      - TANDOOR_URL=http://tandoor:8080
      - TANDOOR_API_TOKEN=${TANDOOR_API_TOKEN}
    depends_on:
      - tandoor
```

## Development

### Running Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export TANDOOR_URL=https://your-tandoor.com
export TANDOOR_API_TOKEN=your_token

# Start the service
python start.py
```

### Testing
```bash
# Run tests
python test_api.py
```

## Integration

The Tandoor Sidecar integrates with other OpenWebUI Suite services:

- **Pipelines Gateway** (8088): Can use recipes in AI workflows
- **Intent Router** (8101): Can route recipe-related queries
- **Memory 2.0** (8102): Can store meal plans and preferences
- **Feeling Engine** (8103): Can analyze recipe sentiment
- **BYOF Tool Hub** (8106): Can execute recipe-related tools

## Important Notes

- **AGPL Compliance**: This sidecar only calls Tandoor's public API and does not modify any Tandoor code
- **API Compatibility**: Designed to work with Tandoor Recipes v1.x API
- **Error Handling**: Graceful degradation when Tandoor is unavailable
- **Caching**: Built-in caching for recipe search results
- **Rate Limiting**: Respects Tandoor's API rate limits

## Future Enhancements

- Recipe import/export functionality
- Nutritional analysis integration
- Smart meal planning with dietary restrictions
- Recipe recommendation engine
- Integration with nutrition tracking services
