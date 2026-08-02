# 🎬 Manim Cloud Render Farm

Render Manim animations on **three free cloud services** — all included in this repo.
Your phone stays cool: the cloud downloads the libraries, does the rendering, and you just download the finished MP4.

```
┌─────────────┐   push / open   ┌──────────────────┐   finished MP4
│  Your phone │ ──────────────► │ FREE cloud (3x!)  │ ──────────────►  you
└─────────────┘                 └──────────────────┘
   (no heavy work)              GitHub Actions + Colab + Kaggle
```

---

## 📁 What's in here

| File | What it does |
|---|---|
| `scenes/example.py` | Sample animation — copy it to make your own |
| `.github/workflows/render.yml` | Auto-renders `scenes/*.py` on GitHub's free servers |
| `Manim_Render.ipynb` | One notebook that works on **both** Colab and Kaggle |
| `push_to_cloud.sh` | Phone shortcut: push a scene file → cloud renders it |

---

## 🚀 Provider 1 — GitHub Actions (unlimited, automatic)

**Step 1 — create the repo (phone browser, 1 minute):**
1. Sign up at https://github.com/signup (free, no credit card needed)
2. Click **New repository** → name it `manim-cloud` → **Public** → Create
3. Do NOT tick "Add a README" (this folder already has one)

**Step 2 — connect + push (Termux on your phone):**
```bash
cd ~/manim-cloud
git remote add origin https://github.com/YOUR_USERNAME/manim-cloud.git
git push -u origin main
```
Git will ask for your GitHub **username** and a **password** — for the password use a
**Personal Access Token** (not your account password):
GitHub → Settings → Developer settings → Personal access tokens →
*Fine-grained tokens* → Generate new → repo permission → copy token.

**Step 3 — render (phone browser):**
- Put your animation in `scenes/` (edit `scenes/example.py`), then run:
  ```bash
  ./push_to_cloud.sh scenes/example.py
  ```
  or just `git add scenes && git commit -m "new scene" && git push`
- Every push auto-starts the **Render Manim** workflow.
- Open the repo → **Actions** tab → click the run → wait 2–5 min →
  scroll to **Artifacts** → download **manim-videos** → your MP4s inside.

💡 You can also click **"Run workflow"** button in the Actions tab anytime.

---

## 🚀 Provider 2 — Google Colab (free GPU cloud)

1. Open https://colab.research.google.com → **Upload** → choose `Manim_Render.ipynb`
   (or upload this whole folder to Google Drive and open the .ipynb from Drive)
2. **Runtime → Run all**
3. Cell 2 has the example scene — edit it to make your animation
4. The last cell auto-downloads your MP4 to your phone

---

## 🚀 Provider 3 — Kaggle (free GPU, 30 hrs/week)

1. Sign up at https://kaggle.com (free, no card)
2. **Create → Notebook → Import → Upload Notebook** → choose `Manim_Render.ipynb`
3. ⚠️ Important: click **Settings** (right panel) → turn **ON** the **Internet** switch
4. **Run All** — same cells as Colab, same scene code
5. When done, the MP4 is in the left file panel under `media/` → tap the ▶ to download

---

## 📝 Tips

- **Quality:** edit the notebook's `QUALITY` line: `-ql` fast draft · `-qm` medium · `-qh` full HD
- **Math equations (MathTex):** need LaTeX. On GitHub Actions uncomment the LaTeX step in
  `render.yml`; in Colab add `!apt-get install -y texlive-latex-extra` before cell 3.
- **GitHub private repos** get 2,000 free minutes/month; **public repos are unlimited**.
- All three services are free **without a credit card**.
