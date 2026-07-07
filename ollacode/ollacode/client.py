from __future__ import annotations
import json
import httpx
from typing import AsyncGenerator, Optional

OLLAMA_BASE = "http://localhost:11434"

class ToolCall:
    def __init__(self, name: str, arguments: dict, id: str = ""):
        self.name = name
        self.arguments = arguments
        self.id = id

    def __repr__(self):
        return f"ToolCall({self.name}, {self.arguments})"

class Message:
    def __init__(self, role: str, content: str = "", tool_calls: Optional[list[ToolCall]] = None,
                 tool_call_id: str = ""):
        self.role = role
        self.content = content
        self.tool_calls = tool_calls or []
        self.tool_call_id = tool_call_id

    def to_dict(self):
        d = {"role": self.role}
        if self.content:
            d["content"] = self.content
        if self.tool_calls:
            d["tool_calls"] = [
                {
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": json.dumps(tc.arguments),
                    },
                    "id": tc.id or f"call_{hash(tc.name) & 0xFFFFFFFF:08x}",
                }
                for tc in self.tool_calls
            ]
        if self.tool_call_id:
            d["tool_call_id"] = self.tool_call_id
        return d

    @classmethod
    def from_dict(cls, d: dict):
        if "tool_calls" in d:
            tcs = []
            for tc in d["tool_calls"]:
                args = {}
                if "function" in tc:
                    try:
                        args = json.loads(tc["function"].get("arguments", "{}"))
                    except json.JSONDecodeError:
                        args = {}
                    tcs.append(ToolCall(
                        name=tc["function"].get("name", ""),
                        arguments=args,
                        id=tc.get("id", ""),
                    ))
            return cls(role=d["role"], content=d.get("content", ""), tool_calls=tcs)
        if "tool_call_id" in d:
            return cls(role=d["role"], content=d.get("content", ""), tool_call_id=d["tool_call_id"])
        return cls(role=d["role"], content=d.get("content", ""))


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file (overwrites existing)",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file"},
                    "content": {"type": "string", "description": "Content to write"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Execute a bash command and get output",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Command to execute"},
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_dir",
            "description": "List contents of a directory",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_fetch",
            "description": "Fetch a web page and return its text content. Use this to get information from the internet.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to fetch"},
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the internet using DuckDuckGo. Results are ordered with trusted sources first (Reuters, AP, BBC, El País, etc). Use web_fetch to get full article content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query (be specific)"},
                    "max_results": {"type": "number", "description": "Maximum results (default 8)"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sys_info",
            "description": "Show system specifications: CPU, RAM, disk, OS version",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "battery_report",
            "description": "Show battery status and charge level",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "usb_list",
            "description": "List connected USB drives",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "disk_usage",
            "description": "Show disk usage for a path",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to check (default /)"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ping_test",
            "description": "Ping a host to test connectivity",
            "parameters": {
                "type": "object",
                "properties": {
                    "host": {"type": "string", "description": "Host to ping (default 8.8.8.8)"},
                    "count": {"type": "number", "description": "Number of pings (default 4)"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "port_scan",
            "description": "Scan common ports on a host to see which are open",
            "parameters": {
                "type": "object",
                "properties": {
                    "host": {"type": "string", "description": "Host to scan (default localhost)"},
                    "ports": {"type": "string", "description": "Comma-separated ports (default 22,80,443,3389,8080)"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "wifi_profiles",
            "description": "Scan and list available WiFi networks",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "pdf_extract",
            "description": "Extract text from a PDF file. Use for reading manuals, error docs, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to PDF file"},
                    "max_pages": {"type": "number", "description": "Max pages to extract (default 5)"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "gen_batch",
            "description": "Generate a Windows .bat repair script and save to file",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Output path (default script.bat)"},
                    "commands": {"type": "string", "description": "Batch commands to include"},
                    "title": {"type": "string", "description": "Script title"},
                },
                "required": ["commands"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "gen_powershell",
            "description": "Generate a Windows PowerShell .ps1 repair script and save to file",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Output path (default script.ps1)"},
                    "commands": {"type": "string", "description": "PowerShell commands to include"},
                    "title": {"type": "string", "description": "Script title"},
                },
                "required": ["commands"],
            },
        },
    },
]


class OllamaClient:
    def __init__(self, base_url: str = OLLAMA_BASE, model: str = "qwen2.5:3b"):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.http = httpx.AsyncClient(timeout=120.0)

    async def close(self):
        await self.http.aclose()

    async def chat(self, messages: list[Message], stream: bool = True) -> AsyncGenerator[dict, None]:
        payload = {
            "model": self.model,
            "messages": [m.to_dict() for m in messages],
            "stream": stream,
        }

        has_tool_model = await self._supports_tools()
        if has_tool_model and stream:
            payload["tools"] = TOOL_DEFINITIONS

        async with self.http.stream("POST", f"{self.base_url}/v1/chat/completions", json=payload) as resp:
            if resp.status_code != 200:
                error_body = await resp.aread()
                yield {"type": "error", "content": f"HTTP {resp.status_code}: {error_body.decode()}"}
                return

            if stream:
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        yield {"type": "chunk", "data": data}
                    except json.JSONDecodeError:
                        continue
            else:
                data = await resp.aread()
                yield {"type": "done", "data": json.loads(data)}

    async def _supports_tools(self):
        try:
            resp = await self.http.get(f"{self.base_url}/api/tags", timeout=5.0)
            if resp.status_code == 200:
                for m in resp.json().get("models", []):
                    if m["name"] == self.model:
                        caps = m.get("capabilities", [])
                        return "tools" in caps
            return False
        except Exception:
            return False

    async def list_models(self) -> list[dict]:
        resp = await self.http.get(f"{self.base_url}/api/tags", timeout=5.0)
        if resp.status_code == 200:
            return resp.json().get("models", [])
        return []

    def count_tokens(self, messages: list[Message]) -> int:
        total = 0
        for m in messages:
            total += len(m.content) // 2
            for tc in m.tool_calls:
                total += len(json.dumps(tc.arguments)) // 2
        return total
