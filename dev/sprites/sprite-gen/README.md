# sprite-gen

Generates the rider sprite sheets with the OpenAI Images API.

## Setup (once)

1. Install Python 3.9 or later, then: `pip install requests`
2. `refs/character-reference.png` (the 4 photos on one board) is already there. Add or remove photos in `refs/` if you want; every image in that folder goes with every request.
3. Set your key in the terminal:
   - macOS / Linux: `export OPENAI_API_KEY="sk-..."`
   - Windows PowerShell: `$env:OPENAI_API_KEY="sk-..."`

## Run

```
python gen_sprites.py list            # the 9 images and what they use
python gen_sprites.py charref         # step 1: pixel-art character model sheet, from the photos only
```

Pick the variant you like in `output/`, copy it to `approved/charref.png`, then:

```
python gen_sprites.py sheet1          # step 2: sheet 1, photos + approved character sheet
```

Copy the variant you keep to `approved/sheet1.png`, then:

```
python gen_sprites.py all             # sheets 2 to 6 + the 2 illustrations, using the photos + approved/charref.png + approved/sheet1.png
python gen_sprites.py sheet3 --n 3    # redo one sheet with 3 variants
```

Options: `--n 2` (variants per sheet), `--quality high|medium|low`, `--model gpt-image-2` (or `gpt-image-1`), `--dry-run` (checks files, sends nothing).

The prompts live in `sheets.json`: edit them there.

Every file lands in `output/` with a timestamp; nothing gets overwritten. Send me the variants you keep.
