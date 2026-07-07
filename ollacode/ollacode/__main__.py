import asyncio
import sys
from pathlib import Path
from .client import OllamaClient, Message
from .repl import OllamaREPL, _needs_windows_kb, _load_windows_kb


def main():
    model = "qwen2.5:3b"
    pipe_mode = False
    prompt = None

    args = sys.argv[1:]
    i = 0
    known_models = {"qwen2.5:3b", "deepseek-r1:1.5b", "deepseek-r1:1.5b-ctx"}
    while i < len(args):
        if args[i] in ("-p", "--print"):
            pipe_mode = True
        elif args[i] in ("-m", "--model"):
            i += 1
            if i < len(args):
                model = args[i]
        elif not args[i].startswith("-"):
            if any(k in args[i].lower() for k in ("qwen", "deepseek", "llama", "mistral")):
                model = args[i]
            elif prompt is None:
                prompt = args[i]
        i += 1

    if pipe_mode:
        if prompt is None and not sys.stdin.isatty():
            prompt = sys.stdin.read().strip()

        async def run_pipe():
            client = OllamaClient(model=model)
            msgs = [
                Message(role="system", content="Eres un asistente útil con acceso a internet vía web_search y web_fetch. Responde de forma directa."),
            ]
            if prompt and _needs_windows_kb(prompt):
                kb = _load_windows_kb()
                if kb:
                    msgs.append(Message(role="system", content=f"Base de reparación Windows:\n{kb[:2000]}"))
            msgs.append(Message(role="user", content=prompt or ""))
            text = ""
            async for event in client.chat(msgs):
                if event["type"] == "chunk":
                    d = event["data"]
                    delta = d.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content")
                    if content:
                        text += content
            print(text.strip())
            await client.close()

        asyncio.run(run_pipe())
        return

    repl = OllamaREPL(model=model)
    try:
        asyncio.run(repl.start())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
