FROM python:3.10-alpine

WORKDIR /usr/src/app

COPY . .
RUN echo "contents copied..."
RUN python -m pip install -U pip
RUN pip install --no-cache-dir -r ./Webapp_requirements.txt
EXPOSE 80
RUN echo "starting to run strategy"

CMD ["uvicorn", "Webapp_Strategies:app", "--host", "0.0.0.0", "--port", "80"]
