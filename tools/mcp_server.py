#!/usr/bin/env python3
"""Minimal stdio MCP server for read-only local arithmetic, newline JSON-RPC."""
import json
import sys
from agency_tools import SCHEMAS, OUTPUT_SCHEMAS, DESCRIPTIONS, run, strict_json

VERSIONS = {"2024-11-05", "2025-03-26", "2025-06-18"}

def handle(request):
    if type(request) is not dict or request.get("jsonrpc") != "2.0" or not isinstance(request.get("method"), str):
        return {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid request"}}
    if "id" not in request:
        return None
    response = {"jsonrpc": "2.0", "id": request["id"]}
    method, p = request["method"], request.get("params", {})
    try:
        if type(p) is not dict:
            raise ValueError("Parameters must be an object")
        if method == "initialize":
            version = p.get("protocolVersion")
            response["result"] = {"protocolVersion": version if version in VERSIONS else "2025-06-18", "capabilities": {"tools": {"listChanged": False}}, "serverInfo": {"name": "agency-erp-local", "version": "0.2.0"}}
        elif method == "ping":
            response["result"] = {}
        elif method == "tools/list":
            response["result"] = {"tools": [{"name": k, "description": DESCRIPTIONS[k], "inputSchema": v, "outputSchema": OUTPUT_SCHEMAS[k], "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}} for k,v in SCHEMAS.items()]}
        elif method == "tools/call":
            try:
                output = run(p.get("name"), p.get("arguments", {}))
                response["result"] = {"content": [{"type": "text", "text": json.dumps(output, allow_nan=False)}], "structuredContent": output, "isError": False}
            except (ValueError, TypeError, OverflowError) as exc:
                response["result"] = {"content": [{"type": "text", "text": str(exc)}], "isError": True}
        else:
            response["error"] = {"code": -32601, "message": "Method not found"}
    except (ValueError, TypeError, OverflowError) as exc:
        response["error"] = {"code": -32602, "message": str(exc)}
    return response

def main():
    while True:
        line = sys.stdin.buffer.readline(1_048_577)
        if not line:
            return
        if len(line) > 1_048_576:
            print(json.dumps({"jsonrpc":"2.0","id":None,"error":{"code":-32700,"message":"Input exceeds 1 MiB; closing transport"}}), flush=True)
            return
        try:
            result = handle(strict_json(line))
        except (ValueError, UnicodeError, RecursionError):
            result = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}
        if result is not None:
            print(json.dumps(result, allow_nan=False), flush=True)

if __name__ == "__main__":
    main()
