import logging
import os
import subprocess
import sys

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.DEBUG,
)

COMSKIP = "comskip"


class Recording:
    def __init__(self, basename, filename, dir):
        self.basename = basename
        self.filename = filename
        self.dir = dir

    def __repr__(self):
        return f"<Recording basename={self.basename} filename={self.filename} dir={self.dir}>"

    @staticmethod
    def from_path(path):
        return Recording(
            basename=os.path.splitext(os.path.basename(path))[0],
            filename=os.path.basename(path),
            dir=os.path.dirname(path),
        )

    def abs_path(self):
        return os.path.join(self.dir, self.filename)

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
                    "-c:v", "libx264", "-preset", "medium", "-crf", "25",
                    "-acodec", "aac", "-ar", "44100", "-b:a", "256k",
                    "-y",  # Overwrite output files without asking
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


if len(sys.argv) == 1:
    raise ValueError(
        f"Expected 2 arguments, got {len(sys.argv)}.\nArgs recieved: {str(sys.argv)}"
    )

recording = Recording.from_path(sys.argv[1])

logger.info(f"Processing recording: {recording}")
recording.comskip()
recording.transcode()
