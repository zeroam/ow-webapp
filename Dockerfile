FROM ubuntu

WORKDIR /src/app

# Options from https://testdriven.io/blog/dockerizing-flask-with-postgres-gunicorn-and-nginx/
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONBUFFERED 1

# Install dependencies
RUN apt-get update
RUN apt-get install -y \
    wget \
    default-jre \
    python-pygame

# Download pre-trained yolo3 model
RUN mkdir /yolo && \
    wget https://pjreddie.com/media/files/yolov3.weights -O /yolo/yolov3.weights && \
    wget https://github.com/pjreddie/darknet/blob/master/cfg/yolov3.cfg?raw=true -O /yolo/yolov3.cfg && \
    wget https://github.com/pjreddie/darknet/blob/master/data/coco.names?raw=true -O /yolo/coco.names

# Install python 3.8
RUN apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y python3.8 python3-pip
RUN apt-get install -y git

# Install python packages
RUN pip3 install --upgrade pip
RUN pip3 install git+https://github.com/e9t/PyTagCloud.git
COPY ./requirements.txt /src/app/requirements.txt
RUN pip3 install -r requirements.txt

COPY . /src/app

CMD gunicorn --bind 0.0.0.0:5000 app:app