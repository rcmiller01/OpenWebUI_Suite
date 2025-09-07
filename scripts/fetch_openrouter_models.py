#!/usr/bin/env python3
"""
Fetch real OpenRouter model names and update configurations
"""

import os
import requests
import json


def get_openrouter_models():
    """Fetch available models from OpenRouter API"""
    
    # Check for API key in environment
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ OPENROUTER_API_KEY not found in environment")
        return None
    
    print("🔍 Fetching models from OpenRouter...")
    
    try:
        response = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            models = response.json()
            return models.get("data", [])
        else:
            print(f"❌ API Error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None


def categorize_models(models):
    """Categorize models by capability and cost"""
    
    if not models:
        return {}
    
    # High-end models for technical and general precision work
    tech_models = []
    
    # Balanced models for legal and general use
    legal_models = []
    
    # Specialized therapy/psychology models
    therapy_models = []
    
    # Fast, cheap models for regulated data (as fallback)
    regulated_models = []
    
    for model in models:
        model_id = model.get("id", "")
        name = model.get("name", "")
        context_length = model.get("context_length", 0)
        pricing = model.get("pricing", {})
        
        # Skip if missing essential info
        if not model_id or not pricing:
            continue
            
        prompt_cost = float(pricing.get("prompt", "0"))
        completion_cost = float(pricing.get("completion", "0"))
        avg_cost = (prompt_cost + completion_cost) / 2
        
        # Categorize based on model characteristics
        model_lower = model_id.lower()
        
        if any(x in model_lower for x in ["gpt-4", "claude-3", "gemini-pro", "command-r+"]):
            if avg_cost < 0.00001:  # Very cheap
                regulated_models.append(model_id)
            elif any(x in model_lower for x in ["therapist", "therapy", "counseling", "mental"]):
                therapy_models.append(model_id)
            elif any(x in model_lower for x in ["legal", "law", "contract"]):
                legal_models.append(model_id)
            else:
                tech_models.append(model_id)
                
        elif any(x in model_lower for x in ["llama", "mixtral", "qwen", "deepseek"]):
            if avg_cost < 0.000005:  # Very cheap
                regulated_models.append(model_id)
            elif context_length > 32000:  # Long context for technical work
                tech_models.append(model_id)
            else:
                legal_models.append(model_id)
                
        elif avg_cost < 0.000003:  # Ultra cheap models
            regulated_models.append(model_id)
    
    # Sort by estimated quality/capability
    tech_models.sort(key=lambda x: (
        0 if "gpt-4" in x else
        1 if "claude-3" in x else
        2 if "gemini" in x else 3
    ))
    
    legal_models.sort(key=lambda x: (
        0 if "gpt-4" in x else
        1 if "claude-3" in x else
        2 if "command" in x else 3
    ))
    
    therapy_models.sort(key=lambda x: (
        0 if "claude" in x else
        1 if "gpt-4" in x else 2
    ))
    
    regulated_models.sort(key=lambda x: (
        0 if "llama" in x else
        1 if "qwen" in x else 2
    ))
    
    return {
        "tech": tech_models[:5],  # Top 5 for each category
        "legal": legal_models[:5],
        "therapy": therapy_models[:3] if therapy_models else tech_models[:3],
        "regulated": regulated_models[:3]
    }


def print_model_recommendations(categorized):
    """Print recommended model configurations"""
    
    print("\n🎯 Recommended Model Configurations")
    print("=" * 60)
    
    for category, models in categorized.items():
        if models:
            print(f"\n{category.upper()}:")
            for i, model in enumerate(models, 1):
                print(f"  {i}. {model}")
            
            # Format for environment variables
            model_list = ",".join(models)
            env_var = f"OPENROUTER_PRIORITIES_{category.upper()}"
            print(f"\n  Environment Variable:")
            print(f"  {env_var}=\"{model_list}\"")


def generate_env_updates(categorized):
    """Generate environment variable updates"""
    
    updates = []
    
    if categorized.get("tech"):
        updates.append(f"OPENROUTER_PRIORITIES_TECH={','.join(categorized['tech'])}")
    
    if categorized.get("legal"):
        updates.append(f"OPENROUTER_PRIORITIES_LEGAL={','.join(categorized['legal'])}")
    
    if categorized.get("therapy"):
        updates.append(f"OPENROUTER_PRIORITIES_PSYCHOTHERAPY={','.join(categorized['therapy'])}")
    
    if categorized.get("regulated"):
        updates.append(f"OPENROUTER_PRIORITIES_REGULATED={','.join(categorized['regulated'])}")
    
    # Add a good default model
    if categorized.get("tech"):
        updates.append(f"OPENROUTER_MODEL_DEFAULT={categorized['tech'][0]}")
    
    return updates


def main():
    """Main function"""
    
    print("🚀 OpenRouter Model Configuration Tool")
    print("=" * 50)
    
    # Fetch models
    models = get_openrouter_models()
    if not models:
        print("\n❌ Could not fetch models. Please check your API key and connection.")
        return
    
    print(f"✅ Found {len(models)} available models")
    
    # Categorize models
    categorized = categorize_models(models)
    
    # Print recommendations
    print_model_recommendations(categorized)
    
    # Generate environment updates
    env_updates = generate_env_updates(categorized)
    
    print(f"\n📝 Environment Variable Updates")
    print("-" * 50)
    for update in env_updates:
        print(update)
    
    # Write to file for easy copying
    with open("openrouter_models.env", "w") as f:
        f.write("# OpenRouter Model Priorities - Generated\n")
        f.write("# Copy these to your .env file\n\n")
        for update in env_updates:
            f.write(f"{update}\n")
    
    print(f"\n💾 Configuration saved to: openrouter_models.env")
    print("📋 Copy these variables to your .env file to use real model names")


if __name__ == "__main__":
    main()
