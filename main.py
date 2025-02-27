import logging
import os
import subprocess
import sys
import time

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.DEBUG,
)

COMSKIP = "./comskip"


class Recording:
    def __init__(self, basename, filename, dir):
        self.basename = basename
        self.filename = filename
        self.dir = dir

    @staticmethod
    def from_path(path):
        return Recording(
            basename=os.path.splitext(os.path.basename(path))[0],
            filename=os.path.basename(path),
            dir=os.path.dirname(path),
        )

    def abs_path(self):
        return os.path.join(self.dir, self.filename)

    def delete_orig(self):
        logger.info(f"Deleting original file: {self.abs_path()}")
        os.remove(self.abs_path())

    def comskip(self):
        try:
            logger.info("Running comskip...")

            result = subprocess.run(
                [
                    COMSKIP,
                    "--ini=./comskip.ini",
                    f"--output={self.dir}",
                    self.abs_path(),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            logger.debug(f"comskip output:\n{result.stdout}")

            self.chapter_ffmeta = os.path.join(self.dir, f"{self.basename}.ffmeta")

        except subprocess.CalledProcessError as e:
            logger.error(f"'{e.cmd}' returned non-zero exit status {e.returncode}.")
            logger.error(f"stdout: {e.stdout}")
            logger.error(f"stderr: {e.stderr}")
            raise e

    def transcode(self):
        input_file = self.abs_path()
        self.transcoded_file = os.path.join(self.dir, f"{self.basename}.mp4")

        try:
            logger.info("Running ffmpeg...")

            process = subprocess.Popen(
                [
                    "ffmpeg",
                    "-i", input_file,
                    "-i", self.chapter_ffmeta,
                    "-map_metadata", "1",
                    "-filter:v", "yadif", # deinterlace
                    "-codec:v", "libx264", "-preset", "medium", "-crf", "24",
                    "-codec:a", "copy",
                    "-y",  # Overwrite output files without asking
                    "-stats_period", "15",
                    self.transcoded_file,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )  # fmt: skip

            for line in iter(process.stdout.readline, ""):
                logger.debug(line.strip())

            process.stdout.close()
            process.wait()

            logger.info(f"Transcoding completed: {self.transcoded_file}")
        except subprocess.CalledProcessError as e:
            logger.error(f"'{e.cmd}' returned non-zero exit status {e.returncode}.")
            logger.error(f"stdout: {e.stdout}")
            logger.error(f"stderr: {e.stderr}")
            raise e


def walk_directory(dir):
    logger.info(f"Walking directory: {dir}")

    current_time = time.time()
    mtime_cutoff = current_time - 600

    for dirpath, _, files in os.walk(dir):
        for file in files:
            if file.endswith(".ts"):
                file_path = os.path.join(dirpath, file)
                if os.path.getmtime(file_path) < mtime_cutoff:
                    recording = Recording.from_path(file_path)
                    logger.info(f"Processing recording: {recording.basename}")
                    recording.comskip()
                    recording.transcode()
                    recording.delete_orig()
                else:
                    logger.info(f"Skipping recently modified file: {file_path}")


if len(sys.argv) == 1:
    raise ValueError(
        f"Expected 2 arguments, got {len(sys.argv)}.\nArgs recieved: {str(sys.argv)}"
    )

dir = sys.argv[1]
walk_directory(dir)
