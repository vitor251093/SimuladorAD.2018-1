from controllers.agendador import *
from models.pacote import *
from models.fila import *
from models.fase import *
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

class Simulacao(object):

    def __init__(self):
        self.__mi = None
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

        ### Codigo dos principais eventos da simulacao:
        # 0: Evento chegada de Pacote na fila de voz
        # 1: Evento chegada de Pacote na fila de dados
        # 2: Evento fim de servico de voz
        # 3: Evento fim de servico de dados
        self.__timerChegadaPacoteFilaVozIndice = 0
        self.__timerChegadaPacoteFilaDadosIndice = 1
        self.__timerFimDeServicoPacoteFilaVozIndice = 2
        self.__timerFimDeServicoPacoteFilaDadosIndice = 3

        ### Todos iniciam com valores invalidos: -1
        self.__timerChegadaPacoteFilaVozPorCanal = []
        for indice in range(30):
            self.__timerChegadaPacoteFilaVozPorCanal.append(-1)
        self.__timerChegadaPacoteFilaVoz = -1
        self.__timerChegadaPacoteFilaDados = -1
        self.__timerFimDeServicoPacoteFilaVoz = -1
        self.__timerFimDeServicoPacoteFilaDados = -1

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
            self.__view.imprimir("%f,%d" % (self.__fase.getEsperancaDeT1(), self.__fase.getID()))
        if self.__output_type == 7:
            self.__view.imprimir("%f,%d" % (self.__fase.getEsperancaDeT2(), self.__fase.getID()))
        if self.__output_type == 8:
            self.__view.imprimir("%f,%d" % (self.__fase.getEsperancaDeW1(), self.__fase.getID()))
        if self.__output_type == 9:
            self.__view.imprimir("%f,%d" % (self.__fase.getEsperancaDeW2(), self.__fase.getID()))
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


    def randomNumber(self):
        # Retorna um numero aleatorio entre 0.0 e 1.0
        return random.random()

    def randomNumberDistantFrom(self, numbersList, distance):
        # Retorna um numero aleatorio entre 0.0 e 1.0 que seja distante de todos
        # os numeros de `numbersList` por pelo menos o valor de `distance`.
        newNumber = 0
        while newNumber == 0:
            newNumber = self.randomNumber()
            for number in numbersList:
                if abs(newNumber - number) < distance:
                    newNumber = 0
        return newNumber


    """Evento: Pacote entra na fila de voz
       Com essa funcao realizamos todas as acoes que ocorrem em decorrencia da
       entrada de um Pacote na fila de voz, que sao: se nao houver ninguem na fila de voz,
       levar esse Pacote diretamente ao servico, e interrompe qualquer Pacote
       da fila de dados que possa estar sendo atendido.
        
       Eh aqui tambem que decidimos qual sera a cor de um Pacote. O fim de uma fase/rodada
       tambem ocorre aqui, entao aqui tambem ocorrem os calculos estatisticos que sao 
       chamados ao fim de uma fase/rodada."""

    def PacoteEntraNaFilaVoz (self, canal):
        self.__indice_pacote_atual += 1
        if self.__faseTransienteFinalizada == True and self.__indice_primeiro_pacote_nao_transiente == 0:
            self.__indice_primeiro_pacote_nao_transiente = self.__indice_pacote_atual

        if self.__indice_primeiro_pacote_nao_transiente == 0:
            corDoPacote = -1
        else:
            indiceDaFase = (self.__indice_pacote_atual - self.__indice_primeiro_pacote_nao_transiente)/self.__numero_de_pacotes_por_fase
            if indiceDaFase > self.__fase.getID():
                if self.__output_type == 0:
                    self.__fase.calcularEstatisticas(self.__tempoAtual - self.__timerChegadaPacoteFilaVoz, self.__view, self.__intervaloDeConfianca)

                newSeed = self.randomNumberDistantFrom(self.__seedsList, self.__seedsDistance)
                self.__agendador.configurarSemente(newSeed)
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
                
                self.__timerFimDeServicoPacoteFilaVoz = self.__agendador.agendarTempoDeServicoFilaVoz()
                pacote.setTempoServico(self.__timerFimDeServicoPacoteFilaVoz)
            else:
                if self.__interrupcoes == True:
                    if self.__filaDados.numeroDePessoasNaFila() > 0: # Interrompe individuo da fila de dados
                        PacoteInterrompido = self.__filaDados.PacoteEmAtendimento()
                        PacoteInterrompido.setTempoDecorridoServico(PacoteInterrompido.getTempoDecorridoServico() + self.__timerFimDeServicoPacoteFilaVoz)
                        self.__timerFimDeServicoPacoteFilaDados = -1
                    
                    pacote.setTempoChegadaServico(self.__tempoAtual)
                    #self.adicionarEvento(pacote, "comecou a ser atendido", self.__filaVoz.getID(), self.__tempoAtual)
                    
                    self.__timerFimDeServicoPacoteFilaVoz = self.__agendador.agendarTempoDeServicoFilaVoz()
                    pacote.setTempoServico(self.__timerFimDeServicoPacoteFilaVoz)

        if self.__faseTransienteFinalizada == False:
            self.__timerChegadaPacoteFilaVozPorCanal[pacote.getCanal()] = self.__agendador.agendarChegadaFilaVoz(pacote.getCanal())
            return

        if self.__fase.getID() + 1 == self.__numero_de_rodadas and self.__fase.quantidadeDePacotes() == self.__numero_de_pacotes_por_fase:
            self.__timerChegadaPacoteFilaVozPorCanal[pacote.getCanal()] = -1
        else:    
            self.__timerChegadaPacoteFilaVozPorCanal[pacote.getCanal()] = self.__agendador.agendarChegadaFilaVoz(pacote.getCanal())


    """Evento: Pacote entra na fila de dados
       Com essa funcao realizamos todas as acoes que ocorrem em decorrencia da
       entrada de um Pacote na fila de dados, que sao: se nao houver ninguem na fila 
       de dados nem de voz, levar esse Pacote diretamente ao servico.
        
       Eh aqui tambem que decidimos qual sera a cor de um Pacote. O fim de uma fase/rodada
       tambem ocorre aqui, entao aqui tambem ocorrem os calculos estatisticos que sao 
       chamados ao fim de uma fase/rodada."""

    def PacoteEntraNaFilaDados (self):
        self.__indice_pacote_atual += 1
        if self.__faseTransienteFinalizada == True and self.__indice_primeiro_pacote_nao_transiente == 0:
            self.__indice_primeiro_pacote_nao_transiente = self.__indice_pacote_atual

        if self.__indice_primeiro_pacote_nao_transiente == 0:
            corDoPacote = -1
        else:
            indiceDaFase = (self.__indice_pacote_atual - self.__indice_primeiro_pacote_nao_transiente)/self.__numero_de_pacotes_por_fase
            if indiceDaFase > self.__fase.getID():
                if self.__output_type == 0:
                    self.__fase.calcularEstatisticas(self.__tempoAtual - self.__timerChegadaPacoteFilaVoz, self.__view, self.__intervaloDeConfianca)

                newSeed = self.randomNumberDistantFrom(self.__seedsList, self.__seedsDistance)
                self.__agendador.configurarSemente(newSeed)
                self.__fase = Fase(indiceDaFase, self.__tempoAtual)
            corDoPacote = indiceDaFase

        pacote = Pacote(self.__indice_pacote_atual, self.__tempoAtual, corDoPacote, -1)
        
        self.__fase.adicionarPacote(pacote)
        self.__filaDados.adicionarPacoteAFila(pacote)

        self.adicionarEvento(pacote, "chegou", self.__filaDados.getID(), self.__tempoAtual)
        if self.__filaVoz.numeroDePessoasNaFila() == 0 and self.__filaDados.numeroDePessoasNaFila() == 1:
            pacote.setTempoChegadaServico(self.__tempoAtual)
            #self.adicionarEvento(pacote, "comecou a ser atendido", self.__filaDados.getID(), self.__tempoAtual)
            
            self.__timerFimDeServicoPacoteFilaDados = self.__agendador.agendarTempoDeServicoFilaDados(self.__mi)
            pacote.setTempoServico(self.__timerFimDeServicoPacoteFilaDados)

        if self.__faseTransienteFinalizada == False:
            self.__timerChegadaPacoteFilaDados = self.__agendador.agendarChegadaFilaDados(self.__lambd)
            return

        if self.__fase.getID() + 1 == self.__numero_de_rodadas and self.__fase.quantidadeDePacotes() == self.__numero_de_pacotes_por_fase:
            self.__timerChegadaPacoteFilaDados = -1
        else:    
            self.__timerChegadaPacoteFilaDados = self.__agendador.agendarChegadaFilaDados(self.__lambd)


    """Evento: Fim de servico na fila de voz
       Com essa funcao realizamos todas as acoes que ocorrem em decorrencia do 
       fim de um servico na fila de voz, que sao: tirar o Pacote que concluiu o servico 
       da fila de voz, e colocar em servico o proximo Pacote da fila de voz se houver 
       algum (se nao houver, colocar em servico o proximo Pacote da fila de dados, 
       se houver algum)."""

    def PacoteTerminaServicoNaFilaVoz(self):
        Pacote = self.__filaVoz.retirarPacoteEmAtendimento()
        Pacote.setTempoTerminoServico(self.__tempoAtual)
        self.__timerFimDeServicoPacoteFilaVoz = -1

        self.adicionarEvento(Pacote, "terminou o atendimento", self.__filaVoz.getID(), self.__tempoAtual)

        if self.__filaVoz.numeroDePessoasNaFila() > 0:
            novoPacote = self.__filaVoz.PacoteEmAtendimento()
            novoPacote.setTempoChegadaServico(self.__tempoAtual)
            #self.adicionarEvento(novoPacote, "comecou a ser atendido", self.__filaVoz.getID(), self.__tempoAtual)

            self.__timerFimDeServicoPacoteFilaVoz = self.__agendador.agendarTempoDeServicoFilaVoz()
            novoPacote.setTempoServico(self.__timerFimDeServicoPacoteFilaVoz)
        else:
            self.__timerFimDeServicoPacoteFilaVoz = -1
            if self.__filaDados.numeroDePessoasNaFila() > 0:
                proximoPacote = self.__filaDados.PacoteEmAtendimento()
                if proximoPacote.getTempoDecorridoServico() > 0: 
                    # Pacote da fila de dados que foi interrompido anteriormente retorna
                    self.__timerFimDeServicoPacoteFilaDados = proximoPacote.getTempoServico() - proximoPacote.getTempoDecorridoServico()
                    
                else: 
                    # Pacote da fila de dados eh atendido pela primeira vez
                    proximoPacote.setTempoChegadaServico(self.__tempoAtual)
                    #self.adicionarEvento(proximoPacote, "comecou a ser atendido", self.__filaDados.getID(), self.__tempoAtual)

                    self.__timerFimDeServicoPacoteFilaDados = self.__agendador.agendarTempoDeServicoFilaDados(self.__mi)
                    proximoPacote.setTempoServico(self.__timerFimDeServicoPacoteFilaDados)
            else:
                self.__timerFimDeServicoPacoteFilaDados = -1


    """Evento: Fim de servico na fila de dados
       Com essa funcao realizamos todas as acoes que ocorrem em decorrencia do 
       fim de um servico na fila de dados, que sao: tirar o Pacote que concluiu o servico 
       da fila de dados, e colocar em servico o proximo Pacote da fila de dados (se houver algum)."""

    def PacoteTerminaServicoNaFilaDados(self):
        Pacote = self.__filaDados.retirarPacoteEmAtendimento()
        Pacote.setTempoTerminoServico(self.__tempoAtual)
        self.__timerFimDeServicoPacoteFilaDados = -1

        self.adicionarEvento(Pacote, "terminou o atendimento", self.__filaDados.getID(), self.__tempoAtual)
        
        if self.__interrupcoes == False and self.__filaVoz.numeroDePessoasNaFila() > 0:
            novoPacote = self.__filaVoz.PacoteEmAtendimento()
            novoPacote.setTempoChegadaServico(self.__tempoAtual)
            #self.adicionarEvento(novoPacote, "comecou a ser atendido", self.__filaVoz.getID(), self.__tempoAtual)

            self.__timerFimDeServicoPacoteFilaVoz = self.__agendador.agendarTempoDeServicoFilaVoz()
            novoPacote.setTempoServico(self.__timerFimDeServicoPacoteFilaVoz)
        else:
            if self.__filaDados.numeroDePessoasNaFila() > 0:
                proximoPacote = self.__filaDados.PacoteEmAtendimento()
                proximoPacote.setTempoChegadaServico(self.__tempoAtual)
                #self.adicionarEvento(proximoPacote, "comecou a ser atendido", self.__filaDados.getID(), self.__tempoAtual)
                
                self.__timerFimDeServicoPacoteFilaDados = self.__agendador.agendarTempoDeServicoFilaDados(self.__mi)
                proximoPacote.setTempoServico(self.__timerFimDeServicoPacoteFilaDados)


    """ eventoDeDuracaoMinima() ira cuidar da verificacao de qual evento ocorre antes.
        Temos 3 eventos principais: tempo de chegada na fila de voz, fim de servico 1 e
        fim de servico 2. Aqui verificamos qual acontece antes. """

    def eventoDeDuracaoMinima(self):

        """ Esse metodo avalia qual o proximo evento em que o simulador deve 
            "entrar" baseado naquele que levara menos tempo para ocorrer no 
            instante atual. """


        # Aqui avaliamos quais dos quatro principais eventos da simulacao estao agendados:
        # timerValido1, timerValido2, timerValido3 e timerValido4.

        # Quer dizer que o evento chegada de Pacote na fila de voz esta agendado.
        smallerValidTimer1 = -1
        for indice in range(30):
            timer1 = self.__timerChegadaPacoteFilaVozPorCanal[indice]
            smallerValidTimer1 = timer1 if (timer1 < smallerValidTimer1 or smallerValidTimer1 == -1) and timer1 != -1 else smallerValidTimer1
        self.__timerChegadaPacoteFilaVoz = smallerValidTimer1
        timerValido1 = (self.__timerChegadaPacoteFilaVoz        != -1)

        # Quer dizer que o evento chegada de Pacote na fila de dados esta agendado.
        timerValido2 = (self.__timerChegadaPacoteFilaDados      != -1)

        # Quer dizer que o evento fim do servico 1 esta agendado.
        timerValido3 = (self.__timerFimDeServicoPacoteFilaVoz   != -1)

        # Quer dizer que o evento fim do servico 2 esta agendado.
        timerValido4 = (self.__timerFimDeServicoPacoteFilaDados != -1)


        # Essa eh apenas uma condicional para a unica condicao inexperada:
        # a de que nenhuma acao esteja agendada para acontecer;
        # Esse caso so pode ocorrer se houver uma falha do programa,
        # ja que ele deve ser interrompido logo antes disso ocorrer
        if timerValido1 == False and timerValido2 == False and timerValido3 == False and timerValido4 == False:
            return -1


        # As proximas quatro condicoes remetem aos casos em que apenas um dos quatro
        # eventos esta agendado para ocorrer, entao nao eh necessario
        # compara-los para ver qual ocorrera primeiro:

        if timerValido1 == False and timerValido2 == False and timerValido3 == False:
            return self.__timerFimDeServicoPacoteFilaDadosIndice

        if timerValido1 == False and timerValido2 == False and timerValido4 == False:
            return self.__timerFimDeServicoPacoteFilaVozIndice

        if timerValido1 == False and timerValido3 == False and timerValido4 == False:
            return self.__timerChegadaPacoteFilaDadosIndice

        if timerValido2 == False and timerValido3 == False and timerValido4 == False:
            return self.__timerChegadaPacoteFilaVozIndice


        # As proximas seis condicoes remetem aos casos em que apenas dois dos quatro
        # eventos estao agendados para ocorrer, entao so eh necessario comparar
        # esses dois para ver qual ocorrera primeiro.
        
        if timerValido1 == False and timerValido2 == False:
            return self.__timerFimDeServicoPacoteFilaVozIndice if self.__timerFimDeServicoPacoteFilaVoz <= self.__timerFimDeServicoPacoteFilaDados else self.__timerFimDeServicoPacoteFilaDadosIndice

        if timerValido1 == False and timerValido3 == False:
            return self.__timerChegadaPacoteFilaDadosIndice if self.__timerChegadaPacoteFilaDados <= self.__timerFimDeServicoPacoteFilaDados else self.__timerFimDeServicoPacoteFilaDadosIndice

        if timerValido1 == False and timerValido4 == False:
            return self.__timerChegadaPacoteFilaDadosIndice if self.__timerChegadaPacoteFilaDados < self.__timerFimDeServicoPacoteFilaVoz else self.__timerFimDeServicoPacoteFilaVozIndice

        if timerValido2 == False and timerValido3 == False:
            return self.__timerChegadaPacoteFilaVozIndice if self.__timerChegadaPacoteFilaVoz < self.__timerFimDeServicoPacoteFilaDados else self.__timerFimDeServicoPacoteFilaDadosIndice

        if timerValido2 == False and timerValido4 == False:
            return self.__timerChegadaPacoteFilaVozIndice if self.__timerChegadaPacoteFilaVoz < self.__timerFimDeServicoPacoteFilaVoz else self.__timerFimDeServicoPacoteFilaVozIndice

        if timerValido3 == False and timerValido4 == False:
            return self.__timerChegadaPacoteFilaVozIndice if self.__timerChegadaPacoteFilaVoz <= self.__timerChegadaPacoteFilaDados else self.__timerChegadaPacoteFilaDadosIndice

        
        # As proximas tres condicoes remetem aos casos em que apenas dois dos tres
        # eventos estao agendados para ocorrer, entao so eh necessario comparar
        # esses dois para ver qual ocorrera primeiro:

        if timerValido1 == False:
            lista = [self.__timerChegadaPacoteFilaDados, self.__timerFimDeServicoPacoteFilaVoz, self.__timerFimDeServicoPacoteFilaDados]
            indice = lista.index(min(lista))
            return indice + 1
        
        if timerValido2 == False:
            lista = [self.__timerChegadaPacoteFilaVoz, self.__timerFimDeServicoPacoteFilaVoz, self.__timerFimDeServicoPacoteFilaDados]
            indice = lista.index(min(lista))
            return indice if indice == 0 else indice + 1
        
        if timerValido3 == False:
            lista = [self.__timerChegadaPacoteFilaVoz, self.__timerChegadaPacoteFilaDados, self.__timerFimDeServicoPacoteFilaDados]
            indice = lista.index(min(lista))
            return indice if indice <= 1 else indice + 1
        
        if timerValido4 == False:
            lista = [self.__timerChegadaPacoteFilaVoz, self.__timerChegadaPacoteFilaDados, self.__timerFimDeServicoPacoteFilaVoz]
            indice = lista.index(min(lista))
            return indice
        

        # A proxima condicao remete ao caso em que os tres eventos estao agendados 
        # para ocorrer, entao eh necessario comparar os tres para ver qual ocorrera primeiro:
        
        # Eh criada uma lista com o tempo que falta ate que cada um dos tres eventos 
        # principais agendados ocorra, ordenados em eventos 0, 1, 2 e 3, posicionados
        # nos respectivos indices da lista
        lista = [self.__timerChegadaPacoteFilaVoz, self.__timerChegadaPacoteFilaDados, self.__timerFimDeServicoPacoteFilaVoz, self.__timerFimDeServicoPacoteFilaDados]

        # Com min(lista), retornamos o menor dos tres tempos presentes na lista;
        # com lista.index(), retornamos o indice desse tempo na lista, conseguindo assim 
        # saber qual o evento com o menor tempo faltante para ocorrer
        return lista.index(min(lista))


    """ O metodo executarProximoEvento(), como o proprio nome diz, executa o proximo evento,
        com base no que foi "decidido" no metodo eventoDeDuracaoMinima(). """
    def executarProximoEvento(self):

        proximoTimer = self.eventoDeDuracaoMinima()

        # Tres eventos principais, tres ifs principais.
        if proximoTimer == self.__timerChegadaPacoteFilaVozIndice:
            self.agregarEmSomatorioPessoasPorTempo(self.__timerChegadaPacoteFilaVoz)

            self.__tempoAtual += self.__timerChegadaPacoteFilaVoz
            indiceEscolhido = -1
            for indice in range(30):
                if self.__timerChegadaPacoteFilaVozPorCanal[indice] != -1:
                    self.__timerChegadaPacoteFilaVozPorCanal[indice] -= self.__timerChegadaPacoteFilaVoz
                    if self.__timerChegadaPacoteFilaVozPorCanal[indice] == 0:
                        indiceEscolhido = indice
            if self.__timerChegadaPacoteFilaDados != -1:
                self.__timerChegadaPacoteFilaDados -= self.__timerChegadaPacoteFilaVoz
            if self.__timerFimDeServicoPacoteFilaVoz != -1:
                self.__timerFimDeServicoPacoteFilaVoz -= self.__timerChegadaPacoteFilaVoz
            if self.__timerFimDeServicoPacoteFilaDados != -1:
                self.__timerFimDeServicoPacoteFilaDados -= self.__timerChegadaPacoteFilaVoz
            self.PacoteEntraNaFilaVoz(indiceEscolhido)

        if proximoTimer == self.__timerChegadaPacoteFilaDadosIndice:
            self.agregarEmSomatorioPessoasPorTempo(self.__timerChegadaPacoteFilaDados)

            self.__tempoAtual += self.__timerChegadaPacoteFilaDados
            for indice in range(30):
                if self.__timerChegadaPacoteFilaVozPorCanal[indice] != -1:
                    self.__timerChegadaPacoteFilaVozPorCanal[indice] -= self.__timerChegadaPacoteFilaDados
            if self.__timerFimDeServicoPacoteFilaVoz != -1:
                self.__timerFimDeServicoPacoteFilaVoz -= self.__timerChegadaPacoteFilaDados
            if self.__timerFimDeServicoPacoteFilaDados != -1:
                self.__timerFimDeServicoPacoteFilaDados -= self.__timerChegadaPacoteFilaDados
            self.PacoteEntraNaFilaDados()

        if proximoTimer == self.__timerFimDeServicoPacoteFilaVozIndice:
            self.agregarEmSomatorioPessoasPorTempo(self.__timerFimDeServicoPacoteFilaVoz)
            
            self.__tempoAtual += self.__timerFimDeServicoPacoteFilaVoz
            for indice in range(30):
                if self.__timerChegadaPacoteFilaVozPorCanal[indice] != -1:
                    self.__timerChegadaPacoteFilaVozPorCanal[indice] -= self.__timerFimDeServicoPacoteFilaVoz
            if self.__timerChegadaPacoteFilaDados != -1:
                self.__timerChegadaPacoteFilaDados -= self.__timerFimDeServicoPacoteFilaVoz
            if self.__timerFimDeServicoPacoteFilaDados != -1:
                self.__timerFimDeServicoPacoteFilaDados -= self.__timerFimDeServicoPacoteFilaVoz
            self.PacoteTerminaServicoNaFilaVoz()

        if proximoTimer == self.__timerFimDeServicoPacoteFilaDadosIndice:
            self.agregarEmSomatorioPessoasPorTempo(self.__timerFimDeServicoPacoteFilaDados)
            
            self.__tempoAtual += self.__timerFimDeServicoPacoteFilaDados
            for indice in range(30):
                if self.__timerChegadaPacoteFilaVozPorCanal[indice] != -1:
                    self.__timerChegadaPacoteFilaVozPorCanal[indice] -= self.__timerFimDeServicoPacoteFilaDados
            if self.__timerChegadaPacoteFilaDados != -1:
                self.__timerChegadaPacoteFilaDados -= self.__timerFimDeServicoPacoteFilaDados
            if self.__timerFimDeServicoPacoteFilaVoz != -1:
                self.__timerFimDeServicoPacoteFilaVoz -= self.__timerFimDeServicoPacoteFilaDados
            self.PacoteTerminaServicoNaFilaDados()
        

    """ Principal metodo da classe Simulacao. Aqui a simulacao eh iniciada. """
    def executarSimulacao(self, seed, lambdaValue, miValue, interrupcoes, numeroDePacotesPorRodada, rodadas, hasOutputFile, variavelDeSaida, testeDeCorretude, intervaloDeConfianca):
        self.__lambd = lambdaValue
        self.__mi = miValue
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
            self.__timerChegadaPacoteFilaVozPorCanal[indice] = self.__agendador.agendarChegadaFilaVoz(indice)
        
        self.__timerChegadaPacoteFilaDados = self.__agendador.agendarChegadaFilaDados(self.__lambd)


        # Loop principal da simulacao
        while self.__numero_de_rodadas > self.__fase.getID() + 1 or self.__numero_de_pacotes_por_fase > self.__fase.quantidadeDePacotes():
            self.executarProximoEvento()

        if self.__output_type == 0:
            self.__fase.calcularEstatisticas(self.__tempoAtual, self.__view, self.__intervaloDeConfianca)

        return self.__view.gravarArquivoDeSaida()
        

