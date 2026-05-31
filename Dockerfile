FROM mcr.microsoft.com/playwright/python:v1.60.0-noble

WORKDIR /app



RUN git clone https://github.com/sjjamsa/epscrape.git
WORKDIR /app/epscrape/


RUN pip install --no-cache-dir -r container_requirements.txt

ENV PYTHONUNBUFFERED=1

run mkdir data

CMD ["timeout", "30", "python", "scraper.py"]