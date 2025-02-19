# Links
- https://jellyfin.org/docs/general/server/live-tv/post-process/
- https://github.com/Protektor-Desura/jellyfin-dvr-comskip/blob/main/config/comskip/jellyfin-drv-comskip.sh
- https://github.com/AndrewBreyen/Jellyfin-TV-Post-Process/

```
comskip --output=/tmp/comskip --ini=./comskip.ini /var/lib/jellyfin/data/livetv/recordings/Murder,\ She\ Wrote/Season\ 5/Murder,\ She\ Wrote\ S05E12\ Smooth\ Operators.ts
```


```
ffmpeg \
  -i /var/lib/jellyfin/data/livetv/recordings/Murder,\ She\ Wrote/Season\ 5/Murder,\ She\ Wrote\ S05E12\ Smooth\ Operators.ts \
  -i ./scratch/chapters.ffmeta \
  -map_metadata 1 \
  -codec copy scratch/out.mp4
```