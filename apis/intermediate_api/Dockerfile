FROM python:3.8.2

ENV PYTHONUNBUFFERED 1

ARG BRANCH_NAME

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt
RUN pip install "git+https://github.com/ucgmsim/seistech.git@${BRANCH_NAME}#egg=intermediate_api&subdirectory=apis/intermediate_api"

CMD ["python", "intermediate_api/app.py"]
