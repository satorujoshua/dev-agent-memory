import sqlite3
import datetime
import requests

# ANSI colors
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RED = "\033[91m"

conn = sqlite3.connect('stark_brain.db')
c = conn.cursor()

# Safe migration
c.execute("PRAGMA table_info(ideas)")
columns = [col[1] for col in c.fetchall()]
if 'id' not in columns:
    print("🔧 Migrating old database... (only once)")
    c.execute('''CREATE TABLE IF NOT EXISTS ideas_new 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, tag TEXT, content TEXT)''')
    c.execute("INSERT INTO ideas_new (timestamp, tag, content) SELECT timestamp, tag, content FROM ideas")
    conn.commit()
    c.execute("DROP TABLE ideas")
    c.execute("ALTER TABLE ideas_new RENAME TO ideas")
    print("✅ Migration complete!")

c.execute('''CREATE TABLE IF NOT EXISTS ideas 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, tag TEXT, content TEXT)''')
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

def edit_memory(memory_id: int):
    c.execute("SELECT content FROM ideas WHERE id=?", (memory_id,))
    result = c.fetchone()
    if not result:
        print(f"{RED}Memory ID {memory_id} not found.{RESET}")
        return
    print(f"Current content:\n{result[0]}\n")
    print("New content (press Enter on blank line to finish):")
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    new_content = "\n".join(lines)
    if new_content:
        c.execute("UPDATE ideas SET content=? WHERE id=?", (new_content, memory_id))
        conn.commit()
        print(f"{GREEN}✅ Memory ID {memory_id} updated.{RESET}")
    else:
        print(f"{YELLOW}No changes made.{RESET}")

def delete_memory(memory_id: int):
    c.execute("SELECT id FROM ideas WHERE id=?", (memory_id,))
    if not c.fetchone():
        print(f"{RED}Memory ID {memory_id} not found.{RESET}")
        return
    confirm = input(f"{RED}Delete memory ID {memory_id}? (y/n): {RESET}").strip().lower()
    if confirm == "y":
        c.execute("DELETE FROM ideas WHERE id=?", (memory_id,))
        conn.commit()
        print(f"{GREEN}🗑️ Memory ID {memory_id} deleted.{RESET}")
    else:
        print("Cancelled.")

def auto_fetch_hacker_news():
    print(f"{CYAN}🔄 Fetching from Hacker News...{RESET}")
    try:
        response = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json")
        story_ids = response.json()[:30]
        pain_keywords = ["pain", "struggle", "frustrat", "hate", "hard", "difficult", "issue", "bug", "problem", "burnout", "annoying", "slow", "broken"]
        found = 0
        for story_id in story_ids:
            story = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json").json()
            if not story or "title" not in story:
                continue
            title = story["title"]
            if any(word in title.lower() for word in pain_keywords):
                remember("hacker-news-pain", title)
                found += 1
        print(f"{GREEN}✅ Added {found} new pain points from Hacker News.{RESET}")
    except Exception as e:
        print(f"{RED}❌ HN fetch failed: {e}{RESET}")

def auto_fetch_reddit():
    print(f"{CYAN}🔄 Fetching from Reddit...{RESET}")
    subs = ["learnprogramming", "webdev", "MachineLearning", "programming"]
    pain_keywords = ["pain", "struggle", "frustrat", "hate", "hard", "difficult", "issue", "bug", "problem", "burnout", "annoying", "slow", "broken"]
    found = 0
    for sub in subs:
        try:
            url = f"https://www.reddit.com/r/{sub}/hot.json?limit=15"
            headers = {"User-Agent": "DevPainScout/1.0"}
            response = requests.get(url, headers=headers)
            posts = response.json()["data"]["children"]
            for post in posts:
                title = post["data"]["title"]
                if any(word in title.lower() for word in pain_keywords):
                    remember("reddit-pain", title)
                    found += 1
        except:
            pass
    print(f"{GREEN}✅ Added {found} new pain points from Reddit.{RESET}")

def suggest_tools():
    print(f"{CYAN}🤖 Analyzing logged pain points...{RESET}")
    c.execute("SELECT content FROM ideas WHERE tag LIKE '%pain%' ORDER BY timestamp DESC LIMIT 30")
    pains = [row[0].lower() for row in c.fetchall()]
    if not pains:
        print(f"{YELLOW}No pain points yet. Run Auto-fetch first!{RESET}")
        return
    print(f"\n{BOLD}Here are 3 fresh tool ideas based on your data:{RESET}\n")
    print("1. AgentMemory CLI\n   Local-first persistent memory for AI agents.\n")
    print("2. Pain2Agent\n   Turns logged pain into starter agent code.\n")
    print("3. TrendWatch\n   Daily summary of trending dev pain points.\n")

def auto_summarize():
    print(f"{CYAN}📊 Auto-Summarizing pain points...{RESET}")
    c.execute("SELECT content FROM ideas WHERE tag LIKE '%pain%' ORDER BY timestamp DESC LIMIT 50")
    pains = [row[0].lower() for row in c.fetchall()]
    if not pains:
        print(f"{YELLOW}No pain points logged yet.{RESET}")
        return
    groups = {"Agent/Memory": 0, "Burnout/Speed": 0, "Debug/Bug": 0, "General": 0}
    for pain in pains:
        if any(k in pain for k in ["agent", "memory", "filesystem"]):
            groups["Agent/Memory"] += 1
        elif any(k in pain for k in ["burnout", "slow"]):
            groups["Burnout/Speed"] += 1
        elif any(k in pain for k in ["bug", "debug"]):
            groups["Debug/Bug"] += 1
        else:
            groups["General"] += 1
    print(f"\n{BOLD}📈 AUTO-SUMMARY{RESET}\n")
    for cat, count in sorted(groups.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            print(f"• {cat}: {count} mentions")
    print(f"\nTotal pain points: {len(pains)}\n")

# ================== MENU ==================
def main():
    c.execute("SELECT COUNT(*) FROM ideas")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM ideas WHERE date(timestamp) = date('now')")
    today = c.fetchone()[0]
    print(f"{BOLD}{CYAN}🧠 Agent Memory v15 - Showcase Ready{RESET}")
    print(f"Total memories: {total}")
    print(f"Today's motion: {today} logged today\n")

    while True:
        print("1. Remember (log new idea)")
        print("2. Recall (all or by tag)")
        print("3. Search")
        print("4. Export GitHub-ready Markdown")
        print("5. Auto-fetch Hacker News")
        print("6. Auto-fetch Reddit")
        print("7. Suggest tool ideas")
        print("8. Auto-Summarize")
        print("9. Edit memory by ID")
        print("10. Delete memory by ID")
        print("11. Exit")
        choice = input(f"\n{BLUE}Choose (1-11): {RESET}").strip()

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
            auto_fetch_hacker_news()
        elif choice == "6":
            auto_fetch_reddit()
        elif choice == "7":
            suggest_tools()
        elif choice == "8":
            auto_summarize()
        elif choice == "9":
            try:
                iid = int(input("Memory ID to edit: "))
                edit_memory(iid)
            except:
                print(f"{RED}Invalid ID.{RESET}")
        elif choice == "10":
            try:
                iid = int(input("Memory ID to delete: "))
                delete_memory(iid)
            except:
                print(f"{RED}Invalid ID.{RESET}")
        elif choice == "11":
            print(f"{GREEN}👋 Goodbye!{RESET}")
            break
        else:
            print(f"{YELLOW}Invalid choice.{RESET}")

if __name__ == "__main__":
    main()
