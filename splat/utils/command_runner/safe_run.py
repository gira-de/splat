from typing import Literal, cast

COMMAND_WHITELIST = Literal[
    "/usr/local/bin/pipenv", "/usr/bin/yarn", "/usr/local/bin/poetry", "/usr/bin/git", "/usr/local/bin/uv"
]

COMMAND_ARGS_WHITELIST: dict[COMMAND_WHITELIST, list[tuple[str, ...]]] = {
    "/usr/local/bin/pipenv": [
        ("install",),
        ("requirements",),
        ("run", "pip", "freeze"),
        ("run", "pip-audit"),
        ("install", "pip-audit"),
        ("upgrade",),
        ("graph",),
        ("update",),
    ],
    "/usr/bin/yarn": [("install",), ("audit",), ("upgrade",)],
    "/usr/local/bin/poetry": [
        ("sync",),
        ("export",),
        ("add",),
        ("lock",),
        ("add", "pip-audit"),
        ("run", "pip-audit"),
        ("env", "use"),
    ],
    "/usr/bin/git": [("check-ignore",)],
    "/usr/local/bin/uv": [
        ("sync",),
        ("export",),
        ("run", "pip-audit"),
        ("add",),
        ("lock",),
    ],
}


def is_command_whitelisted(cmd: str, args: list[str]) -> bool:
    if cmd not in COMMAND_ARGS_WHITELIST:
        return False
    allowed_args = COMMAND_ARGS_WHITELIST[cast(COMMAND_WHITELIST, cmd)]

    for arg in allowed_args:
        if args[: len(arg)] == list(arg):
            # Ensures no flags are present in the allowed args part
            if all(not part.startswith("-") for part in args[: len(arg)]):
                return True
    return False
