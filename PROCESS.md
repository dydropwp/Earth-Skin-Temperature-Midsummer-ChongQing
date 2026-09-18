# PROCESS.md — how I used AI

## Tools and what for

I used DeepSeek throughout this assignment for most of it, in a back-and-forth loop. Concretely: the data source was a website the professor gave us, and I used DeepSeek to help me write a `fetch.py` script that pulled the data from that site and saved it locally, so I could parse it offline. I also used it to scaffold the plotting scripts (`ts_month.py`, `ts_clock_hottest.py`) based on a tidal-stream example from the course, and to debug every error that came up — the empty cache file, the JSON decode error, the awkward colour transition, the choppy animation. For the writing itself, I drafted the README in Chinese first, then used DeepSeek to polish it and translate it into English with appropriate word count. I did not use it to decide what the essay argues; I used it to write code I had described but not yet written, and to say in English what I had already said in Chinese.

## One thing it produced that I kept

The smooth-motion interpolation in `ts_clock_hottest.py`. My first animation jumped one hour per frame — twenty-four frames, and the moving dot teleported around the dial. DeepSeek suggested splitting each hour into `SUBSTEPS = 5` sub-frames and interpolating the radius linearly between `radii[h1]` and `radii[h2]` while letting the angle move continuously as a float. That is a small trick, but it is exactly right: the hour axis is continuous in reality, so treating it as continuous in the animation is a correctness choice, not a cosmetic one. I kept it and increased `SUBSTEPS` to 5, which gave the 120-frame smooth sweep in the GIF.

## One thing it produced that I rejected

My first attempt to get DeepSeek to make a green-to-red-to-dark-red gradient did not go well. The hourly temperature plot it produced had muddy colors and hard jumps between segments, as if the blocks had been pasted together. I dropped that version and rewrote the description more clearly: light green through yellow and orange to red, ending in dark red, smooth transitions, no gray. It redid it, and the result is the version now used in the README. That experience changed one habit: before giving an instruction, I ask myself whether someone who has never seen the figure could reproduce it from my words. If not, that is on me.