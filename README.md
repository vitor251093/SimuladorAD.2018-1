# SimuladorAD.2018-1
Simulador de AD (2018-1)

## Como usar
Diferentes métodos para executar o trabalho de forma apropriada. Primeiramente é preciso levantar o backend.

### Levantando o backend
#### Opção 1 (Sandbox)
**Necessita ter Docker previamente instalado**

Método compatível com Linux e macOS. Ir com o terminal até o diretório do repositório e usar o comando:
```
chmod +x build-docker.sh 
./build-docker.sh
```

Um docker será criado e iniciará a execução do backend.

#### Opção 2 (Local)
Método compatível com Linux apenas. Ir com o terminal até o diretório do repositório e usar o comando:
```
chmod +x build-nodocker.sh 
sudo ./build-nodocker.sh
```

A execução do backend irá iniciar, e ficará rodando em background.

### Visualizando o frontend
```
http://localhost:5000/?pacotesporrodada=200&r=1
```

## Log 27 Maio:
* Usaremos Flask no backend pra receber os requests: http://flask.pocoo.org/
* Aproveitaremos Classes do trabalho do semestre passado, já que implementamos duas filas
* Usaremos ChartJS para gerar os gráficos no frontend: https://www.chartjs.org/

## Log 31 Julho:
* Estrutura de duas filas do semestre passado reaproveitada
* Python+Flask funcionando dentro e fora de um Docker
* Frontend ainda a fazer

