# Jellyfin recording post-processing

This script post-processes Jellyfin Live TV recordings. It scans the recordings tree for `.ts` files that have not been modified in the last 10 minutes, runs Comskip to generate chapter metadata, then runs FFmpeg to deinterlace and transcode the recording to MKV. After a successful transcode it deletes the original `.ts` file.

If processing fails, the script writes a sibling `.skip` file containing the traceback. Recordings with an existing `.skip` file are ignored until that file is removed. **Back up recordings before enabling this job:** successful runs replace the original with a transcoded file and remove the source recording.

## Requirements

- Linux with systemd
- Python 3.13 or newer and [uv](https://docs.astral.sh/uv/)
- `ffmpeg` available on `PATH` (with `libx264` support)
- The Comskip executable, available as `./comskip` in the project directory

Comskip is an external prerequisite; its source and binary are not included in this repository. The script also uses the checked-in `comskip.ini` configuration. Make sure the `jellyfin` account can execute Comskip and FFmpeg and can read, write, and delete files in the recordings tree.

## Build and install

The service is configured for this checkout location:

```text
/var/lib/jellyfin/scripts/jellyfin-scripts
```

Clone or place the repository there, and make sure it is owned/readable by the `jellyfin` account. For example, using the HTTPS remote:

```sh
sudo install -d -o jellyfin -g jellyfin /var/lib/jellyfin/scripts
sudo -u jellyfin git clone https://github.com/sirianni/jellyfin-scripts.git \
  /var/lib/jellyfin/scripts/jellyfin-scripts
```

Install the Python environment and put the Comskip executable in the checkout. `main.py` invokes it using the relative path `./comskip`, so it must be in the project root and executable:

```sh
cd /var/lib/jellyfin/scripts/jellyfin-scripts
sudo -u jellyfin uv sync --no-dev
# Install/copy your Comskip executable here, then:
sudo chmod 0755 ./comskip
```

`uv sync` creates the `.venv` used by the service. The project currently has no Python runtime dependencies. `uv build` can build a wheel and source archive for packaging, but the systemd unit runs `main.py` from the checkout directly; installing the wheel is not required for this deployment.

The checked-in systemd units use the same fixed checkout and recordings paths. If your paths differ, edit `jellyfin-post-process.service` before linking it:

- Working directory: `/var/lib/jellyfin/scripts/jellyfin-scripts`
- Recordings root: `/var/lib/jellyfin/data/livetv/recordings`
- Runtime user/group: `jellyfin`

Link both unit files into systemd. `systemctl link` creates links to the files in this checkout (rather than copying them into `/etc/systemd/system`):

```sh
cd /var/lib/jellyfin/scripts/jellyfin-scripts
sudo systemctl link "$PWD/jellyfin-post-process.service" "$PWD/jellyfin-post-process.timer"
sudo systemctl daemon-reload
sudo systemctl enable --now jellyfin-post-process.timer
```

The timer is scheduled for 02:00 every day. It starts `jellyfin-post-process.service`, which scans the configured recordings root. To run it immediately or inspect it:

```sh
sudo systemctl start jellyfin-post-process.service
sudo systemctl status jellyfin-post-process.timer jellyfin-post-process.service
sudo journalctl -u jellyfin-post-process.service
```

To stop the schedule, disable the timer:

```sh
sudo systemctl disable --now jellyfin-post-process.timer
```

## Run manually

For a one-off run, activate the project environment and pass the recordings directory as the sole argument:

```sh
uv run main.py /var/lib/jellyfin/data/livetv/recordings
```

The program logs progress to standard output/error (captured by systemd when run as a unit). It does not require a Jellyfin API token; it operates directly on files in the recordings tree.
