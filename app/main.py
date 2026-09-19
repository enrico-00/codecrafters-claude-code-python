import argparse
import os
import sys
import json
import subprocess

from openai import OpenAI

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-p", required=True)
    args = p.parse_args()

    if not API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    messages = [{"role": "user", "content": args.p}]

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
                    print("Hiiiiiiii", file=sys.stderr)
                    print("hello" + command, file=sys.stderr)

                    try:
                        output = subprocess.run(
                            command,
                            capture_output=True,
                            text=True,
                            check=True,
                            shell=True,
                        )
                        print("jaga", file=sys.stderr)
                        print(output, file=sys.stderr)
                        print("jaga1", file=sys.stderr)
                        print(output.stdout, file=sys.stderr)
                        print("jaga2", file=sys.stderr)
                        print(output.stderr, file=sys.stderr)
                    except subprocess.CalledProcessError as e:
                        print("YOOOOOOOOOOOOO", file=sys.stderr)
                        print(e.stderr.strip(), file=sys.stderr)
                        output = e.stderr.strip()

                    print("HUIiiiiiiii", file=sys.stderr)
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "output": str(output.stdout),
                        }
                    )


if __name__ == "__main__":
    main()
