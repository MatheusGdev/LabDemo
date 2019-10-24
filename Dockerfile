FROM python:2.7
MAINTAINER Matheus Goncalves "MatGon.dev@gmail.com"
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
ENTRYPOINT ["python"]
CMD ["app.py"]
