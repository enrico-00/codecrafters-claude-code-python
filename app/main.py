import argparse
import os
import sys
import json
import subprocess

# import markdown
# import yaml
# import frontmatter

from openai import OpenAI

SKILLS_PATH = ".claude/skills/"

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")


def read_skill(path: str):
    name, description, body = "", "", ""

    with open(path, "r") as file:
        for line in file:
            line_strip = line.strip()
            # print(line_strip, file=sys.stderr)
            if not line_strip or line_strip.startswith("---"):
                # print("a", file=sys.stderr)
                continue
            elif line_strip.startswith("name: "):
                # print("b", file=sys.stderr)
                name = line_strip.split(": ")[-1]
                # print(name, file=sys.stderr)
            elif line_strip.startswith("description: "):
                # print("c", file=sys.stderr)
                description = line_strip.split(": ")[-1]
                # print(description, file=sys.stderr)
            else:
                body = body + line

    return name, description, body


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-p", required=True)
    args = p.parse_args()

    skills_name = os.listdir(SKILLS_PATH)
    print(skills_name, file="sys.stderr")
    skills_description = []

    skills_content = "You have access to the following skills:\n"

    for skill in skills_name:
        skills_content = skills_content + "\n"
        # print("HIII", file=sys.stderr)
        # print(skill, file=sys.stderr)
        # f = open(os.path.join(SKILLS_PATH, skill, "SKILL.md"), "r")
        # print(f.read(), file=sys.stderr)
        # print(read_skill(os.path.join(SKILLS_PATH, skill, "SKILL.md")), file=sys.stderr)
        description = read_skill(os.path.join(SKILLS_PATH, skill, "SKILL.md"))[1]
        skills_description.append(description)
        skills_content = skills_content + "-" + skill + ": " + description

    print(skills_content, file=sys.stderr)
    # print(args.p, file=sys.stderr)

    if not API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    messages = [
        {
            "role": "system",
            "content": skills_content,
        },
        {"role": "user", "content": args.p},
    ]

    while True:
        chat = client.chat.completions.create(
            model="anthropic/claude-haiku-4.5",
            messages=messages,
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "Read",
                        "description": "Read and return the contents of a file",
                        "parameters": {
                            "type": "object",
                            "required": ["file_path"],
                            "properties": {
                                "file_path": {
                                    "type": "string",
                                    "description": "The path to the file to read",
                                }
                            },
                        },
                    },
                },
                {
                    "type": "function",
                    "function": {
                        "name": "Write",
                        "description": "Write content to a file",
                        "parameters": {
                            "type": "object",
                            "required": ["file_path", "content"],
                            "properties": {
                                "file_path": {
                                    "type": "string",
                                    "description": "The path of the file to write to",
                                },
                                "content": {
                                    "type": "string",
                                    "description": "The content to write to the file",
                                },
                            },
                        },
                    },
                },
                {
                    "type": "function",
                    "function": {
                        "name": "Bash",
                        "description": "Execute a shell command",
                        "parameters": {
                            "type": "object",
                            "required": ["command"],
                            "properties": {
                                "command": {
                                    "type": "string",
                                    "description": "The command to execute",
                                }
                            },
                        },
                    },
                },
            ],
        )

        if not chat.choices or len(chat.choices) == 0:
            raise RuntimeError("no choices in response")

        messages.append(chat.choices[0].message)

        if not chat.choices[0].message.tool_calls:
            print(chat.choices[0].message.content)

            break

        else:
            tool_calls = chat.choices[0].message.tool_calls
            for tool_call in tool_calls:
                if tool_call.function.name == "Read":
                    arguments = json.loads(tool_call.function.arguments)

                    file = open(arguments["file_path"])
                    content = file.read()
                    print(content, file=sys.stderr)

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": content,
                        }
                    )

                elif tool_call.function.name == "Write":
                    arguments = json.loads(tool_call.function.arguments)

                    content = arguments["content"]
                    with open(arguments["file_path"], "w") as file:
                        file.write(content)

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": content,
                        }
                    )

                elif tool_call.function.name == "Bash":
                    arguments = json.loads(tool_call.function.arguments)

                    command = arguments["command"]

                    output = subprocess.run(
                        command,
                        capture_output=True,
                        text=True,
                        check=True,
                        shell=True,
                    )

                    if output:
                        content = output.stdout
                    else:
                        content = stdout.stderr

                    # try:
                    #     output = subprocess.run(
                    #         command,
                    #         capture_output=True,
                    #         text=True,
                    #         check=True,
                    #         shell=True,
                    #     )

                    #     content = output.stdout
                    # except subprocess.CalledProcessError as e:
                    #     output = e.stderr.strip()

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": content,
                        }
                    )


if __name__ == "__main__":
    main()
