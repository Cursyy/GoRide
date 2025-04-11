import platform
import subprocess


def check_redis_running():
    try:
        result = subprocess.run(
            ["docker", "ps", "-q", "-f", "name=redis_server"],
            check=False,  # Не викликаємо помилку, якщо контейнер не знайдено
            capture_output=True,
            text=True,  # Декодуємо вихід як текст
        )
        # Якщо stdout не порожній, значить контейнер знайдено і запущено
        return bool(result.stdout.strip())
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        print("Error: Docker not found. Make sure Docker is installed and running.")
        return False


def start_redis():
    try:
        print("Redis is not running. Starting Redis and Celery...")
        subprocess.run(["docker-compose", "up", "-d"], check=True)
        print("Redis and Celery started.")
    except FileNotFoundError:
        print("Error: docker-compose not found. Make sure Docker Compose is installed.")
    except subprocess.CalledProcessError as e:
        print(f"Error starting Redis and Celery: {e}")


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

    print(
        "Checking and starting Redis and Celery (if necessary) using Docker Compose..."
    )
    if not check_redis_running():
        start_redis()
    else:
        print("Redis is already running.")

    run_daphne()
