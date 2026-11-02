# sprite-gen3

Proto 3 sprite jobs. Same tool as `../sprite-gen` (OpenAI Images API), new prompts.
The API key stays local, never in the repo. The reference photos are not versioned: put them in `refs/`.

## Step 1 : the two references

```
export OPENAI_API_KEY="sk-..."
pip install requests
python gen_sprites.py charref --n 3     # Marine, model sheet v2 (photos only)
```
Copy the variant you keep to `approved/charref.png`, then:
```
python gen_sprites.py world --n 3       # style board for everything that is not Marine (approved charref only, no photos)
```
Copy the variant you keep to `approved/world.png`.

`--dry-run` lists what would be sent without calling the API.
