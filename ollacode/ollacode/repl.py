from __future__ import annotations
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text
from rich import box

from .client import OllamaClient, Message, ToolCall
from .tools import execute_tool

console = Console()
HISTORY_FILE = Path.home() / ".ollacode_history"
SESSION_DIR = Path.home() / ".ollacode_sessions"
MAX_CONTEXT_TOKENS = 6000
KB_DIR = Path(__file__).resolve().parent.parent / "kb"
WINDOWS_KEYWORDS = [
    "windows", "win10", "win11", "error 0x", "pantalla azul", "bsod", "blue screen",
    "red", "network", "internet", "wifi", "dns", "dhcp", "ipconfig",
    "sfc", "dism", "chkdsk", "boot", "recuperar", "reparar",
    "lento", "disco 100", "virus", "driver", "actualización",
    "no enciende", "no arranca", "congela", "se apaga",
]

def _load_windows_kb() -> str:
    path = KB_DIR / "windows.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""

def _needs_windows_kb(text: str) -> bool:
    lower = text.lower()
    for kw in WINDOWS_KEYWORDS:
        if kw in lower:
            return True
    return False
SYSTEM_PROMPT = """Eres ollacode, un asistente AI con herramientas locales y de internet.
Herramientas: read_file, write_file, bash, list_dir, web_search, web_fetch.

FLUJO PARA INFORMACIÓN ACTUAL:
1. web_search(query) → encuentra fuentes (las ★ son confiables)
2. web_fetch(url) → lee el artículo COMPLETO de las mejores fuentes
3. Resume la información obtenida con datos concretos

NO respondas solo con los snippets del buscador. Siempre haz web_fetch a los artículos para leer el contenido real antes de responder.

Para preguntas generales responde directo sin herramientas.
Sé conciso. Responde en español."""


