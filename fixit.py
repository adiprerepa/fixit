import json
import libtmux
import os
import openai
import platform
from typing import List, Optional
BASH_HISTORY_LOC = os.environ.get("HOME") + "/.bash_history"
ZSH_HISTORY_LOC = os.environ.get("HOME") + "/.zsh_history"
SHELL = os.environ.get("SHELL")


PROMPT = """
I am running the following command:

{0}

I am running on {1}, release {2}, version {3}.

I'm running into the following error:

=================

{4}

=================

Here is the rest of my terminal window:

=================

{5}

=================

I am running on the following shell: {6}

What command should I run next to fix my error?

Your response should be formatted in JSON as follows:
{{
    "suggested_command": "<this field should ONLY CONTAIN THE COMMAND>",
    "explanation": "..."
}}

The field "suggested_command" in your response should contain ONLY the command the user should run to fix their issue. THIS FIELD SHOULD CONTAIN NOTHING ELSE. The user should be able to take this command and put it in their shell, without any errors.

The field "explanation" should contain an explanation as to why that command would fix the users issue.

Your output should include NOTHING else.
"""



def gen_response(
    prompt: Optional[str] = None,
    api_key: Optional[str] = None,
    model: str = "gpt-3.5-turbo",
    system_prompt: str = "You are a helpful assistant.",
    temperature: float = 0.5,
    max_tokens: int = 256,
    n: int = 1,
):
    openai.api_key = api_key if api_key else os.getenv("OPENAI_API_KEY")
    assert (
        openai.api_key is not None
    ), "API key not found - pass as arg or set environment variable OPENAI_API_KEY"

    messages = [
        {"role": "system", "content": f"{system_prompt}"},
        {"role": "user", "content": prompt},
    ]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        n=n,
    )
    return [
        choice.message["content"].strip() for choice in response["choices"]
    ][0]

if __name__ == "__main__":
    server = libtmux.Server()
    session = server.sessions[0]
    pane = session.attached_pane
    history = '\n'.join(pane.cmd('capture-pane', '-p').stdout)
    with open(ZSH_HISTORY_LOC, 'r') as f:
        # change idx to -2 if running fixit inserts into history
        last_zsh_line = f.readlines()[-2].split(';')[-1]

   # print(last_zsh_line)
    if last_zsh_line in history:
        last_cmd_output = history.split(last_zsh_line)[-1]
       # out_code = int(os.popen('echo $?').read().split('\n')[0])
       # todo make out_code work
    prompt = (PROMPT.format(last_zsh_line, platform.system(), platform.version(), platform.release(), last_cmd_output, "", SHELL))
#    print(prompt)
#    print("\n\n\n\n\n\n")
    resp = json.loads(gen_response(prompt, temperature=0.0, system_prompt="You are an expert at debugging issues on the command line. You will do ONLY WHAT YOU ARE TOLD"))
    print(resp)
    pane.send_keys(resp["suggested_command"], enter=False)
