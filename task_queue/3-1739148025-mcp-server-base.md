# Task: MCPサーバー共通基盤

role: core-dev
priority: 3
created_at: 2026-02-10T01:00:00Z

## Description

Create mcp-servers/common/ with shared MCP server infrastructure. mcp_base.py: Base MCP server class using MCP Python SDK (stdio transport). Standard tools: execute_input (receives JSON order data, returns result), check_status (health check), take_screenshot. schema.py: Pydantic models for input data (OrderInputData with fields matching Excel parser output) and output data (ExecutionResult with success/failure, confirmation_number, screenshot_path, error_details). screenshot.py: Screenshot capture and file management utility. All MCP servers inherit from this base. Write tests.
