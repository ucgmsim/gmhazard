from celery import Celery

app = Celery(
    "service",
    backend="redis://localhost",
    broker="redis://localhost",
    include=["project_gen.tasks"],
)

app.conf.update(
    result_expires=3600,
)

if __name__ == "__main__":
    app.start()
