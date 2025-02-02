from invoke import task


@task
def setup(ctx):
    """Set up the virtual environment and install dependencies."""
    ctx.run("python -m venv venv")
    ctx.run("source venv/bin/activate && pip install -r requirements.txt")
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
