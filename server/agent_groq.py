"""
Library Desk Agent - Simple & Clean
"""

import os
import re
import json
from pathlib import Path
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from tools import TOOLS
from database import db

class LibraryAgent:

    def __init__(self, session_id="default"):
        self.session_id = session_id
        self.history = []
        self.prompt = self._load_prompt()

        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0,
            groq_api_key=os.getenv("GROQ_API_KEY"),
            max_tokens=100
        )

    def _load_prompt(self):
        """Load system prompt from file"""
        prompt_file = Path(__file__).parent.parent / "prompts" / "system_prompt.md"

        if prompt_file.exists():
            return prompt_file.read_text(encoding='utf-8')

        return "You are a Library Agent. Use tools when needed."

    def chat(self, msg):
        try:
            db.log_message(self.session_id, "user", msg)

            ai = self.llm.invoke([
                SystemMessage(content=self.prompt),
                *self.history[-6:],
                HumanMessage(content=msg)
            ]).content.strip()

            response = self._exec_tool(ai) if "TOOL:" in ai.upper() else ai

            self.history += [HumanMessage(content=msg), AIMessage(content=response)]
            if len(self.history) > 10:
                self.history = self.history[-10:]

            db.log_message(self.session_id, "assistant", response)
            return response

        except Exception as e:
            return f"Error: {e}"

    def _exec_tool(self, ai_text):
        """Execute ALL tools found in AI response"""
        try:
            # Find ALL matches (not just first)
            matches = list(re.finditer(r'TOOL:\s*(\w+)\((.*?)\)', ai_text, re.DOTALL))
            
            if not matches:
                return ai_text
            
            results = []
            
            for match in matches:
                tool_name = match.group(1)
                args_str = match.group(2).strip()
                
                if tool_name not in TOOLS:
                    results.append(f"Unknown tool: {tool_name}")
                    continue
                
                tool_func = TOOLS[tool_name]['function']
                
                args = {}
                if args_str:
                    for m in re.finditer(r'(\w+)=(?:"([^"]*)"|\'([^\']*)\'|(\[[^\]]*\])|([^,)]+))', args_str):
                        k = m.group(1)
                        v = (m.group(2) or m.group(3) or m.group(4) or m.group(5)).strip()
                        
                        if k == "items":
                            try:
                                args[k] = json.loads(v)
                            except:
                                args[k] = v
                        elif v.isdigit():
                            args[k] = int(v)
                        elif '.' in v and v.replace('.','').isdigit():
                            args[k] = float(v)
                        else:
                            args[k] = v
                
                # Execute tool
                result = tool_func(**args) if args else tool_func()
                results.append(result)
            
            # Combine all results
            return "\n\n".join(results)
        
        except Exception as e:
            return f"Error: {e}"
    def load_history(self):
        msgs = db.get_session_history(self.session_id)[-10:]
        self.history = [
            HumanMessage(content=m['content']) if m['role'] == 'user' 
            else AIMessage(content=m['content'])
            for m in msgs
        ]

    def get_history(self):
        return [
            {"role": "user" if isinstance(m, HumanMessage) else "assistant", "content": m.content} 
            for m in self.history
        ]