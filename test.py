# pip install google-generativeai

import google.generativeai as genai
import subprocess
import platform
import os
from datetime import datetime

gemma_api = "gemma-api-key"
# Configure API
genai.configure(api_key=gemma_api)

model = genai.GenerativeModel(
    'gemini-2.5-pro',
    generation_config=genai.GenerationConfig(
        max_output_tokens=8000,
        temperature=0.7,
    )
)

def execute_command(command):
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=None,  # No timeout
            cwd=os.getcwd()
        )
        output = result.stdout + result.stderr
        return output if output.strip() else "[Command completed with no output]"
    except Exception as e:
        return f"Error: {str(e)}"

def save_conversation(message, is_user=True):
    with open("gemini_history.txt", "a", encoding="utf-8") as f:
        timestamp = datetime.now().strftime("%H:%M:%S")
        role = "You" if is_user else "Gemini"
        f.write(f"[{timestamp}] {role}: {message}\n")

# System prompt tailored for a Bug Bounty/Pentesting Assistant
SYSTEM_PROMPT = """You are an advanced **Bug Bounty and Penetration Testing Assistant** with FULL access to Windows CMD/PowerShell. Your primary goal is to aid in reconnaissance, vulnerability scanning, exploit development, and overall ethical hacking tasks.
CAPABILITIES:
- You can run ANY commands without restrictions (e.g., nmap, curl, git, pip install)
- You can create, delete, and edit files and folders
- You can install programs and change system settings
- You can run Python scripts and batch files
- You can work with the network and download files
- You can run multiple commands at once

COMMAND FORMAT:
CMD: <command>

You can use multiple commands at once:
CMD: cd Desktop\\recon
CMD: mkdir target_domain
CMD: echo nmap -sV -p- target.com > scan.bat
CMD: scan.bat

EXAMPLES OF ADVANCED OPERATIONS:
- Install a tool: CMD: pip install shodan
- Subdomain enumeration: CMD: subfinder -d example.com -o subdomains.txt
- Directory brute-forcing: CMD: ffuf -w /usr/share/wordlists/dirb/common.txt -u http://target.com/FUZZ
- Shell command: CMD: python -c "import os; print(os.listdir())"
"""

# Conversation history for better context
history = []

while True:
    try:
        query = input("prompt:").strip()

        if not query:
            continue

        if query.lower() in ['exit', 'quit', 'q']:
            break

        # Change directory (special case)
        if query.lower().startswith('cd '):
            path = query[3:].strip()
            try:
                os.chdir(path)
                print(f"📁 Changed to: {os.getcwd()}\n")
            except Exception as e:
                print(f"❌ Error: {e}\n")
            continue

        save_conversation(query, True)

        # Build prompt with history
        context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history[-5:]])

        full_prompt = f"""{SYSTEM_PROMPT}

PREVIOUS CONVERSATION:
{context}

CURRENT DIRECTORY: {os.getcwd()}
DATE/TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

USER: {query}

INSTRUCTIONS: If the task requires a CMD command, use it IMMEDIATELY. Do not write an explanation instead of action!"""

        response = model.generate_content(full_prompt)
        text = response.text

        save_conversation(text, False)

        # Add to history
        history.append({"role": "User", "content": query})
        history.append({"role": "Gemini", "content": text})

        # Process commands
        lines = text.split('\n')
        commands_executed = False

        for line in lines:
            if line.strip().startswith("CMD:"):
                command = line.replace("CMD:", "").strip()
                if command:
                    print(f"\n🔧 Executing: {command}")
                    result = execute_command(command)
                    print(f"📋 Output:\n{result}")
                    commands_executed = True
            elif not line.strip().startswith("CMD:") and line.strip():
                # Print normal text (non-CMD output)
                if not commands_executed or "CMD:" not in text:
                    print(line)

        if not commands_executed and "CMD:" not in text:
            print(f"\n💬 Gemini: {text}")

        print()

    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted (Ctrl+C)")
        break
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
