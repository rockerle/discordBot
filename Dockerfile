FROM python:3.11.13-bookworm
ADD rockerBot.py .
ADD ascii/** ./ascii/
COPY requirements.txt /tmp
RUN pip install -r /tmp/requirements.txt
RUN apt-get -y update && apt-get -y upgrade && apt-get install -y --no-install-recommends ffmpeg
CMD ["python3", "./rockerBot.py"]