"""randomNumber, randomNumberDistantFrom, printHelp, safeInt e safeFloat sao funcoes
   de apoio para a funcao main. Cada uma sera explicada com mais detalhes abaixo."""

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

def printHelp():
    # Imprime a ajuda do programa, que eh mostrada quando os parametros sao passados
    # incorretamente ou quando ela eh chamada diretamente via -h ou --help.
    print 'Uso: simulacao.py [args]'
    print 'Opcoes e argumentos:'
    print '-l, --lambda\t\t\tEspecifica o valor de lambda (Padrao: 0.3)'
    print '-m, --mi\t\t\tEspecifica o valor de mi (Padrao: 1.0)'
    print '-c, --Pacotes-por-rodada\tEspecifica o numero de Pacotes por rodada (Padrao: 20000)'
    print '-r, --rodadas\t\t\tEspecifica o numero de rodadas (Padrao: 100)'
    print '-s, --simulacoes\t\tEspecifica o numero de simulacoes (Padrao: 1)'
    print '-t, --teste\t\t\tExecuta o programa em modo de Teste de Corretude'
    print '-o, --csv-output\t\tDefine que a saida deve ser em um arquivo csv no diretorio \'plot\''
    print '-v, --variavel-de-saida\t\tDefine o que sera calculado e impresso pelo programa'
    print '   0:  Imprime as estatisticas de cada fase/rodada (nao parseavel pelo \'plot.py\')'
    print '   1:  Imprime o E[N] durante cada evento'
    print '   2:  Imprime o E[N1] durante cada evento'
    print '   3:  Imprime o E[N2] durante cada evento'
    print '   4:  Imprime o E[Nq1] durante cada evento'
    print '   5:  Imprime o E[Nq2] durante cada evento'
    print '   6:  Imprime o E[T1] durante cada evento'
    print '   7:  Imprime o E[T2] durante cada evento'
    print '   8:  Imprime o E[W1] durante cada evento'
    print '   9:  Imprime o E[W2] durante cada evento'
    print '  10:  Imprime o V(W1) durante cada evento'
    print '  11:  Imprime o V(W2) durante cada evento'

