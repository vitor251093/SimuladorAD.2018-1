docker build -t trabalhoad1 .
docker run -p 5000:5000 --name trabalhoad1 -td trabalhoad1
docker exec -it trabalhoad1 bash /simulador/run-docker.sh

