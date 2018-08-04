from controllers.agendador import *
from models.pacote import *
from models.fila import *
from models.fase import *
from models.evento import *
from views.view import *
import random
import math
import sys
import getopt
import warnings
from flask import Flask
from flask import request
from flask import render_template
""" Principal classe do simulador. Simulacao possui o metodo executarSimulacao que eh 
    chamado pelo main, o qual pode ser encontrado no fim deste arquivo. """

EVENTO_PACOTE_VOZ_CHEGADA = 0
EVENTO_PACOTE_VOZ_FINALIZADO = 1
EVENTO_PACOTE_DADOS_CHEGADA = 2
EVENTO_PACOTE_DADOS_FINALIZADO = 3

class Simulacao(object):

    def __init__(self):
        self.__lambd = None
        self.__interrupcoes = False
        self.__numero_de_pacotes_por_fase = None
        self.__numero_de_rodadas = None
        self.__intervaloDeConfianca = None

        self.__seedsDistance = 0.01
        self.__seedsList = []
        self.__view = None
        self.__output_type = None
        
        self.__agendador = Agendador()
        
        self.__pacotes = []
        self.__filaVoz = Fila(1)
        self.__filaDados = Fila(2)
        
        self.__fases = []
        self.__fase = Fase(-1, 0)
        
        self.__tempoAtual = 0.0
        self.__indice_pacote_atual = 0
        self.__indice_primeiro_pacote_nao_transiente = 0
        self.__faseTransienteFinalizada = False

        self.__lista_de_eventos = []

        ### Atributos usados para determinar o fim da fase transiente
        self.__quantidadeDeEventosPorVariancia = 1000
        self.__diferencaAceitavelDasVariancias = 0.0000002
        self.__eventosDaVariancia1 = []
        self.__duracaoEventosDaVariancia1 = []
        self.__eventosDaVariancia2 = []
        self.__duracaoEventosDaVariancia2 = []


    """ Esse metodo apenas fica responsavel por relizar os somatorios
        para o calculo do numero medio de pessoas nas duas filas (E[Ns]). """
    def agregarEmSomatorioPessoasPorTempo (self, tempo):
        self.__fase.inserirNumeroDePacotesPorTempoNaFilaVoz(self.__filaVoz.numeroDePessoasNaFila(), tempo)
        self.__fase.inserirNumeroDePacotesPorTempoNaFilaDados(self.__filaVoz.numeroDePessoasNaFila(), tempo)

        if self.__filaVoz.numeroDePessoasNaFila() > 0:
            self.__fase.inserirNumeroDePacotesPorTempoNaFilaEspera1(self.__filaVoz.numeroDePessoasNaFila() - 1, tempo)
        else:
            self.__fase.inserirNumeroDePacotesPorTempoNaFilaEspera1(0, tempo)

        if self.__filaVoz.numeroDePessoasNaFila() > 0:
            self.__fase.inserirNumeroDePacotesPorTempoNaFilaEspera2(self.__filaDados.numeroDePessoasNaFila(), tempo)
        else:
            if self.__filaDados.numeroDePessoasNaFila() > 0:
                self.__fase.inserirNumeroDePacotesPorTempoNaFilaEspera2(self.__filaDados.numeroDePessoasNaFila() - 1, tempo)
            else: 
                self.__fase.inserirNumeroDePacotesPorTempoNaFilaEspera2(0, tempo)

    def adicionarEvento (self, Pacote, evento, fila, momento):
        #tipo = "de voz" if Pacote.getCanal() != -1 else "de dados"
        #print "%f: Pacote %s %d (%d) %s na fila %d" % (momento, tipo, Pacote.getID(), Pacote.getIndiceDaCor(), evento, fila)
        
        ENt = self.__fase.getEsperancaDeN(momento)

        if self.__output_type == 1:
            self.__view.imprimir("%f,%d" % (ENt, self.__fase.getID()))
        if self.__output_type == 2:
            self.__view.imprimir("%f,%d" % (self.__fase.getEsperancaDeN1(momento), self.__fase.getID()))
        if self.__output_type == 3:
            self.__view.imprimir("%f,%d" % (self.__fase.getEsperancaDeN2(momento), self.__fase.getID()))
        if self.__output_type == 4:
            self.__view.imprimir("%f,%d" % (self.__fase.getEsperancaDeNq1(momento), self.__fase.getID()))
        if self.__output_type == 5:
            self.__view.imprimir("%f,%d" % (self.__fase.getEsperancaDeNq2(momento), self.__fase.getID()))
        if self.__output_type == 6:
            self.__view.imprimir("%f,%d" % (self.__fase.getEsperancaDeTVoz(), self.__fase.getID()))
        if self.__output_type == 7:
            self.__view.imprimir("%f,%d" % (self.__fase.getEsperancaDeTDados(), self.__fase.getID()))
        if self.__output_type == 8:
            self.__view.imprimir("%f,%d" % (self.__fase.getEsperancaDeWVoz(), self.__fase.getID()))
        if self.__output_type == 9:
            self.__view.imprimir("%f,%d" % (self.__fase.getEsperancaDeWDados(), self.__fase.getID()))
        if self.__output_type == 10:
            self.__view.imprimir("%f,%d" % (self.__fase.getVarianciaDeW1(), self.__fase.getID()))
        if self.__output_type == 11:
            self.__view.imprimir("%f,%d" % (self.__fase.getVarianciaDeW2(), self.__fase.getID()))

        if self.__faseTransienteFinalizada == True:
            return


        # Daqui para baixo, essa funcao realiza o calculo que define quando
        # a fase transiente acaba. Comparando a variancia das ultimas 1000
        # amostras de E[N] com a variancia das 1000 amostras anteriores,
        # o fim da fase transiente eh caracterizado quando se encontram
        # duas variancias que variam apenas em 0,0000002.

        if len(self.__eventosDaVariancia1) < self.__quantidadeDeEventosPorVariancia:
            self.__eventosDaVariancia1.append(ENt)
            self.__duracaoEventosDaVariancia1.append(momento)

        else: 
            if len(self.__eventosDaVariancia2) < self.__quantidadeDeEventosPorVariancia:
                self.__eventosDaVariancia2.append(ENt)
                self.__duracaoEventosDaVariancia2.append(momento)

                if len(self.__eventosDaVariancia2) == self.__quantidadeDeEventosPorVariancia:
                    media1 = 0
                    media2 = 0
                    duracao1 = 0
                    duracao2 = 0
                    for indiceEvento in range(self.__quantidadeDeEventosPorVariancia):
                        media1 += self.__eventosDaVariancia1[indiceEvento]*self.__duracaoEventosDaVariancia1[indiceEvento]
                        media2 += self.__eventosDaVariancia2[indiceEvento]*self.__duracaoEventosDaVariancia2[indiceEvento]
                        duracao1 += self.__duracaoEventosDaVariancia1[indiceEvento]
                        duracao2 += self.__duracaoEventosDaVariancia2[indiceEvento]
                    media1 /= duracao1
                    media2 /= duracao2
                    
                    variancia1 = 0
                    variancia2 = 0
                    for indiceEvento in range(self.__quantidadeDeEventosPorVariancia):
                        variancia1 += (self.__eventosDaVariancia1[indiceEvento] - media1)**2
                        variancia2 += (self.__eventosDaVariancia2[indiceEvento] - media2)**2
                    variancia1 /= (self.__quantidadeDeEventosPorVariancia - 1)
                    variancia2 /= (self.__quantidadeDeEventosPorVariancia - 1)

                    if abs(variancia1 - variancia2) < self.__diferencaAceitavelDasVariancias:
                        self.__faseTransienteFinalizada = True
                    else:
                        self.__eventosDaVariancia1 = self.__eventosDaVariancia2
                        self.__duracaoEventosDaVariancia1 = self.__duracaoEventosDaVariancia2
                        self.__eventosDaVariancia2 = []
                        self.__duracaoEventosDaVariancia2 = []


    """Evento: Pacote entra na fila de voz
       Com essa funcao realizamos todas as acoes que ocorrem em decorrencia da
       entrada de um Pacote na fila de voz, que sao: se nao houver ninguem na fila de voz,
       levar esse Pacote diretamente ao servico, e interrompe qualquer Pacote
       da fila de dados que possa estar sendo atendido.
        
       Eh aqui tambem que decidimos qual sera a cor de um Pacote. O fim de uma fase/rodada
       tambem ocorre aqui, entao aqui tambem ocorrem os calculos estatisticos que sao 
       chamados ao fim de uma fase/rodada."""

    def PacoteEntraNaFilaVoz (self, canal, tempoAnterior, tempoAvancado):
        self.__indice_pacote_atual += 1
        if self.__faseTransienteFinalizada == True and self.__indice_primeiro_pacote_nao_transiente == 0:
            self.__indice_primeiro_pacote_nao_transiente = self.__indice_pacote_atual

        if self.__indice_primeiro_pacote_nao_transiente == 0:
            corDoPacote = -1
        else:
            indiceDaFase = (self.__indice_pacote_atual - self.__indice_primeiro_pacote_nao_transiente)/self.__numero_de_pacotes_por_fase
            if indiceDaFase > self.__fase.getID():
                if self.__output_type == 0:
                    self.__fase.calcularEstatisticas(tempoAnterior, self.__view, self.__intervaloDeConfianca, self.__lambd)

                self.__fase = Fase(indiceDaFase, self.__tempoAtual)
            corDoPacote = indiceDaFase

        if canal == -1:
            print "ERRO: O tempo deslocado nao se aplica a nenhuma das esperas de canais de voz."
            sys.exit(2)

        pacote = Pacote(self.__indice_pacote_atual, self.__tempoAtual, corDoPacote, canal) 
        
        self.__fase.adicionarPacote(pacote)
        self.__filaVoz.adicionarPacoteAFila(pacote)

        self.adicionarEvento(pacote, "chegou", self.__filaVoz.getID(), self.__tempoAtual)
        if self.__filaVoz.numeroDePessoasNaFila() == 1: # So o atual se encontra na fila
            if self.__interrupcoes == False and self.__filaDados.numeroDePessoasNaFila() == 0:
                pacote.setTempoChegadaServico(self.__tempoAtual)
                #self.adicionarEvento(pacote, "comecou a ser atendido", self.__filaVoz.getID(), self.__tempoAtual)
                
                novoEvento = Evento(EVENTO_PACOTE_VOZ_FINALIZADO, pacote.getCanal(), self.__agendador.agendarTempoDeServicoFilaVoz(pacote.getCanal()))
                self.__lista_de_eventos.append(novoEvento)
                pacote.setTempoServico(novoEvento.tempoRestante())

                if self.__agendador.deveAgendarChegadaFilaVoz(pacote.getCanal()):
                    novoEvento = Evento(EVENTO_PACOTE_VOZ_CHEGADA, pacote.getCanal(), self.__agendador.agendarChegadaFilaVoz(pacote.getCanal()))
                    self.__lista_de_eventos.append(novoEvento)
            else:
                if self.__interrupcoes == True:
                    if self.__filaDados.numeroDePessoasNaFila() > 0: # Interrompe individuo da fila de dados
                        PacoteInterrompido = self.__filaDados.PacoteEmAtendimento()
                        PacoteInterrompido.setTempoDecorridoServico(PacoteInterrompido.getTempoDecorridoServico() + tempoAvancado)
                        for evento in self.__lista_de_eventos:
                            if evento.tipo() == EVENTO_PACOTE_DADOS_FINALIZADO:
                                self.__lista_de_eventos.remove(evento)
                    
                    pacote.setTempoChegadaServico(self.__tempoAtual)
                    #self.adicionarEvento(pacote, "comecou a ser atendido", self.__filaVoz.getID(), self.__tempoAtual)
                    
                    novoEvento = Evento(EVENTO_PACOTE_VOZ_FINALIZADO, pacote.getCanal(), self.__agendador.agendarTempoDeServicoFilaVoz(pacote.getCanal()))
                    self.__lista_de_eventos.append(novoEvento)
                    pacote.setTempoServico(novoEvento.tempoRestante())

                    if self.__agendador.deveAgendarChegadaFilaVoz(pacote.getCanal()):
                        novoEvento = Evento(EVENTO_PACOTE_VOZ_CHEGADA, pacote.getCanal(), self.__agendador.agendarChegadaFilaVoz(pacote.getCanal()))
                        self.__lista_de_eventos.append(novoEvento)

        if self.__faseTransienteFinalizada == False:
            novoEvento = Evento(EVENTO_PACOTE_VOZ_CHEGADA, pacote.getCanal(), self.__agendador.agendarChegadaFilaVoz(pacote.getCanal()))
            self.__lista_de_eventos.append(novoEvento)
            return

        if self.__fase.getID() + 1 != self.__numero_de_rodadas or self.__fase.quantidadeDePacotes() != self.__numero_de_pacotes_por_fase:
            novoEvento = Evento(EVENTO_PACOTE_VOZ_CHEGADA, pacote.getCanal(), self.__agendador.agendarChegadaFilaVoz(pacote.getCanal()))
            self.__lista_de_eventos.append(novoEvento)


    """Evento: Pacote entra na fila de dados
       Com essa funcao realizamos todas as acoes que ocorrem em decorrencia da
       entrada de um Pacote na fila de dados, que sao: se nao houver ninguem na fila 
       de dados nem de voz, levar esse Pacote diretamente ao servico.
        
       Eh aqui tambem que decidimos qual sera a cor de um Pacote. O fim de uma fase/rodada
       tambem ocorre aqui, entao aqui tambem ocorrem os calculos estatisticos que sao 
       chamados ao fim de uma fase/rodada."""

    def PacoteEntraNaFilaDados (self, tempoAnterior):
        self.__indice_pacote_atual += 1
        if self.__faseTransienteFinalizada == True and self.__indice_primeiro_pacote_nao_transiente == 0:
            self.__indice_primeiro_pacote_nao_transiente = self.__indice_pacote_atual

        if self.__indice_primeiro_pacote_nao_transiente == 0:
            corDoPacote = -1
        else:
            indiceDaFase = (self.__indice_pacote_atual - self.__indice_primeiro_pacote_nao_transiente)/self.__numero_de_pacotes_por_fase
            if indiceDaFase > self.__fase.getID():
                if self.__output_type == 0:
                    self.__fase.calcularEstatisticas(tempoAnterior, self.__view, self.__intervaloDeConfianca, self.__lambd)

                self.__fase = Fase(indiceDaFase, self.__tempoAtual)
            corDoPacote = indiceDaFase

        pacote = Pacote(self.__indice_pacote_atual, self.__tempoAtual, corDoPacote, -1)
        
        self.__fase.adicionarPacote(pacote)
        self.__filaDados.adicionarPacoteAFila(pacote)

        self.adicionarEvento(pacote, "chegou", self.__filaDados.getID(), self.__tempoAtual)
        if self.__filaVoz.numeroDePessoasNaFila() == 0 and self.__filaDados.numeroDePessoasNaFila() == 1:
            pacote.setTempoChegadaServico(self.__tempoAtual)
            #self.adicionarEvento(pacote, "comecou a ser atendido", self.__filaDados.getID(), self.__tempoAtual)
            
            novoEvento = Evento(EVENTO_PACOTE_DADOS_FINALIZADO, pacote.getCanal(), self.__agendador.agendarTempoDeServicoFilaDados())
            self.__lista_de_eventos.append(novoEvento)
            pacote.setTempoServico(novoEvento.tempoRestante())

        if self.__faseTransienteFinalizada == False:
            novoEvento = Evento(EVENTO_PACOTE_DADOS_CHEGADA, pacote.getCanal(), self.__agendador.agendarChegadaFilaDados(self.__lambd))
            self.__lista_de_eventos.append(novoEvento)
            return

        if self.__fase.getID() + 1 != self.__numero_de_rodadas or self.__fase.quantidadeDePacotes() != self.__numero_de_pacotes_por_fase:
            novoEvento = Evento(EVENTO_PACOTE_DADOS_CHEGADA, pacote.getCanal(), self.__agendador.agendarChegadaFilaDados(self.__lambd))
            self.__lista_de_eventos.append(novoEvento)


    """Evento: Fim de servico na fila de voz
       Com essa funcao realizamos todas as acoes que ocorrem em decorrencia do 
       fim de um servico na fila de voz, que sao: tirar o Pacote que concluiu o servico 
       da fila de voz, e colocar em servico o proximo Pacote da fila de voz se houver 
       algum (se nao houver, colocar em servico o proximo Pacote da fila de dados, 
       se houver algum)."""

    def PacoteTerminaServicoNaFilaVoz(self):
        Pacote = self.__filaVoz.retirarPacoteEmAtendimento()
        Pacote.setTempoTerminoServico(self.__tempoAtual)
        
        self.adicionarEvento(Pacote, "terminou o atendimento", self.__filaVoz.getID(), self.__tempoAtual)

        if self.__filaVoz.numeroDePessoasNaFila() > 0:
            novoPacote = self.__filaVoz.PacoteEmAtendimento()
            novoPacote.setTempoChegadaServico(self.__tempoAtual)
            #self.adicionarEvento(novoPacote, "comecou a ser atendido", self.__filaVoz.getID(), self.__tempoAtual)

            novoEvento = Evento(EVENTO_PACOTE_VOZ_FINALIZADO, novoPacote.getCanal(), self.__agendador.agendarTempoDeServicoFilaVoz(novoPacote.getCanal()))
            self.__lista_de_eventos.append(novoEvento)
            novoPacote.setTempoServico(novoEvento.tempoRestante())

            if self.__agendador.deveAgendarChegadaFilaVoz(novoPacote.getCanal()):
                novoEvento = Evento(EVENTO_PACOTE_VOZ_CHEGADA, novoPacote.getCanal(), self.__agendador.agendarChegadaFilaVoz(novoPacote.getCanal()))
                self.__lista_de_eventos.append(novoEvento)
        else:
            if self.__filaDados.numeroDePessoasNaFila() > 0:
                proximoPacote = self.__filaDados.PacoteEmAtendimento()
                if proximoPacote.getTempoDecorridoServico() > 0: 
                    # Pacote da fila de dados que foi interrompido anteriormente retorna
                    novoEvento = Evento(EVENTO_PACOTE_DADOS_FINALIZADO, proximoPacote.getCanal(), proximoPacote.getTempoServico() - proximoPacote.getTempoDecorridoServico())
                    self.__lista_de_eventos.append(novoEvento)
                    
                else: 
                    # Pacote da fila de dados eh atendido pela primeira vez
                    proximoPacote.setTempoChegadaServico(self.__tempoAtual)
                    #self.adicionarEvento(proximoPacote, "comecou a ser atendido", self.__filaDados.getID(), self.__tempoAtual)

                    novoEvento = Evento(EVENTO_PACOTE_DADOS_FINALIZADO, proximoPacote.getCanal(), self.__agendador.agendarTempoDeServicoFilaDados())
                    self.__lista_de_eventos.append(novoEvento)
                    proximoPacote.setTempoServico(novoEvento.tempoRestante())


    """Evento: Fim de servico na fila de dados
       Com essa funcao realizamos todas as acoes que ocorrem em decorrencia do 
       fim de um servico na fila de dados, que sao: tirar o Pacote que concluiu o servico 
       da fila de dados, e colocar em servico o proximo Pacote da fila de dados (se houver algum)."""

    def PacoteTerminaServicoNaFilaDados(self):
        Pacote = self.__filaDados.retirarPacoteEmAtendimento()
        Pacote.setTempoTerminoServico(self.__tempoAtual)
        
        self.adicionarEvento(Pacote, "terminou o atendimento", self.__filaDados.getID(), self.__tempoAtual)
        
        if self.__interrupcoes == False and self.__filaVoz.numeroDePessoasNaFila() > 0:
            novoPacote = self.__filaVoz.PacoteEmAtendimento()
            novoPacote.setTempoChegadaServico(self.__tempoAtual)
            #self.adicionarEvento(novoPacote, "comecou a ser atendido", self.__filaVoz.getID(), self.__tempoAtual)

            novoEvento = Evento(EVENTO_PACOTE_VOZ_FINALIZADO, novoPacote.getCanal(), self.__agendador.agendarTempoDeServicoFilaVoz(novoPacote.getCanal()))
            self.__lista_de_eventos.append(novoEvento)
            novoPacote.setTempoServico(novoEvento.tempoRestante())

            if self.__agendador.deveAgendarChegadaFilaVoz(novoPacote.getCanal()):
                novoEvento = Evento(EVENTO_PACOTE_VOZ_CHEGADA, novoPacote.getCanal(), self.__agendador.agendarChegadaFilaVoz(novoPacote.getCanal()))
                self.__lista_de_eventos.append(novoEvento)
        else:
            if self.__filaDados.numeroDePessoasNaFila() > 0:
                proximoPacote = self.__filaDados.PacoteEmAtendimento()
                proximoPacote.setTempoChegadaServico(self.__tempoAtual)
                #self.adicionarEvento(proximoPacote, "comecou a ser atendido", self.__filaDados.getID(), self.__tempoAtual)
                
                novoEvento = Evento(EVENTO_PACOTE_DADOS_FINALIZADO, proximoPacote.getCanal(), self.__agendador.agendarTempoDeServicoFilaDados())
                self.__lista_de_eventos.append(novoEvento)
                proximoPacote.setTempoServico(novoEvento.tempoRestante())


    def eventoDeDuracaoMinima(self):

        def tempoRestanteDeEvento(e):
            return e.tempoRestante()
        self.__lista_de_eventos.sort(key=tempoRestanteDeEvento)

        return self.__lista_de_eventos.pop(0) if self.__lista_de_eventos.count > 0 else None


    """ O metodo executarProximoEvento(), como o proprio nome diz, executa o proximo evento,
        com base no que foi "decidido" no metodo eventoDeDuracaoMinima(). """
    def executarProximoEvento(self):

        proximoEvento = self.eventoDeDuracaoMinima()
        tempoRestante = proximoEvento.tempoRestante()
        for evento in self.__lista_de_eventos:
            evento.avancarTempo(tempoRestante)

        tempoAnterior = self.__tempoAtual
        self.__tempoAtual += tempoRestante
        
        self.agregarEmSomatorioPessoasPorTempo(tempoRestante)

        # Tres eventos principais, tres ifs principais.
        if proximoEvento.tipo() == EVENTO_PACOTE_VOZ_CHEGADA:
            self.PacoteEntraNaFilaVoz(proximoEvento.canal(), tempoAnterior, tempoRestante)

        if proximoEvento.tipo() == EVENTO_PACOTE_DADOS_CHEGADA:
            self.PacoteEntraNaFilaDados(tempoAnterior)

        if proximoEvento.tipo() == EVENTO_PACOTE_VOZ_FINALIZADO:
            self.PacoteTerminaServicoNaFilaVoz()

        if proximoEvento.tipo() == EVENTO_PACOTE_DADOS_FINALIZADO:
            self.PacoteTerminaServicoNaFilaDados()
        

    """ Principal metodo da classe Simulacao. Aqui a simulacao eh iniciada. """
    def executarSimulacao(self, seed, lambdaValue, interrupcoes, numeroDePacotesPorRodada, rodadas, hasOutputFile, variavelDeSaida, testeDeCorretude, intervaloDeConfianca):
        self.__lambd = lambdaValue
        self.__interrupcoes = interrupcoes
        self.__numero_de_pacotes_por_fase = numeroDePacotesPorRodada
        self.__numero_de_rodadas = rodadas
        self.__intervaloDeConfianca = intervaloDeConfianca

        self.__output_type = variavelDeSaida
        self.__view = View()
        self.__view.setImprimirEmArquivo(hasOutputFile)

        self.__agendador.setTesteDeCorretude(testeDeCorretude)
        self.__agendador.configurarSemente(seed)

        # Comecamos agendando a chegada do primeiro Pacote no sistema.
        # A partir dela os proximos eventos sao gerados no loop principal da simulacao (mais abaixo).
        for indice in range(30):
            novoEvento = Evento(EVENTO_PACOTE_VOZ_CHEGADA, indice, self.__agendador.agendarChegadaFilaVoz(indice))
            self.__lista_de_eventos.append(novoEvento)
        
        novoEvento = Evento(EVENTO_PACOTE_DADOS_CHEGADA, -1, self.__agendador.agendarChegadaFilaDados(self.__lambd))
        self.__lista_de_eventos.append(novoEvento)


        # Loop principal da simulacao
        while self.__numero_de_rodadas > self.__fase.getID() + 1 or self.__numero_de_pacotes_por_fase > self.__fase.quantidadeDePacotes():
            self.executarProximoEvento()

        if self.__output_type == 0:
            self.__fase.calcularEstatisticas(self.__tempoAtual, self.__view, self.__intervaloDeConfianca, self.__lambd)

        return self.__view.gravarArquivoDeSaida()
        

