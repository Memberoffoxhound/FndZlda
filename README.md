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

## Install on Windows (easiest)

Download the EXE and double-click it. It installs a private portable Python for you. No PATH, no admin.

**[Download FndZlda.exe](https://github.com/Memberoffoxhound/FndZlda/releases/latest/download/FndZlda.exe)**  
(also on [Releases](https://github.com/Memberoffoxhound/FndZlda/releases/latest))

1. Save **`FndZlda.exe`** somewhere easy (Desktop is fine).
2. Double-click it. Windows may say “Windows protected your PC” — click **More info** → **Run anyway**.
3. First run may take a minute (“It's dangerous to go alone! Setting up…”).
4. Type **1**, **2**, or **3** and press Enter.

Leave the black window open.

### Windows, if you already have Python

Unzip the repo and double-click **`install.bat`**. If Python is missing it opens python.org and tells you to check **Add python.exe to PATH**.

---

## Install on Linux

```bash
git clone https://github.com/Memberoffoxhound/FndZlda.git
cd FndZlda
chmod +x install.sh
./install.sh
```

That copies the app to `~/.local/share/fndzlda` and puts `fndzlda` on `~/.local/bin`. Or just run it in place:

```bash
python3 -m fndzlda
```

On this machine:

```bash
cd /home/deck/FndZlda && python3 -m fndzlda
```

---

## The question it asks

```
  [1] Console only          ($519.99)
  [2] Zelda Pro Controller  ($99.99)
  [3] Both
```

Type the number. Press Enter.

---

## If it finds one

- Navi shouts **HEY! LISTEN!!!**
- The terminal prints **HIT**
- It beeps
- Your default browser opens the store cart, then checkout
- You still click the final **Place order** / **Pay** button. That is you, not the bot.

If nothing is in stock, you get a disappointed Zelda quote instead.

It will not keep opening the same store over and over. To force it again, start with `--again`.

---

## Extra buttons (optional)

Most people can ignore this. Double-click **FndZlda.exe** (Windows) or run `./install.sh` (Linux) is enough.

| You type this | What it does |
|---|---|
| `--want both` | Skip the 1/2/3 question; hunt both |
| `--want console` | Console only |
| `--want controller` | Pro Controller only |
| `--once` | Check once, then quit (good for a test) |
| `--dry-run` | Print the cart links but **do not** open the browser |

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
