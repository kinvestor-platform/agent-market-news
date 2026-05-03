import argparse
import os
import sys
import textwrap


AGENT_TEMPLATE = textwrap.dedent("""\
    import asyncio
    import os
    from kinagent import BaseAgent, run_agent
    from kinagent.tools import fetch_url, web_search
    from kinagent.llm import LLMRouter


    class {class_name}(BaseAgent):
        agent_type = "{agent_type}"
        version = "0.1.0"

        def __init__(self):
            self.llm = LLMRouter(primary="gemini-flash", fallback="claude-haiku")
            self._tools = [web_search, fetch_url]

        async def handle(self, input: dict) -> dict:
            # TODO: implement your agent logic here
            return {{"result": "not implemented"}}


    if __name__ == "__main__":
        agent = {class_name}()
        marketplace_url = os.environ.get("MARKETPLACE_URL", "http://localhost:7777")
        asyncio.run(run_agent(agent, marketplace_url=marketplace_url, port=8000))
""")


def cmd_new(name: str) -> None:
    class_name = "".join(part.capitalize() for part in name.split("-")) + "Agent"
    agent_type = name.replace("-", "_")
    os.makedirs(f"{name}/agent", exist_ok=True)
    with open(f"{name}/agent/main.py", "w") as f:
        f.write(AGENT_TEMPLATE.format(class_name=class_name, agent_type=agent_type))
    print(f"Created {name}/agent/main.py")
    print(f"Run with: MARKETPLACE_URL=http://localhost:7777 python -m agent.main")


def cmd_validate(path: str = "agent.manifest.json") -> None:
    import json
    required = {"agent_type", "display_name", "version", "description", "compute"}
    with open(path) as f:
        manifest = json.load(f)
    missing = required - set(manifest.keys())
    if missing:
        print(f"INVALID — missing fields: {missing}")
        sys.exit(1)
    print(f"VALID — {manifest['agent_type']} v{manifest['version']}")


def cmd_run() -> None:
    import importlib
    import asyncio
    marketplace_url = os.environ.get("MARKETPLACE_URL")
    if not marketplace_url:
        print("Error: MARKETPLACE_URL environment variable not set")
        sys.exit(1)
    module = importlib.import_module("agent.main")
    from kinagent import BaseAgent as _BaseAgent
    agent_cls = next(
        v for v in vars(module).values()
        if isinstance(v, type) and issubclass(v, _BaseAgent) and v is not _BaseAgent
    )
    agent = agent_cls()
    asyncio.run(module.run_agent(agent, marketplace_url=marketplace_url))


def main() -> None:
    parser = argparse.ArgumentParser(prog="kinagent")
    sub = parser.add_subparsers(dest="command")

    new_p = sub.add_parser("new", help="Scaffold a new agent project")
    new_p.add_argument("name")

    sub.add_parser("validate", help="Validate agent.manifest.json")
    sub.add_parser("run", help="Run agent locally")

    args = parser.parse_args()
    if args.command == "new":
        cmd_new(args.name)
    elif args.command == "validate":
        cmd_validate()
    elif args.command == "run":
        cmd_run()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