"""randomNumber e randomNumberDistantFrom sao funcoes de apoio para a funcao main. 
   Cada uma sera explicada com mais detalhes abaixo."""

def randomNumber():
    # Retorna um numero aleatorio entre 0.0 e 1.0
    return random.random()

def randomNumberDistantFrom(numbersList, distance):
    # Retorna um numero aleatorio entre 0.0 e 1.0 que seja distante de todos
    # os numeros de `numbersList` por pelo menos o valor de `distance`.
    newNumber = 0
    while newNumber == 0:
        newNumber = randomNumber()
        for number in numbersList:
            if abs(newNumber - number) < distance:
                newNumber = 0
    return newNumber


app = Flask(__name__)

@app.route("/")
def indexPage():
    return render_template('index.html')

@app.route('/plot/<index>.csv')
def getPlotCsv(index):
    return render_template('/plot/' + index + '.csv')


"""Funcao principal do programa. Interpreta as flags passadas como parametros para configurar
    e executar o simulador."""

@app.route("/simulator", methods=['GET', 'POST'])
def mainFlask():
    lambdaValue = float(request.args.get('lambda', default='0.3'))
    numeroDePacotesPorRodada = int(request.args.get('pacotesporrodada', default='20000'))
    rodadas = int(request.args.get('rodadas', default='100'))
    simulacoes = int(request.args.get('simulacoes', default='1'))
    outputFile = (request.args.get('progressivo', default='false') == 'true')
    interrupcoes = (request.args.get('interrupcoes', default='false') == 'true')
    testeDeCorretude = (request.args.get('teste', default='false') == 'true')
    variavelDeSaida = int(request.args.get('variavel', default='1'))
    intervaloDeConfianca = float(request.args.get('confianca', default='0.95'))
    
    seedsDistance = 0.01
    seedsList = []

    output = ''
    for i in range(simulacoes):
        newSeed = randomNumberDistantFrom(seedsList, seedsDistance)
        sOutput = Simulacao().executarSimulacao(newSeed, lambdaValue, interrupcoes, numeroDePacotesPorRodada, rodadas, outputFile, variavelDeSaida, testeDeCorretude, intervaloDeConfianca)
        seedsList.append(newSeed)
        output = "%s\n%s" % (output, sOutput)
    return output

if __name__ == "__main__":
    # Inicia o Flask se o arquivo do Python for chamado diretamente (o que nunca deve ser o caso)
    app.run(host='0.0.0.0')
