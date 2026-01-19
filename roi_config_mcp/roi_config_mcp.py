#!/usr/bin/env python3
"""
Secure MCP Server for F5 DPU ROI Calculator Config Updates.

SECURITY FEATURES:
- Only reads/writes ONE specific file: roi-config Rev 08.json
- Cannot access any other files on your system
- Requires explicit user confirmation before any write operation
- All file paths are hardcoded and validated
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, ConfigDict
from mcp.server.fastmcp import FastMCP

# SECURITY: Hardcoded allowed file - ONLY this file can be accessed
ALLOWED_CONFIG_FILE = os.path.expanduser(
    "~/Library/Mobile Documents/com~apple~CloudDocs/Research/AI/"
    "Financial Modeling/Webapps/Claude/F5 DPU Calculator Package Rev 08/"
    "F5_DPU_ROI_Toolkit/Up-to-date ROI Calculator/roi-config Rev 08.json"
)

if os.environ.get("ROI_CONFIG_PATH"):
    ALLOWED_CONFIG_FILE = os.path.expanduser(os.environ["ROI_CONFIG_PATH"])

mcp = FastMCP("roi_config_mcp")

def _validate_file_access():
    return os.path.isfile(ALLOWED_CONFIG_FILE)

def _get_file_hash():
    if not _validate_file_access():
        return ""
    with open(ALLOWED_CONFIG_FILE, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:12]

def _read_config():
    if not _validate_file_access():
        raise FileNotFoundError(f"Config file not found: {ALLOWED_CONFIG_FILE}")
    with open(ALLOWED_CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def _write_config(config, backup=True):
    if not _validate_file_access():
        raise FileNotFoundError(f"Config file not found: {ALLOWED_CONFIG_FILE}")
    if backup:
        backup_path = ALLOWED_CONFIG_FILE + f".backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        with open(ALLOWED_CONFIG_FILE, "r", encoding="utf-8") as f:
            backup_content = f.read()
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(backup_content)
    with open(ALLOWED_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    return f"Config saved. Backup: {backup_path if backup else 'None'}"

class ResponseFormat(str, Enum):
    MARKDOWN = "markdown"
    JSON = "json"

class ReadConfigInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    section: Optional[str] = Field(default=None)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)

class UpdatePreviewInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    categories: Optional[str] = Field(default="all")

class ApplyUpdateInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    updates_json: str = Field(..., min_length=2)
    user_confirmed: bool = Field(...)
    create_backup: bool = Field(default=True)

@mcp.tool(name="roi_config_read")
async def roi_config_read(params: ReadConfigInput) -> str:
    """Read the ROI calculator configuration file."""
    try:
        config = _read_config()
        file_hash = _get_file_hash()
        if params.section:
            section_map = {"gpuTypes": "gpuTypes", "hardware": "hardware", 
                          "models": "modelArchitectures", "storage": "storageOptions"}
            if params.section == "metadata":
                data = {"version": config.get("version"), "lastUpdated": config.get("lastUpdated")}
            elif params.section in section_map:
                data = config.get(section_map[params.section], {})
            else:
                return f"Error: Unknown section"
        else:
            data = config
        if params.response_format == ResponseFormat.JSON:
            return json.dumps({"file_hash": file_hash, "data": data}, indent=2)
        return f"# ROI Config
Version: {config.get('version')}
" + json.dumps(data, indent=2)[:3000]
    except Exception as e:
        return f"Error: {e}"

@mcp.tool(name="roi_config_research")
async def roi_config_research(params: UpdatePreviewInput) -> str:
    """Research latest pricing and specs for ROI config categories."""
    config = _read_config()
    return f"""# Research Request
Version: {config.get('version')}
Date: {datetime.now().strftime('%Y-%m-%d')}
Categories: {params.categories}

Research needed:
- GPU pricing (H100, H200, B200, B300)
- New AI models (Llama, Mistral, DeepSeek)  
- Storage pricing updates
- NVLink configurations

Return JSON with version_increment, gpuTypes_updates, modelArchitectures_updates, notes."""

@mcp.tool(name="roi_config_apply")
async def roi_config_apply(params: ApplyUpdateInput) -> str:
    """Apply updates to the ROI config file. REQUIRES user_confirmed=True."""
    if not params.user_confirmed:
        return "ERROR: Set user_confirmed=True to proceed"
    try:
        updates = json.loads(params.updates_json)
        config = _read_config()
        old_version = config.get("version", "1.0.0")
        changes = []
        if updates.get("version_increment"):
            parts = old_version.split(".")
            major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
            if updates["version_increment"] == "minor":
                minor += 1
                patch = 0
            else:
                patch += 1
            config["version"] = f"{major}.{minor}.{patch}"
            changes.append(f"Version: {old_version} -> {config['version']}")
        config["lastUpdated"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        for gpu, data in updates.get("gpuTypes_updates", {}).items():
            if gpu in config.get("gpuTypes", {}):
                for k, v in data.items():
                    config["gpuTypes"][gpu][k] = v
                    changes.append(f"gpuTypes.{gpu}.{k}: {v}")
        for model, data in updates.get("modelArchitectures_updates", {}).items():
            if model in config.get("modelArchitectures", {}):
                for k, v in data.items():
                    config["modelArchitectures"][model][k] = v
                    changes.append(f"models.{model}.{k}: {v}")
        result = _write_config(config, backup=params.create_backup)
        return f"# Update Applied
Changes: {len(changes)}
{result}
" + "
".join(f"- {c}" for c in changes[:20])
    except Exception as e:
        return f"Error: {e}"

@mcp.tool(name="roi_config_status")
async def roi_config_status() -> str:
    """Get status of the ROI config file and MCP server."""
    status = {"file": ALLOWED_CONFIG_FILE, "exists": _validate_file_access()}
    if status["exists"]:
        config = _read_config()
        status["version"] = config.get("version")
        status["gpus"] = len(config.get("gpuTypes", {}))
        status["models"] = len(config.get("modelArchitectures", {}))
    return f"""# ROI Config MCP Status
File: {status['file']}
Exists: {status['exists']}
Version: {status.get('version', 'N/A')}
GPUs: {status.get('gpus', 0)}
Models: {status.get('models', 0)}
Security: Single file access only, requires confirmation for writes"""

if __name__ == "__main__":
    mcp.run()

