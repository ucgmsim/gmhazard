FROM python:3.8.2

ENV PYTHONUNBUFFERED 1

ARG BRANCH_NAME

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt
RUN pip install "git+https://github.com/ucgmsim/seistech_psha_frontend.git@${BRANCH_NAME}#egg=middleware&subdirectory=middleware"

CMD ["python", "app.py"]
