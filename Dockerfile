FROM ubuntu

RUN apt-get update
RUN apt-get install python -y
RUN apt-get install python-dev -y
RUN apt-get install python-pip -y

RUN pip install --upgrade pip
RUN pip install setuptools
RUN apt-get install libblas3 liblapack3 liblapack-dev libblas-dev -y
RUN pip install scipy
RUN pip install numpy
RUN pip install flask

COPY simulador /simulador
RUN FLASK_APP=/simulador/main.py flask run &
