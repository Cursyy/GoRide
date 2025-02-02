# GoRide 🚲🛴

**GoRide** is a web platform for bike and scooter rentals, developed as part of a semester project by a team of three students. The platform is built using Django and aims to provide an easy-to-use system for browsing, renting, and managing rides.

## Project Overview 📋

GoRide is designed to offer a simple and efficient platform for renting bikes and scooters. Users will be able to register, check availability, and make bookings, all through an intuitive interface. This project is being developed as part of a semester-long course.

## Development Team 👩‍💻👨‍💻

This project is being developed by a team of three students as part of a semester project. The focus is on learning and applying Django to create a functional, real-world application.

## 🚀 **GoRide Project Setup Guide**

This guide will help you and your team set up a Django project efficiently without using Docker. It includes environment setup, dependency management, code formatting, and workflow automation.
## 📚 Useful Resources:

- Django Documentation
- pip-tools Documentation
- pre-commit Documentation
- Black (Code Formatter)
- Flake8 (Linter)
- Conventional Commits
## 📌 Prerequisites

- Python 3.x installed
- Git installed
- `just` for task automation (recommended)

## 🔧 1. Clone the Repository

```bash
git clone https://github.com/Cursyy/GoRide.git
cd project
```

## 📦 2. Set Up a Virtual Environment
## **Do this every time before you start coding**
```bash
python -m venv env
source env/bin/activate  # macOS/Linux
env\Scripts\activate  # Windows
```

## 📋 3. Install Dependencies

Install all the necessary dependencies using pip:
```bash
pip install <package-name>
```
After installing all the required packages, freeze the installed packages into a requirements.txt file:
```bash
    pip freeze > requirements.txt
```
    Commit and push the requirements.txt to the repository.

Installing Dependencies from requirements.txt:

To install the dependencies on a new environment or for other team members, simply run:
```bash
pip install -r requirements.txt
```
## 🚀 4. Automate Tasks with `invoke`


### **Important Notes:**

- **Steps 1 and 2** are only necessary for the person who is setting up the project environment for the first time.
- **Other team members** who have already installed the dependencies can skip Steps 1 and 2 and directly move on to Step 3.

### 1. Install `invoke`:

You can install `invoke` via `pip`:

```bash
pip install invoke
```

### 2. Create a `tasks.py` File in Your Project:

Instead of using a `justfile`, you'll create a `tasks.py` file in your project root. This file will contain all the commands you'd like to automate.

### `tasks.py` Example:

```python
from invoke import task

@task
def setup(ctx):
    """Set up the virtual environment and install dependencies."""
    ctx.run("python -m venv env")
    ctx.run("env/bin/activate && pip install -r requirements.txt")
    ctx.run("invoke migrate")
    ctx.run("invoke run")

@task
def run(ctx):
    """Run the Django development server."""
    ctx.run("python manage.py runserver")

@task
def migrate(ctx):
    """Apply database migrations."""
    ctx.run("python manage.py migrate")

@task
def createsuperuser(ctx):
    """Create a superuser for the Django project."""
    ctx.run("python manage.py createsuperuser")
```

### 3. Run the Tasks:

Once you have the `tasks.py` file set up, you can run the tasks using `invoke`:

```bash
invoke setup
```

This will automatically set up the project, activate the virtual environment, install dependencies, and run any other tasks you define in the `tasks.py`.


## 🎨 5. Code Formatting & Linting

We use `pre-commit` to enforce coding standards:

```bash
pip install pre-commit
pre-commit install
```

Add `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
  - repo: https://github.com/PyCQA/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
```

Now, before each commit, code will be automatically formatted.

## 🔄 6. Git Workflow

- `main` – Stable production-ready branch
- `develop` – Active development branch
- `feature/*` – Feature branches

Example workflow:

```bash
git checkout -b feature/auth
# Make changes
git commit -m "Added authentication"
git push origin feature/auth
```

## 📜 7. Conventional Commits

We follow [Conventional Commits](https://www.conventionalcommits.org/) to maintain a clear commit history.

### Why?
- Helps automate changelogs
- Improves collaboration and readability
- Standardizes commit messages

### Commit Message Format:
```
type(scope): short description
```

### Examples:
```bash
git commit -m "feat(auth): add login functionality"
git commit -m "fix(api): resolve 500 error on GET request"
git commit -m "docs(readme): update setup instructions"
```

### Common Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (no logic changes)
- `refactor`: Code refactoring (no new features or fixes)
- `test`: Adding or updating tests
- `chore`: Maintenance tasks (e.g., dependencies, CI/CD updates)

