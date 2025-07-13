#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools import TOOL_SCHEMAS
from mcp.types import Tool

# Test tool schema processing
print("=== Testing Tool Schema Processing ===")

print("\n1. Original TOOL_SCHEMAS:")
for i, schema in enumerate(TOOL_SCHEMAS[:2]):  # Show first 2
    print(f"Schema {i+1}: {schema}")

print("\n2. Creating Tool objects:")
tools = []
for schema in TOOL_SCHEMAS:
    # Filter out None values
    filtered_schema = {k: v for k, v in schema.items() if v is not None}
    tool = Tool(**filtered_schema)
    tools.append(tool)

print(f"Created {len(tools)} tools")

print("\n3. Tool model_dump() with exclude_none=True:")
for i, tool in enumerate(tools[:2]):  # Show first 2
    dumped = tool.model_dump(exclude_none=True)
    print(f"Tool {i+1}: {dumped}")

print("\n4. Tool model_dump() without exclude_none:")
for i, tool in enumerate(tools[:2]):  # Show first 2
    dumped = tool.model_dump()
    print(f"Tool {i+1}: {dumped}")