class OllamaREPL:
    def __init__(self, model: str = "qwen2.5:3b"):
        self.model = model
        self.client = OllamaClient(model=model)
        self.messages: list[Message] = [
            Message(role="system", content=SYSTEM_PROMPT)
        ]
        self.running = True
        self._load_history()

    async def start(self):
        self._print_banner()

        while self.running:
            try:
                user_input = Prompt.ask(f"\n[bold cyan]{self.model}[/]")
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not user_input.strip():
                continue

            cmd = self._parse_command(user_input)
            if cmd:
                await self._handle_command(cmd)
                continue

            if _needs_windows_kb(user_input):
                kb = _load_windows_kb()
                if kb and not any("Base de reparación" in m.content for m in self.messages):
                    console.print("[dim]📖 consultando base de reparación Windows...[/]")
                    self.messages.insert(1, Message(role="system", content=f"Tienes esta Base de reparación Windows. Úsala para responder:\n\n{kb[:2500]}"))

            self.messages.append(Message(role="user", content=user_input))
            await self._run_loop()

        await self.client.close()
        self._save_history()
        console.print("\n[dim]Bye![/]")

    async def _run_loop(self):
        max_iterations = 5
        for iteration in range(max_iterations):
            self._trim_context()

            response_text = ""
            tc_buffers: dict[int, dict] = {}
            finish_reason = None

            with console.status(f"[dim]thinking...[/]", spinner="dots"):
                async for event in self.client.chat(self.messages):
                    if event["type"] == "error":
                        console.print(f"[red]Error: {event['content']}[/]")
                        return
                    if event["type"] == "chunk":
                        data = event["data"]
                        choice = data.get("choices", [{}])[0]
                        delta = choice.get("delta", {})
                        fr = choice.get("finish_reason")
                        if fr:
                            finish_reason = fr

                        content = delta.get("content")
                        if content:
                            response_text += content

                        tcs = delta.get("tool_calls")
                        if tcs:
                            for tc in tcs:
                                idx = tc.get("index", 0)
                                if idx not in tc_buffers:
                                    tc_buffers[idx] = {
                                        "id": tc.get("id", ""),
                                        "type": tc.get("type", "function"),
                                        "function": {"name": "", "arguments": ""},
                                    }
                                buf = tc_buffers[idx]
                                if tc.get("id"):
                                    buf["id"] = tc["id"]
                                fn = tc.get("function", {})
                                if fn.get("name"):
                                    buf["function"]["name"] += fn["name"]
                                if fn.get("arguments"):
                                    buf["function"]["arguments"] += fn["arguments"]

            tool_calls = self._extract_tool_calls_from_buffers(tc_buffers)

            if response_text.strip():
                msg = Message(role="assistant", content=response_text.strip())
                self.messages.append(msg)
                console.print(Markdown(response_text.strip()))

            if tool_calls:
                for tc in tool_calls:
                    console.print(f"\n[dim]🔧 {tc.name}...[/]")
                    result = await execute_tool(tc.name, tc.arguments)
                    preview = result[:200] + "..." if len(result) > 200 else result
                    console.print(Panel(
                        Text(preview, style="dim"),
                        title=f"[bold]{tc.name}[/]",
                        border_style="blue",
                        box=box.SQUARE,
                        padding=(0, 1),
                    ))
                    self.messages.append(Message(
                        role="assistant",
                        content="",
                        tool_calls=[tc],
                    ))
                    self.messages.append(Message(
                        role="tool",
                        content=result[:3000],
                        tool_call_id=tc.id or f"call_{hash(tc.name) & 0xFFFFFFFF:08x}",
                    ))
            else:
                break
        else:
            console.print("[yellow]Reached max iterations without final response[/]")

    def _extract_tool_calls_from_buffers(self, buffers: dict) -> list[ToolCall]:
        tcs = []
        for idx in sorted(buffers.keys()):
            buf = buffers[idx]
            fn = buf.get("function", {})
            name = fn.get("name", "")
            args_str = fn.get("arguments", "{}")
            try:
                args = json.loads(args_str) if args_str else {}
            except json.JSONDecodeError:
                args = {}
            if name:
                tcs.append(ToolCall(
                    name=name,
                    arguments=args,
                    id=buf.get("id", ""),
                ))
        return tcs

    def _extract_tool_calls(self, response_data: dict) -> list[ToolCall]:
        tcs = []
        for tc_raw in response_data.get("tool_calls", []):
            if "function" in tc_raw:
                try:
                    args = json.loads(tc_raw["function"].get("arguments", "{}"))
                except json.JSONDecodeError:
                    args = {}
                tcs.append(ToolCall(
                    name=tc_raw["function"].get("name", ""),
                    arguments=args,
                    id=tc_raw.get("id", ""),
                ))
        return tcs

    def _trim_context(self):
        total = self.client.count_tokens(self.messages)
        while total > MAX_CONTEXT_TOKENS and len(self.messages) > 4:
            removed = self.messages.pop(2)
            total = self.client.count_tokens(self.messages)

    def _parse_command(self, text: str) -> Optional[dict]:
        text = text.strip()
        if text == "/exit" or text == "/quit":
            return {"type": "exit"}
        if text == "/help":
            return {"type": "help"}
        if text == "/clear":
            return {"type": "clear"}
        if text.startswith("/model "):
            return {"type": "model", "args": text[7:].strip()}
        if text.startswith("/save "):
            return {"type": "save", "args": text[6:].strip()}
        if text.startswith("/load "):
            return {"type": "load", "args": text[6:].strip()}
        if text == "/models":
            return {"type": "list_models"}
        if text == "/context":
            return {"type": "context"}
        if text == "/tokens":
            return {"type": "tokens"}
        return None

    async def _handle_command(self, cmd: dict):
        t = cmd["type"]
        if t == "exit":
            self.running = False
        elif t == "help":
            self._print_help()
        elif t == "clear":
            self.messages = [Message(role="system", content=SYSTEM_PROMPT)]
            console.print("[dim]Context cleared[/]")
        elif t == "model":
            self.model = cmd["args"]
            self.client.model = self.model
            console.print(f"[green]Switched to [bold]{self.model}[/][/]")
        elif t == "save":
            name = cmd["args"]
            await self._save_session(name)
        elif t == "load":
            name = cmd["args"]
            await self._load_session(name)
        elif t == "list_models":
            await self._show_models()
        elif t == "context":
            self._show_context()
        elif t == "tokens":
            total = self.client.count_tokens(self.messages)
            console.print(f"[dim]~{total} tokens in context (limit: {MAX_CONTEXT_TOKENS})[/]")

    async def _show_models(self):
        models = await self.client.list_models()
        table = Table(title="Available Models", box=box.ROUNDED)
        table.add_column("Name", style="cyan")
        table.add_column("Size", style="dim")
        table.add_column("Capabilities", style="green")

        for m in models:
            size_gb = m["size"] / (1024**3)
            caps = ", ".join(m.get("capabilities", []))
            table.add_row(m["name"], f"{size_gb:.1f} GB", caps)

        console.print(table)

    def _show_context(self):
        console.print(f"[dim]Messages in context: {len(self.messages)}[/]")
        total = self.client.count_tokens(self.messages)
        console.print(f"[dim]Estimated tokens: ~{total} (limit: {MAX_CONTEXT_TOKENS})[/]")

    async def _save_session(self, name: str):
        SESSION_DIR.mkdir(parents=True, exist_ok=True)
        path = SESSION_DIR / f"{name}.json"
        data = {
            "model": self.model,
            "messages": [m.to_dict() for m in self.messages],
            "saved_at": datetime.now().isoformat(),
        }
        path.write_text(json.dumps(data, indent=2))
        console.print(f"[green]Session saved: [bold]{path}[/][/]")

    async def _load_session(self, name: str):
        path = SESSION_DIR / f"{name}.json"
        if not path.exists():
            console.print(f"[red]Session not found: {name}[/]")
            return
        data = json.loads(path.read_text())
        self.model = data.get("model", self.model)
        self.client.model = self.model
        self.messages = [Message.from_dict(m) for m in data["messages"]]
        console.print(f"[green]Session loaded: [bold]{name}[/] ({data['saved_at']})[/]")

    def _print_banner(self):
        console.print()
        console.print(Panel(
            "[bold cyan]ollacode[/] — lightweight AI CLI for local Ollama models\n"
            "[dim]Type /help for commands | /exit to quit[/]",
            box=box.ROUNDED,
            border_style="cyan",
            padding=(1, 2),
        ))

    def _print_help(self):
        table = Table(box=box.ROUNDED, title="Commands")
        table.add_column("Command", style="cyan")
        table.add_column("Description", style="white")
        table.add_row("/model <name>", "Switch model (e.g. /model qwen2.5:3b)")
        table.add_row("/models", "List available models")
        table.add_row("/clear", "Clear conversation context")
        table.add_row("/context", "Show context stats")
        table.add_row("/save <name>", "Save session")
        table.add_row("/load <name>", "Load session")
        table.add_row("/help", "Show this help")
        table.add_row("/exit", "Exit ollacode")
        console.print(table)

    def _load_history(self):
        if HISTORY_FILE.exists():
            import readline
            try:
                readline.read_history_file(str(HISTORY_FILE))
            except Exception:
                pass

    def _save_history(self):
        import readline
        try:
            readline.write_history_file(str(HISTORY_FILE))
        except Exception:
            pass
