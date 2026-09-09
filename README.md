# FndZlda

A little terminal app that watches **US stores** for the **Nintendo Switch 2 Zelda 40th Anniversary** console and/or the matching **Pro Controller**. When one actually goes on sale, it opens **your normal browser**, tries to **add it to the cart**, then jumps to **checkout**.

United States only. Nintendo, Best Buy, Target, Walmart, GameStop, Amazon.

It greets you with the old **Ocarina of Time** logo in the terminal. That is on purpose.

---

## What you do

1. Start it.
2. It asks: **console**, **Zelda Pro Controller**, or **both**.
3. Leave the window open.
4. When it finds one, your browser pops up. Finish paying like a normal checkout.

Be already signed in to the store websites (Best Buy, Target, Walmart, etc.) in that same browser. The app cannot type your password.

---

## Install on Windows (the easy way)

You only need Python. Nothing else to pip-install.

1. Go to [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Download Python and run the installer.
3. **Check the box that says “Add python.exe to PATH.”** Then click Install.
4. Open [https://github.com/Memberoffoxhound/FndZlda](https://github.com/Memberoffoxhound/FndZlda)
5. Click the green **Code** button → **Download ZIP**
6. Unzip the folder (right-click → Extract All). Open the unzipped `FndZlda` folder.
7. Double-click **`fndzlda.cmd`**
8. A black window appears with the Zelda logo. Type **1**, **2**, or **3** and press Enter.

Leave that window running. Minimize it if you want. Close it only when you are done hunting.

If Windows says “Python was not found,” you skipped the PATH checkbox. Reinstall Python and check that box.

---

## Install on Linux

Open a terminal:

```bash
git clone https://github.com/Memberoffoxhound/FndZlda.git
cd FndZlda
python3 -m fndzlda
```

No extra packages. If `git` is missing: download the ZIP from GitHub, unzip, then:

```bash
cd ~/Downloads/FndZlda-main
python3 -m fndzlda
```

On this machine the folder is already here:

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

- The terminal prints **HIT**
- It beeps
- Your default browser opens the store cart, then checkout
- You still click the final **Place order** / **Pay** button. That is you, not the bot.

It will not keep opening the same store over and over. To force it again, start with `--again`.

---

## Extra buttons (optional)

Most people can ignore this. Double-click `fndzlda.cmd` (Windows) or run `python3 -m fndzlda` (Linux) is enough.

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
