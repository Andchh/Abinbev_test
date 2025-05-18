FROM apache/airflow:3.0.1-python3.10

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
RUN export JAVA_HOME

COPY requirements.txt /requirements.txt

RUN pip install --no-cache-dir -r /requirements.txt

