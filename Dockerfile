FROM langflowai/langflow:latest
EXPOSE 7860
ENV LANGFLOW_NUM_WORKERS=1
ENV DO_NOT_TRACK=true
ENV LANGFLOW_AUTO_LOGIN=true
CMD ["langflow", "run", "--host", "0.0.0.0", "--port", "7860", "--backend-only"]
