# FndZlda

A little terminal app that watches **US stores** for the **Nintendo Switch 2 Zelda 40th Anniversary** console and/or the matching **Pro Controller**. When one actually goes on sale, it opens **your normal browser**, tries to **add it to the cart**, then jumps to **checkout**.

United States only. Nintendo, Best Buy, Target, Walmart, GameStop, Amazon.

It opens in a NES cave: the old man says **IT'S DANGEROUS TO GO ALONE! TAKE THIS!**, hands you the **Master Sword**, then starts scanning. A miss quotes Zelda. A hit is Navi: **HEY! LISTEN!!!**

---

## What you do

1. Start it.
2. It asks: **console**, **Zelda Pro Controller**, or **both**.
3. Leave the window open.
4. When it finds one, your browser pops up. Finish paying like a normal checkout.

Be already signed in to the store websites (Best Buy, Target, Walmart, etc.) in that same browser. The app cannot type your password.

---

## Install on Windows

Download the EXE and double-click it. It installs a private portable Python for you. No PATH, no admin.

**[Download FndZlda.exe](https://github.com/Memberoffoxhound/FndZlda/releases/latest/download/FndZlda.exe)**  
(also on [Releases](https://github.com/Memberoffoxhound/FndZlda/releases/latest))

1. Save **`FndZlda.exe`** somewhere easy (Desktop is fine).
2. Double-click it. Windows may say “Windows protected your PC” — click **More info** → **Run anyway**.
3. First run may take a minute (“It's dangerous to go alone! Setting up…”). That download *is* Python.
4. Type **1**, **2**, or **3** and press Enter.

Leave the black window open.

### Windows, from the repo (`install.bat`)

Unzip or clone the repo and double-click **`install.bat`**. If Python 3.10+ is missing it now **downloads portable Python itself** into `%LOCALAPPDATA%\FndZlda\python` (curl, then PowerShell). If that fails it tries `winget` for Python 3.12. Only after that does it open python.org.

---

## Install on Linux or macOS

Same hunter, same installer. You need **Python 3.10+** (`python3`). No extra packages.

- **Linux:** `sudo apt install python3` (Debian / Ubuntu) or `sudo pacman -S python` (Arch / SteamOS)
- **macOS:** [python.org](https://www.python.org/downloads/) or `brew install python`

Then:

```bash
git clone https://github.com/Memberoffoxhound/FndZlda.git
cd FndZlda
chmod +x install.sh
./install.sh
```

That copies the app to `~/.local/share/fndzlda` and puts `fndzlda` on `~/.local/bin`. Or skip the installer and run it from the repo:

```bash
python3 -m fndzlda
```

On start it checks GitHub `main` and pulls the latest commit, then restarts if it updated. Use `--no-update` to skip.

---

## The question it asks

```
  [1] Console only          ($519.99)
  [2] Zelda Pro Controller  ($99.99)
  [3] Both
```

Type the number. Press Enter.

Then it asks which stores. Type names separated by commas. Typos are fine.

```
Which US stores should I check?

Type the names, separated by commas. Spelling can be messy.
Stores: Nintendo, Best Buy, Target, Walmart, GameStop, Amazon
Type all if you want every store.

Examples:  walmart, target
           best buy, gamestop, amazon
           all
```

---

## If it finds one

- The terminal prints **HIT**
- It beeps
- Your default browser opens the store cart, then checkout
- You still click the final **Place order** / **Pay** button. That is you, not the bot.

Then it waits **two minutes** and scans every chosen store again. It will **not** add the same listing to the cart a second time (Best Buy’s add-to-cart link stacks quantity). Use `--again` if you really want another add. It keeps going until you quit (**Ctrl+C**).

---

## Extra buttons (optional)

Most people can ignore this. Double-click **FndZlda.exe** (Windows) or run `./install.sh` (Linux or macOS) is enough.

| You type this | What it does |
|---|---|
| `--want both` | Skip the 1/2/3 question; hunt both |
| `--want console` | Console only |
| `--want controller` | Pro Controller only |
| `--shops all` | Skip the store question; check every US shop |
| `--shops "walmart, target"` | Only those stores (typos ok) |
| `--once` | Check once, then quit (good for a test) |
| `--dry-run` | Print the cart links but **do not** open the browser |
| `--again` | If the same listing is still in stock, open the cart again (can stack quantity) |
| `--no-update` | Do not check GitHub for a newer commit |

Example test (no shopping):

```bash
python3 -m fndzlda --want both --once --dry-run
```

---

## US only

Pages, prices, and checkout links are **US retail**. It will not hunt Canada, UK, Japan, etc.

---

## It is picky on purpose

It ignores PowerA knockoffs, carrying cases, OLED (that’s Switch 1), and scalper prices. It wants the real Zelda 40th Switch 2 hardware.

---

## Stop

Click the terminal and press **Ctrl+C**, or just close the window.
