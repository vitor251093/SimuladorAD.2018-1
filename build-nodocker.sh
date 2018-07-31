apt-get update
apt-get install python -y
apt-get install python-dev -y
apt-get install python-pip -y

pip install --upgrade pip
pip install setuptools
apt-get install libblas3 liblapack3 liblapack-dev libblas-dev -y
pip install scipy
pip install numpy
pip install flask

chmod +x ./simulador/run-nodocker.sh
./simulador/run-nodocker.sh
