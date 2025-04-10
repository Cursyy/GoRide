import platform
import subprocess


def check_redis_running():
    try:
        subprocess.run(
            ["docker", "ps", "-q", "-f", "name=redis_server"],
            check=True,
            capture_output=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        print("Error: Docker not found. Make sure Docker is installed and running.")
        return False


def start_redis():
    try:
        print("Redis is not running. Starting...")
        subprocess.run(["docker-compose", "up", "-d", "redis"], check=True)
        print("Redis started.")
    except FileNotFoundError:
        print("Error: docker-compose not found. Make sure Docker Compose is installed.")
    except subprocess.CalledProcessError as e:
        print(f"Error starting Redis: {e}")


def run_daphne():
    try:
        print("Starting Daphne...")
        print("Server running on http://127.0.0.1:8000")
        subprocess.run(["daphne", "GoRide.asgi:application"], check=True)
    except FileNotFoundError:
        print(
            "Error: 'daphne' command not found. Make sure Daphne is installed in your virtual environment."
        )
    except subprocess.CalledProcessError as e:
        print(f"Error starting Daphne: {e}")


if __name__ == "__main__":
    os_name = platform.system()
    print(f"Detected operating system: {os_name}")

    if os_name == "Windows":
        print("Checking and starting Redis (if necessary) using Docker Compose...")
        if not check_redis_running():
            start_redis()
        else:
            print("Redis is already running.")
        run_daphne()
    elif os_name == "Darwin" or os_name == "Linux":
        print("Checking and starting Redis (if necessary) using Docker Compose...")
        if not check_redis_running():
            start_redis()
        else:
            print("Redis is already running.")
        run_daphne()
    else:
        print(
            f"Unknown operating system: {os_name}. Please configure Redis and Daphne startup manually."
        )
