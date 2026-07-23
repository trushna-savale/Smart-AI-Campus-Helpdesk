FROM python:3.10-slim
WORKDIR /app
RUN pip install --upgrade pip setuptools wheel
RUN pip install langflow
EXPOSE 7860
CMD ["langflow", "run", "--host", "0.0.0.0", "--port", "7860"]
