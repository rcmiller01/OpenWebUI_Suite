#!/usr/bin/env python3
"""
Environment Variable Configuration Manager for OpenWebUI Suite
Checks for missing environment variables and prompts for them interactively.

Environment Variables for Service Control:
- ENABLE_TANDOOR=1      : Enable Tandoor sidecar validation
- ENABLE_OPENBB=1       : Enable OpenBB sidecar validation  
- COMPOSE_PROFILES      : Comma-separated profiles (e.g., "extras,ui")
- REQUIRE_EXTRAS_STRICT : If 1, require extras when profiles include them
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import re


def _on(v):  # truthy env helper
    return str(v).lower() in ("1", "true", "yes", "on")


ENABLE_TANDOOR = _on(os.getenv("ENABLE_TANDOOR", "0"))
ENABLE_OPENBB  = _on(os.getenv("ENABLE_OPENBB",  "0"))

# Profiles from systemd or shell (e.g., COMPOSE_PROFILES=extras,ui)
EXTRA_PROFILES = {p.strip() for p in os.getenv("COMPOSE_PROFILES", "").split(",") if p.strip()}

# If you want CI to be strict later, flip this to 1. For first-time deploys, keep 0.
REQUIRE_EXTRAS_STRICT = _on(os.getenv("REQUIRE_EXTRAS_STRICT", "0"))


def service_enabled(name: str) -> bool:
    """
    A service is 'enabled' for validation if either:
      - You explicitly set ENABLE_<NAME>=1, OR
      - (Strict mode) the 'extras' profile is on (or the service's own profile).
    """
    if name == "tandoor":
        return ENABLE_TANDOOR or (REQUIRE_EXTRAS_STRICT and ("extras" in EXTRA_PROFILES or "tandoor" in EXTRA_PROFILES))
    if name == "openbb":
        return ENABLE_OPENBB  or (REQUIRE_EXTRAS_STRICT and ("extras" in EXTRA_PROFILES or "openbb" in EXTRA_PROFILES))
    return True


# Environment variable definitions for each service
ENV_VARIABLES = {
    # Global/Core Variables
    "CORE": {
        "REDIS_URL": {
            "default": "redis://localhost:6379",
            "description": "Redis connection URL for caching and task queues",
            "required": False,
            "example": "redis://localhost:6379"
        },
        "ENABLE_OTEL": {
            "default": "false",
            "description": "Enable OpenTelemetry tracing",
            "required": False,
            "example": "true"
        },
        "OTEL_EXPORTER_OTLP_ENDPOINT": {
            "default": None,
            "description": "OpenTelemetry OTLP endpoint for traces",
            "required": False,
            "example": "http://jaeger:14268"
        },
        "OTEL_SERVICE_NAME": {
            "default": "pipelines-gateway",
            "description": "Service name for OpenTelemetry",
            "required": False,
            "example": "openwebui-gateway"
        }
    },
    
    # 00-pipelines-gateway
    "PIPELINES_GATEWAY": {
        "RATE_LIMIT_PER_MIN": {
            "default": "0",
            "description": "Rate limit per minute (0 = disabled)",
            "required": False,
            "example": "60"
        },
        "RATE_LIMIT_BURST": {
            "default": None,
            "description": "Rate limit burst capacity",
            "required": False,
            "example": "10"
        },
        "REMOTE_CODE_ROUTING": {
            "default": "true",
            "description": "Enable remote code routing",
            "required": False,
            "example": "true"
        },
        "REMOTE_CODE_MIN_CHARS": {
            "default": "350",
            "description": "Minimum characters for remote code routing",
            "required": False,
            "example": "350"
        },
        "REMOTE_CODE_KEYWORDS": {
            "default": "python,javascript,typescript,java,cpp,rust,go,sql,html,css",
            "description": "Keywords for remote code detection",
            "required": False,
            "example": "python,javascript,sql"
        },
        "PIPELINE_TIMEOUT_SECONDS": {
            "default": "0",
            "description": "Pipeline timeout in seconds (0 = no timeout)",
            "required": False,
            "example": "300"
        },
        "TASK_WORKER_ENABLED": {
            "default": "true",
            "description": "Enable background task worker",
            "required": False,
            "example": "true"
        },
        "TASK_QUEUE_NAME": {
            "default": "pipeline_tasks",
            "description": "Redis task queue name",
            "required": False,
            "example": "pipeline_tasks"
        },
        "TASK_DQL_NAME": {
            "default": "pipeline_tasks_dlq",
            "description": "Redis dead letter queue name",
            "required": False,
            "example": "pipeline_tasks_dlq"
        },
        "FILE_STORAGE_PATH": {
            "default": "data/files",
            "description": "File storage directory path",
            "required": False,
            "example": "/data/files"
        },
        "MAX_FILE_BYTES": {
            "default": "2097152",
            "description": "Maximum file size in bytes (2MB default)",
            "required": False,
            "example": "5242880"
        },
        "ALLOWED_FILE_EXTENSIONS": {
            "default": "txt,md,py,js,ts,html,css,json,xml,csv,log",
            "description": "Allowed file extensions (comma-separated)",
            "required": False,
            "example": "txt,md,py,js,json"
        },
        "ENABLE_FILE_SNIPPETS": {
            "default": "true",
            "description": "Enable file snippet extraction",
            "required": False,
            "example": "true"
        },
        "FILE_SNIPPET_MAX_CHARS": {
            "default": "1200",
            "description": "Maximum characters in file snippets",
            "required": False,
            "example": "1200"
        },
        "FILE_SNIPPET_KEYWORDS": {
            "default": "function,class,def,async,import,export,const,let,var",
            "description": "Keywords for file snippet extraction",
            "required": False,
            "example": "function,class,def"
        },
        "GATEWAY_DB": {
            "default": "/data/gateway.db",
            "description": "SQLite database path for gateway projects",
            "required": False,
            "example": "/data/gateway.db"
        }
    },
    
    # 07-tandoor-sidecar
    "TANDOOR_SIDECAR": {
        "TANDOOR_URL": {
            "default": "http://localhost:8080",
            "description": "Tandoor Recipes instance URL",
            "required": True,
            "example": "http://tandoor:8080"
        },
        "TANDOOR_API_TOKEN": {
            "default": None,
            "description": "Tandoor API token (preferred authentication method)",
            "required": False,
            "example": "your_api_token_here"
        },
        "TANDOOR_USERNAME": {
            "default": None,
            "description": "Tandoor username (alternative to API token)",
            "required": False,
            "example": "admin"
        },
        "TANDOOR_PASSWORD": {
            "default": None,
            "description": "Tandoor password (alternative to API token)",
            "required": False,
            "example": "your_password_here",
            "sensitive": True
        }
    },
    
    # 08-openbb-sidecar
    "OPENBB_SIDECAR": {
        "OPENBB_PAT": {
            "default": "",
            "description": "OpenBB Personal Access Token",
            "required": True,
            "example": "your_openbb_pat_here",
            "sensitive": True
        }
    },
    
    # 16-fastvlm-sidecar
    "FASTVLM_SIDECAR": {
        "FASTVLM_MODEL": {
            "default": "apple/fastvlm-2.7b",
            "description": "Hugging Face model ID for FastVLM",
            "required": False,
            "example": "apple/fastvlm-2.7b"
        },
        "DEVICE": {
            "default": "cuda",
            "description": "PyTorch device (cuda/cpu/mps)",
            "required": False,
            "example": "cuda"
        },
        "TORCH_DTYPE": {
            "default": "float16",
            "description": "PyTorch data type",
            "required": False,
            "example": "float16"
        },
        "MAX_TOKENS": {
            "default": "192",
            "description": "Maximum tokens for VLM generation",
            "required": False,
            "example": "256"
        }
    },
    
    # Ollama Plugin
    "OLLAMA_PLUGIN": {
        "OLLAMA_HOST": {
            "default": "http://core2-gpu:11434",
            "description": "Ollama server URL",
            "required": True,
            "example": "http://localhost:11434"
        },
        "OWUI_MEMORY_PATH": {
            "default": "./data/memory.sqlite",
            "description": "SQLite database path for Ollama plugin memory",
            "required": False,
            "example": "/data/memory.sqlite"
        }
    }
}


def load_env_file(env_file: Path) -> Dict[str, str]:
    """Load environment variables from .env file."""
    env_vars = {}
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip('"\'')
                    env_vars[key.strip()] = value
    return env_vars


def save_env_file(env_file: Path, env_vars: Dict[str, str]) -> None:
    """Save environment variables to .env file."""
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write("# OpenWebUI Suite Environment Variables\n")
        f.write(f"# Generated on {os.popen('date').read().strip()}\n\n")
        
        # Group by service
        current_service = None
        for key, value in sorted(env_vars.items()):
            # Determine service from key
            service = get_service_for_var(key)
            if service != current_service:
                f.write(f"\n# {service}\n")
                current_service = service
            
            # Quote values that contain spaces or special characters
            if ' ' in value or any(c in value for c in '&|;()<>'):
                value = f'"{value}"'
            
            f.write(f"{key}={value}\n")


def get_service_for_var(var_name: str) -> str:
    """Get the service name for a given environment variable."""
    for service, variables in ENV_VARIABLES.items():
        if var_name in variables:
            return service
    return "UNKNOWN"


def prompt_for_value(var_name: str, var_config: Dict[str, Any]) -> Optional[str]:
    """Prompt user for environment variable value."""
    description = var_config.get("description", "")
    default = var_config.get("default")
    example = var_config.get("example", "")
    sensitive = var_config.get("sensitive", False)
    
    print(f"\n📋 {var_name}")
    print(f"   Description: {description}")
    if example:
        print(f"   Example: {example}")
    if default:
        print(f"   Default: {default}")
    
    prompt = f"   Enter value"
    if default:
        prompt += f" (press Enter for default)"
    prompt += ": "
    
    if sensitive:
        import getpass
        value = getpass.getpass(prompt)
    else:
        value = input(prompt).strip()
    
    if not value and default:
        return str(default)
    elif not value:
        return None
    
    return value


def validate_env_value(var_name: str, value: str, var_config: Dict[str, Any]) -> bool:
    """Validate environment variable value."""
    # Basic validation rules
    if var_name.endswith('_URL') and value:
        # Basic URL validation
        if not re.match(r'^https?://', value):
            print(f"⚠️  Warning: {var_name} should be a valid URL starting with http:// or https://")
            return False
    
    if var_name.endswith('_PORT') and value:
        # Port validation
        try:
            port = int(value)
            if not 1 <= port <= 65535:
                print(f"⚠️  Error: {var_name} must be a valid port number (1-65535)")
                return False
        except ValueError:
            print(f"⚠️  Error: {var_name} must be a valid integer")
            return False
    
    if var_name.endswith('_TIMEOUT') and value:
        # Timeout validation
        try:
            timeout = int(value)
            if timeout < 0:
                print(f"⚠️  Error: {var_name} must be a positive integer")
                return False
        except ValueError:
            print(f"⚠️  Error: {var_name} must be a valid integer")
            return False
    
    return True


def check_missing_variables(env_vars: Dict[str, str]) -> List[tuple]:
    """Check for missing required environment variables."""
    missing = []
    
    for service, variables in ENV_VARIABLES.items():
        # Check if service should be validated
        service_name = service.lower().replace("_sidecar", "").replace("_", "")
        
        # Skip validation for disabled services
        if service == "TANDOOR_SIDECAR" and not service_enabled("tandoor"):
            continue
        if service == "OPENBB_SIDECAR" and not service_enabled("openbb"):
            continue
            
        for var_name, var_config in variables.items():
            if var_config.get("required", False) and var_name not in env_vars:
                missing.append((service, var_name, var_config))
    
    return missing


def print_service_status(env_vars: Dict[str, str]) -> None:
    """Print status of environment variables by service."""
    print("\n" + "="*60)
    print("🔧 OPENWEBUI SUITE ENVIRONMENT STATUS")
    print("="*60)
    
    for service, variables in ENV_VARIABLES.items():
        print(f"\n📦 {service}")
        print("-" * 40)
        
        # Check if service is disabled
        if service == "TANDOOR_SIDECAR" and not service_enabled("tandoor"):
            print("⚪ DISABLED (ENABLE_TANDOOR=0; not required)")
            continue
        if service == "OPENBB_SIDECAR" and not service_enabled("openbb"):
            print("⚪ DISABLED (ENABLE_OPENBB=0; not required)")
            continue
        
        for var_name, var_config in variables.items():
            status = "✅ SET" if var_name in env_vars else "❌ MISSING"
            required = "🔴 REQUIRED" if var_config.get("required", False) else "🟡 OPTIONAL"
            
            value_display = ""
            if var_name in env_vars:
                value = env_vars[var_name]
                if var_config.get("sensitive", False):
                    value_display = f" = {'*' * min(len(value), 8)}"
                else:
                    value_display = f" = {value[:50]}{'...' if len(value) > 50 else ''}"
            
            print(f"   {status} {required} {var_name}{value_display}")


def main():
    """Main environment variable checker."""
    print("🚀 OpenWebUI Suite Environment Variable Manager")
    print("=" * 50)
    
    # Find .env.prod file
    env_file = Path(".env.prod")
    if not env_file.exists():
        print(f"📝 Creating new environment file: {env_file}")
        env_vars = {}
    else:
        print(f"📖 Loading existing environment file: {env_file}")
        env_vars = load_env_file(env_file)
    
    # Add environment variables from os.environ
    for key in os.environ:
        if any(key in service_vars for service_vars in ENV_VARIABLES.values()):
            env_vars[key] = os.environ[key]
    
    # Check for missing variables
    missing = check_missing_variables(env_vars)
    
    # Print current status
    print_service_status(env_vars)
    
    if missing:
        print(f"\n⚠️  Found {len(missing)} missing required variables!")
        print("\nWould you like to configure them now? (y/n): ", end="")
        response = input().strip().lower()
        
        if response in ['y', 'yes']:
            print("\n🔧 Configuring missing variables...")
            
            for service, var_name, var_config in missing:
                print(f"\n📦 Service: {service}")
                value = prompt_for_value(var_name, var_config)
                
                if value:
                    if validate_env_value(var_name, value, var_config):
                        env_vars[var_name] = value
                        print(f"✅ Set {var_name}")
                    else:
                        print(f"❌ Skipped {var_name} due to validation error")
                else:
                    print(f"⏭️  Skipped {var_name}")
            
            # Ask about optional variables
            print("\n🔧 Would you like to configure optional variables? (y/n): ", end="")
            response = input().strip().lower()
            
            if response in ['y', 'yes']:
                for service, variables in ENV_VARIABLES.items():
                    # Skip disabled services for optional variables too
                    if service == "TANDOOR_SIDECAR" and not service_enabled("tandoor"):
                        continue
                    if service == "OPENBB_SIDECAR" and not service_enabled("openbb"):
                        continue
                        
                    for var_name, var_config in variables.items():
                        if not var_config.get("required", False) and var_name not in env_vars:
                            print(f"\n📦 Service: {service}")
                            value = prompt_for_value(var_name, var_config)
                            
                            if value:
                                if validate_env_value(var_name, value, var_config):
                                    env_vars[var_name] = value
                                    print(f"✅ Set {var_name}")
            
            # Save the file
            save_env_file(env_file, env_vars)
            print(f"\n💾 Saved environment variables to {env_file}")
    
    else:
        print("\n✅ All required environment variables are configured!")
    
    # Final status
    print("\n" + "="*60)
    print("🎯 CONFIGURATION COMPLETE")
    print("="*60)
    
    total_vars = sum(len(vars) for vars in ENV_VARIABLES.values())
    configured = len(env_vars)
    print(f"📊 Configured: {configured}/{total_vars} variables")
    
    print(f"\n📋 Next steps:")
    print(f"   1. Review {env_file} and adjust values as needed")
    print(f"   2. Deploy with: ./scripts/deploy_with_deps.sh")
    print(f"   3. Test deployment: docker-compose -f compose.prod.yml up -d")
    
    return 0 if not missing else 1


if __name__ == "__main__":
    sys.exit(main())
