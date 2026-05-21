# Push to GitHub (NISARGAMIN28)

**Do not put your GitHub password in terminal commands.** GitHub disabled password push in 2021.

**Change your GitHub password now** — it was shared in chat.

## Steps

### 1. Create a Personal Access Token

1. Log in as **NISARGAMIN28**
2. [github.com/settings/tokens](https://github.com/settings/tokens) → **Generate new token (classic)**
3. Scope: **repo**
4. Copy the token (starts with `ghp_`)

### 2. Create empty repo on GitHub

- Name: `fastapi-rag-agent` (or any name)
- Public
- No README from GitHub

### 3. Push from your Mac

```bash
cd /Users/shaikmohammadusman/Desktop/William

git init
git add .
git status   # .env must NOT appear

git commit -m "FastAPI docs RAG with eval harness and MCP server"

git branch -M main
git remote add origin https://github.com/NISARGAMIN28/fastapi-rag-agent.git

# When prompted: username = NISARGAMIN28, password = paste ghp_ token (not account password)
git push -u origin main
```

### 4. Share with Ovidius

Send: `https://github.com/NISARGAMIN28/fastapi-rag-agent`

Or invite `tech@ovidius.ai` if private.