def safeInt(key, stringValue):
    # Converte uma string passada como valor de um parametro para um numero inteiro. 
    # Se a string nao for um numero inteiro, o programa encerra com uma mensagem
    # de erro, alertando que o parametro esta incorreto.
    try:
        return int(stringValue)
    except ValueError:
        print "ERRO: A chave \"%s\" aceita apenas valores inteiros (int)." % (key)
        sys.exit(2)

def safeFloat(key, stringValue):
    # Converte uma string passada como valor de um parametro para um numero float. 
    # Se a string nao for um numero float, o programa encerra com uma mensagem
    # de erro, alertando que o parametro esta incorreto.
    try:
        return float(stringValue)
    except ValueError:
        print "ERRO: A chave \"%s\" aceita apenas valores de ponto flutuante (float)." % (key)
        sys.exit(2)


app = Flask(__name__)

@app.route("/")
def indexPage():
    return render_template('index.html')

@app.route("/js/Chart.bundle.js")
def chartJsPage():
    return render_template('js/Chart.bundle.js')

@app.route('/<string:page_name>/')
def render_static(page_name):
    return render_template('%s.html' % page_name)


"""Funcao principal do programa. Interpreta as flags passadas como parametros para configurar
    e executar o simulador."""

@app.route("/simulator", methods=['GET', 'POST'])
def mainFlask():
    lambdaValue = float(request.args.get('lambda', default='0.3'))
    miValue = float(request.args.get('mi', default='1.0'))
    numeroDePacotesPorRodada = int(request.args.get('pacotesporrodada', default='20000'))
    rodadas = int(request.args.get('rodadas', default='100'))
    simulacoes = int(request.args.get('simulacoes', default='1'))
    outputFile = False
    interrupcoes = (request.args.get('interrupcoes', default='false') == 'true')
    testeDeCorretude = (request.args.get('teste', default='false') == 'true')
    variavelDeSaida = int(request.args.get('variavel', default='1'))
    intervaloDeConfianca = float(request.args.get('confianca', default='0.95'))
    
    seedsDistance = 0.01
    seedsList = []

    output = ''
    for i in range(simulacoes):
        newSeed = randomNumberDistantFrom(seedsList, seedsDistance)
        sOutput = Simulacao().executarSimulacao(newSeed, lambdaValue, miValue, interrupcoes, numeroDePacotesPorRodada, rodadas, outputFile, variavelDeSaida, testeDeCorretude, intervaloDeConfianca)
        seedsList.append(newSeed)
        output = "%s\n%s" % (output, sOutput)
    return output

if __name__ == "__main__":
    # Inicia o Flash se o arquivo do Python for chamado diretamente (o que nunca deve ser o caso)
    app.run(host='0.0.0.0')
