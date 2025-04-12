import subprocess
from watchgod import run_process


def run():
    subprocess.run(["daphne", "-b", "0.0.0.0", "-p", "8000", "GoRide.asgi:application"])


if __name__ == "__main__":
    run_process("GoRide", run)
