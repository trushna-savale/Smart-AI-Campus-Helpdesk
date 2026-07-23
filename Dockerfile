FROM langflowai/langflow:latest
EXPOSE 10000
ENV LANGFLOW_NUM_WORKERS=1
ENV DO_NOT_TRACK=true
ENV LANGFLOW_AUTO_LOGIN=true
CMD ["sh", "-c", "langflow run --host 0.0.0.0 --port ${PORT:-10000} --backend-only"]
