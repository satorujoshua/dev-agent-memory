import sqlite3
import datetime
import requests

# ANSI colors for Termux
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RED = "\033[91m"

conn = sqlite3.connect('stark_brain.db')
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS ideas 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, 
              timestamp TEXT, 
              tag TEXT, 
              content TEXT)''')
conn.commit()

def remember(tag: str, content: str):
    timestamp = datetime.datetime.now().isoformat()
    c.execute("INSERT INTO ideas (timestamp, tag, content) VALUES (?, ?, ?)",
              (timestamp, tag, content))
    conn.commit()
    print(f"{GREEN}🧠 Remembered under '{tag}'{RESET}")

def recall(tag: str = None):
    if tag:
        c.execute("SELECT id, timestamp, content FROM ideas WHERE tag=? ORDER BY timestamp DESC", (tag,))
    else:
        c.execute("SELECT id, timestamp, tag, content FROM ideas ORDER BY timestamp DESC")
    results = c.fetchall()
    if not results:
        print(f"{YELLOW}No memories found.{RESET}")
        return
    print(f"\n{BOLD}{CYAN}🧠 AGENT MEMORY RECALL ({len(results)} results){RESET}\n")
    for iid, ts, *rest in results:
        if len(rest) == 2:
            t, content = rest
            print(f"[{ts[:16]}]  {BLUE}#{t}{RESET}  (ID:{iid})")
        else:
            content = rest[0]
            print(f"[{ts[:16]}]  (ID:{iid})")
        print(f"   {content}\n")

def search(query: str):
    c.execute("SELECT timestamp, tag, content FROM ideas WHERE content LIKE ? ORDER BY timestamp DESC", 
              (f"%{query}%",))
    results = c.fetchall()
    print(f"\n{BOLD}{YELLOW}🔍 SEARCH RESULTS for '{query}' ({len(results)} found){RESET}\n")
    for ts, tag, content in results:
        print(f"[{ts[:16]}]  {BLUE}#{tag}{RESET} → {content[:120]}...")
    print()

def export_github_ready(filename="agent_memory_github.md"):
    c.execute("SELECT timestamp, tag, content FROM ideas ORDER BY timestamp DESC")
    results = c.fetchall()
    with open(filename, "w", encoding="utf-8") as f:
        f.write("# Agent Memory\n\n")
        f.write("**A simple local-first memory tool for devs and AI agents**\n\n")
        f.write(f"**Total memories:** {len(results)}\n")
        f.write(f"**Last updated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        for ts, tag, content in results:
            f.write(f"## {ts[:16]} — #{tag}\n")
            f.write(f"{content}\n\n")
    print(f"{GREEN}✅ Exported GitHub-ready markdown to {filename}{RESET}")

def main():
    c.execute("SELECT COUNT(*) FROM ideas")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM ideas WHERE date(timestamp) = date('now')")
    today = c.fetchone()[0]
    print(f"{BOLD}{CYAN}🧠 Agent Memory v15{RESET}")
    print(f"Total memories: {total}")
    print(f"Today's motion: {today} logged today\n")

    while True:
        print("1. Remember (log new idea)")
        print("2. Recall (all or by tag)")
        print("3. Search")
        print("4. Export GitHub-ready Markdown")
        print("5. Exit")
        choice = input(f"\n{BLUE}Choose (1-5): {RESET}").strip()

        if choice == "1":
            tag = input("Tag: ").strip()
            if not tag:
                print(f"{YELLOW}Tag is required.{RESET}")
                continue
            print("Content (press Enter on blank line to finish):")
            lines = []
            while True:
                line = input()
                if line == "":
                    break
                lines.append(line)
            content = "\n".join(lines)
            if content:
                remember(tag, content)
            else:
                print(f"{YELLOW}No content entered.{RESET}")
        elif choice == "2":
            tag = input("Tag (leave empty for all): ").strip()
            recall(tag if tag else None)
        elif choice == "3":
            query = input("Search keyword: ").strip()
            if query:
                search(query)
        elif choice == "4":
            export_github_ready()
        elif choice == "5":
            print(f"{GREEN}👋 Goodbye!{RESET}")
            break
        else:
            print(f"{YELLOW}Invalid choice.{RESET}")

if __name__ == "__main__":
    main()
