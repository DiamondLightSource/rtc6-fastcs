import re
from pathlib import Path


def parse_execution_list_file(filepath: str | Path) -> list[str]:
    """
    Parse a LaserDESK execution list file and return command strings
    ready for dispatch_list_command.

    Strips the n_ prefix and first argument (card number) from each command.
    Skips header lines and blank lines.
    """
    commands: list[str] = []
    in_command_section = False

    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if "Command List:" in line:
                in_command_section = True
                continue
            if not in_command_section:
                continue

            # Strip trailing semicolon
            line = line.rstrip(";")

            # Match pattern: n_command_name(card_no, arg1, arg2, ...)
            # or n_command_name(card_no)
            match = re.match(r"^n_(\w+)\((\d+)(?:,\s*(.*))?\)$", line)
            if match:
                func_name = match.group(1)
                remaining_args = match.group(3)  # may be None
                if remaining_args:
                    commands.append(f"{func_name}({remaining_args})")
                else:
                    commands.append(f"{func_name}()")

    return commands
