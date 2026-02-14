import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
sys.path.insert(0, str(Path(__file__).parent / "server"))
from agent_groq import LibraryAgent
from database import db

load_dotenv()

class TerminalUI:
    """Simple terminal interface"""
    
    def __init__(self):
        self.agent = None
        self.session_id = None
    
    def clear_screen(self):
        """Clear terminal"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self):
        """Show header"""
        print("\n" + "="*60)
        print(" LIBRARY DESK AGENT".center(60))
        print("="*60)
    
    def print_menu(self):
        """Show commands"""
        print("\n Commands:")
        print("  • Type your question")
        print("  • 'sessions' - List all sessions")
        print("  • 'history' - Show current session history")
        print("  • 'switch <number>' - Change session")
        print("  • 'new' - New session")
        print("  • 'clear' - Clear screen")
        print("  • 'quit' - Exit\n")
    
    def show_sessions(self):
        sessions = db.get_all_sessions()
        
        if not sessions:
            print("\n  No saved sessions\n")
            return sessions
        
        # Get message counts
        conn = db.get_connection()
        cursor = conn.cursor()
        
        print("\n Available Sessions:")
        for i, session in enumerate(sessions, 1):
            # Count messages for this session
            cursor.execute(
                "SELECT COUNT(*) as count FROM messages WHERE session_id = ?",
                (session,)
            )
            msg_count = cursor.fetchone()['count']
            
            marker = "✓" if session == self.session_id else " "
            print(f"  {marker} {i}. {session}  {msg_count} msg")
        
        conn.close()
        print()
        return sessions
    
    def select_session(self):
        sessions = db.get_all_sessions()
        
        if sessions:
            print(f"\n✓ Found {len(sessions)} session(s)")
            self.show_sessions()
            
            choice = input("Select session number (or Enter for new): ").strip()
            
            if choice.isdigit() and 1 <= int(choice) <= len(sessions):
                return sessions[int(choice) - 1]
        
        # Create new session
        return f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    def init_agent(self):
        """Initialize agent"""
        self.session_id = self.select_session()
        print(f"\n Loading: {self.session_id}")
        
        self.agent = LibraryAgent(session_id=self.session_id)
        self.agent.load_history()
        
        # Show previous messages if any
        history = self.agent.get_history()
        if history:
            print(f"\n Previous Messages ({len(history)}):")
            print("-" * 60)
            for msg in history:
                role = " You" if msg['role'] == 'user' else " Agent"
                content = msg['content']
                # Truncate long messages
                if len(content) > 80:
                    content = content[:80] + "..."
                print(f"{role}: {content}")
            print("-" * 60)
        
        print("✓ Ready!\n")
    
    def chat_loop(self):
        while True:
            try:
                # Get input
                user_input = input(f" You: ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                cmd = user_input.lower()
                
                # Exit
                if cmd in ['quit', 'exit', 'q']:
                    print("\n Goodbye!\n")
                    break
                
                # Clear
                elif cmd == 'clear':
                    self.clear_screen()
                    self.print_header()
                    self.print_menu()
                    continue
                
                # Sessions
                elif cmd == 'sessions':
                    self.show_sessions()
                    continue
                
                # History
                elif cmd == 'history':
                    history = self.agent.get_history()
                    if not history:
                        print("\n No messages in this session yet.\n")
                    else:
                        print(f"\n Session History ({len(history)} messages):")
                        print("=" * 60)
                        for msg in history:
                            role = " You" if msg['role'] == 'user' else " Agent"
                            print(f"\n{role}:")
                            print(msg['content'])
                        print("=" * 60 + "\n")
                    continue
                
                # Switch
                elif cmd.startswith('switch '):
                    num = cmd.split()[1]
                    if num.isdigit():
                        sessions = db.get_all_sessions()
                        idx = int(num) - 1
                        if 0 <= idx < len(sessions):
                            self.session_id = sessions[idx]
                            self.agent = LibraryAgent(session_id=self.session_id)
                            self.agent.load_history()
                            print(f"\n✓ Switched to: {self.session_id}\n")
                    continue
                
                # New session
                elif cmd == 'new':
                    self.session_id = f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                    self.agent = LibraryAgent(session_id=self.session_id)
                    print(f"\n✓ New session: {self.session_id}\n")
                    continue
                
                # Send to agent
                print("\n Agent: ", end="", flush=True)
                response = self.agent.chat(user_input)
                print(response + "\n")
                
            except KeyboardInterrupt:
                print("\n\nInterrupted. Goodbye!\n")
                break
            
            except Exception as e:
                print(f"\n Error: {e}\n")
    
    def run(self):
        
        if not os.getenv("GROQ_API_KEY"):
            print("\n GROQ_API_KEY not found!")
            print("   Add it to .env file")
            print("   Get FREE key: https://console.groq.com/keys\n")
            return
        
        db.init_database()
        self.print_header()
        self.init_agent()
        self.print_menu()
        self.chat_loop()

if __name__ == "__main__":
    ui = TerminalUI()
    ui.run()