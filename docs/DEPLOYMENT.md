# Deployment guide

MatEIS is a Python web app (NiceGUI on FastAPI). It needs a host that runs a Python process with WebSocket support. **Streamlit Community Cloud will not work.** Use one of the options below.

## Step 1 – Put the code on GitHub

```bash
cd MatEIS
git init -b main
git add .
git commit -m "MatEIS: materials engineering interactive suite"
git remote add origin https://github.com/<your-user>/MatEIS.git
git push -u origin main
```
Create the empty repository on GitHub first (leave *README*, *.gitignore* and *license* unticked). If `git push` asks for a password, use the browser sign-in or a Personal Access Token. A green tick appears on the **Actions** tab when the CI run (ruff + pytest) passes.

## Step 2A – Render (free, recommended)

1. Sign in at <https://render.com> with GitHub.
2. **New → Web Service**, pick the `MatEIS` repository.
3. Runtime: **Docker** (it finds the `Dockerfile`). Plan: **Free**. Render reads `render.yaml` if you use *Blueprint* instead.
4. Add the environment variable `MATEIS_STORAGE_SECRET` with any long random string.
5. Deploy. After a few minutes you get `https://mateis-xxxx.onrender.com`.

The free plan sleeps after inactivity (first load takes about 30 s) and its disk is temporary: materials you add online disappear on restart, while the original data returns from the JSON seed. Open the site a minute before your demo.

## Step 2B – Hugging Face Spaces (free, no sleep for public Spaces)

1. <https://huggingface.co/new-space> → **SDK: Docker**, visibility public.
2. Upload the project files (or connect the GitHub repository).
3. Add `PORT=7860` as a Space variable, and put `app_port: 7860` in the Space `README.md` front matter.
4. The Space builds from the `Dockerfile` and serves the app.

## Step 2C – Run locally for the demo (always works)

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows   (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
python main.py                   # open http://localhost:8080
```
Keep this as your backup if the Wi-Fi fails during the presentation.

## Environment variables

| Variable | Purpose | Default |
|---|---|---|
| `PORT` | Port to listen on | 8080 |
| `MATEIS_DB_PATH` | SQLite file location | `data/mateis.db` |
| `MATEIS_STORAGE_SECRET` | Signs the browser storage (dark-mode preference) | a dev value; set your own online |
