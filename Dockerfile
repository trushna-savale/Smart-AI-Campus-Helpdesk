FROM langflowai/langflow:latest
EXPOSE 7860
CMD ["langflow", "run", "--host", "0.0.0.0", "--port", "7860"]
