# Audio install

Personal-use hunt sounds. The updater/installer looks here:

- `https://raw.githubusercontent.com/Memberoffoxhound/FndZlda/main/fndzlda/listen.wav`
- `https://raw.githubusercontent.com/Memberoffoxhound/FndZlda/main/fndzlda/storms.mp3`
- sidecar fallbacks: `listen.wav.b64` and `storms.mp3.b64` (ASCII; decoded locally)

Aliases accepted next to the package: `LockChime.wav`, `song-of-storms-ocarina.mp3`.

`fndzlda.sounds.ensure_sounds()` copies aliases, decodes sidecars, then downloads raw.
