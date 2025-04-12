FROM python:3.11
ADD rockerBot.py .
COPY requirements.txt /tmp
RUN pip install -r /tmp/requirements.txt
RUN apt-get -y update && apt-get -y upgrade && apt-get install -y --no-install-recommends ffmpeg
CMD ["python3", "./rockerBot.py"]