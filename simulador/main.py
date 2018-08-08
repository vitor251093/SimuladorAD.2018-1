from controllers.agendador import *
from controllers.calculadora_ic import *
from controllers.calculadora_voz import *
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
import logging

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
        self.__numero_de_fases = None
        self.__intervaloDeConfianca = None

        self.__seedsDistance = 0.01
        self.__seedsList = []
        self.__view = None
        self.__output_type = None
        
        self.__agendador = Agendador()
        
        self.__pacotes = []
        self.__filaVoz = Fila(1)
        self.__filaDados = Fila(2)
        
        self.__fase = Fase(-1, 0)
        self.__fases = []
        
        self.__tempoAtual = 0.0
        self.__indice_pacote_atual = 0
        self.__indice_primeiro_pacote_nao_transiente = 0
        self.__faseTransienteFinalizada = False

        self.__lista_de_eventos = []

        ### Atributos usados para determinar o fim da fase transiente
        self.__quantidadeDeEventosPorVariancia = 1000
        self.__diferencaAceitavelDasVariancias = 0.002
        self.__eventosDaVariancia1 = []
        self.__duracaoEventosDaVariancia1 = []
        self.__eventosDaVariancia2 = []
        self.__duracaoEventosDaVariancia2 = []
        self.__variancia1 = -1
        self.__variancia2 = -1


    """ Esse metodo apenas fica responsavel por relizar os somatorios
        para o calculo do numero medio de pacotes nas duas filas (E[Ns]). """
    def agregarEmSomatorioPacotesPorTempo (self, tempo):
        self.__fase.inserirNumeroDePacotesPorTempoNaFilaVoz(self.__filaVoz.numeroDePacotesNaFila(), tempo)
        self.__fase.inserirNumeroDePacotesPorTempoNaFilaDados(self.__filaDados.numeroDePacotesNaFila(), tempo)

        if self.__filaVoz.numeroDePacotesNaFila() > 0:
            self.__fase.inserirNumeroDePacotesPorTempoNaFilaEsperaVoz(self.__filaVoz.numeroDePacotesNaFila() - 1, tempo)
        else:
            self.__fase.inserirNumeroDePacotesPorTempoNaFilaEsperaVoz(0, tempo)

        if self.__filaDados.numeroDePacotesNaFila() > 0:
            self.__fase.inserirNumeroDePacotesPorTempoNaFilaEsperaDados(self.__filaDados.numeroDePacotesNaFila() - 1, tempo)
        else: 
            self.__fase.inserirNumeroDePacotesPorTempoNaFilaEsperaDados(0, tempo)

    def adicionarEvento (self, Pacote, evento, fila, momento):
        ENt = 0

        if self.__output_type == 1:
            ENt = self.__fase.getEsperancaDeN(momento)
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
        if self.__output_type == 12:
            tipo = ("de voz de canal %d" % (Pacote.getCanal() + 1)) if Pacote.getCanal() != -1 else "de dados"
            self.__view.imprimir("%f: Pacote %s (%d) de grupo %d %s na fila %d" % (momento, tipo, Pacote.getID(), Pacote.getIndiceDaCor(), evento, fila))

        
        if self.__faseTransienteFinalizada == True:
            self.__eventosDaVariancia1 = []
            self.__duracaoEventosDaVariancia1 = []
            self.__eventosDaVariancia2 = []
            self.__duracaoEventosDaVariancia2 = []
            return

        if ENt == 0:
            ENt = self.__fase.getEsperancaDeN(momento)


        # Daqui para baixo, essa funcao realiza o calculo que define quando
        # a fase transiente acaba. Comparando a variancia das ultimas 1000
        # amostras de E[N] com a variancia das 1000 amostras anteriores,
        # o fim da fase transiente eh caracterizado quando se encontram
        # duas variancias que variam apenas em 0,0000002.

        if len(self.__eventosDaVariancia1) < self.__quantidadeDeEventosPorVariancia:
            self.__eventosDaVariancia1.append(ENt)
            self.__duracaoEventosDaVariancia1.append(momento)

            if len(self.__eventosDaVariancia1) == self.__quantidadeDeEventosPorVariancia:
                media1 = 0
                duracao1 = 0
                for indiceEvento in range(self.__quantidadeDeEventosPorVariancia):
                    media1 += self.__eventosDaVariancia1[indiceEvento]*self.__duracaoEventosDaVariancia1[indiceEvento]
                    duracao1 += self.__duracaoEventosDaVariancia1[indiceEvento]
                media1 /= duracao1
                
                self.__variancia1 = 0
                for indiceEvento in range(self.__quantidadeDeEventosPorVariancia):
                    self.__variancia1 += (self.__eventosDaVariancia1[indiceEvento] - media1)**2
                self.__variancia1 /= (self.__quantidadeDeEventosPorVariancia - 1)

            return

        if len(self.__eventosDaVariancia2) < self.__quantidadeDeEventosPorVariancia:
            self.__eventosDaVariancia2.append(ENt)
            self.__duracaoEventosDaVariancia2.append(momento)

        if len(self.__eventosDaVariancia2) == self.__quantidadeDeEventosPorVariancia:
            media2 = 0
            duracao2 = 0
            for indiceEvento in range(self.__quantidadeDeEventosPorVariancia):
                media2 += self.__eventosDaVariancia2[indiceEvento]*self.__duracaoEventosDaVariancia2[indiceEvento]
                duracao2 += self.__duracaoEventosDaVariancia2[indiceEvento]
            media2 /= duracao2
            
            self.__variancia2 = 0
            for indiceEvento in range(self.__quantidadeDeEventosPorVariancia):
                self.__variancia2 += (self.__eventosDaVariancia2[indiceEvento] - media2)**2
            self.__variancia2 /= (self.__quantidadeDeEventosPorVariancia - 1)

            if abs(self.__variancia1 - self.__variancia2) < self.__diferencaAceitavelDasVariancias:
                print "Fase transiente finalizada"
                self.__faseTransienteFinalizada = True
                return
            
            self.__eventosDaVariancia1 = self.__eventosDaVariancia2
            self.__duracaoEventosDaVariancia1 = self.__duracaoEventosDaVariancia2
            self.__variancia1 = self.__variancia2
            self.__eventosDaVariancia2 = []
            self.__duracaoEventosDaVariancia2 = []
            self.__variancia2 = -1


    def corDeNovoPacote(self, tempoAnterior):
        self.__indice_pacote_atual += 1
        if self.__faseTransienteFinalizada == True and self.__indice_primeiro_pacote_nao_transiente == 0:
            self.__indice_primeiro_pacote_nao_transiente = self.__indice_pacote_atual

        # Enquanto o primeiro pacote nao transiente nao eh encontrado, ainda
        # estamos na fase transiente, e por isso a cor eh -1
        if self.__indice_primeiro_pacote_nao_transiente == 0: 
            corDoPacote = -1
        else:
            # Como o numero de pacotes por fase nao-transiente eh deterministico, ao subtrair o indice
            # atual pelo indice do primeiro pacote nao-transiente e dividir pelo numero de pacotes
            # por fase nos traz o indice da fase, iniciando em zero
            indiceDaFase = (self.__indice_pacote_atual - self.__indice_primeiro_pacote_nao_transiente)/self.__numero_de_pacotes_por_fase

            if indiceDaFase > self.__fase.getID():
                # A entrada nesse 'if' indice o fim de uma fase e o inicio de uma nova
                if self.__output_type == 0 and self.__fase.getID() != -1:
                    self.__fase.calcularEstatisticas(tempoAnterior, self.__view, self.__intervaloDeConfianca, self.__lambd)

                print "Iniciada rodada %d" % (indiceDaFase + 1)
                self.__fase = Fase(indiceDaFase, self.__tempoAtual)
                self.__fases.append(self.__fase)

            corDoPacote = indiceDaFase
        
        return corDoPacote

    """Evento: Pacote entra na fila de voz
       Com essa funcao realizamos todas as acoes que ocorrem em decorrencia da
       entrada de um Pacote na fila de voz, que sao: se nao houver ninguem na fila de voz,
       levar esse Pacote diretamente ao servico, e interrompe qualquer Pacote
       da fila de dados que possa estar sendo atendido.
        
       Eh aqui tambem que decidimos qual sera a cor de um Pacote. O fim de uma fase/rodada
       tambem ocorre aqui, entao aqui tambem ocorrem os calculos estatisticos que sao 
       chamados ao fim de uma fase/rodada."""

    def PacoteEntraNaFilaVoz(self, canal, tempoAnterior, tempoAvancado, indiceEmCanal, servico):
        if canal == -1:
            print "ERRO: O tempo deslocado nao se aplica a nenhuma das esperas de canais de voz."
            sys.exit(2)

        corDoPacote = self.corDeNovoPacote(tempoAnterior)
        pacote = Pacote(self.__indice_pacote_atual, self.__tempoAtual, corDoPacote, canal, indiceEmCanal, servico) 
        
        self.__fase.adicionarPacote(pacote)
        self.__filaVoz.adicionarPacoteAFila(pacote)

        self.adicionarEvento(pacote, "chegou", self.__filaVoz.getID(), self.__tempoAtual)
        if self.__filaVoz.numeroDePacotesNaFila() == 1: # So o atual se encontra na fila
            if self.__interrupcoes == True and self.__filaDados.numeroDePacotesNaFila() > 0: 
                # Interrompe individuo da fila de dados em servico
                PacoteInterrompido = self.__filaDados.PacoteEmAtendimento()
                PacoteInterrompido.setTempoDecorridoServico(PacoteInterrompido.getTempoDecorridoServico() + tempoAvancado)

                # Removendo evento de completude do individuo interrompido
                for eventoIndex in range(len(self.__lista_de_eventos)):
                    if len(self.__lista_de_eventos) > eventoIndex and self.__lista_de_eventos[eventoIndex].tipo() == EVENTO_PACOTE_DADOS_FINALIZADO:
                        self.__lista_de_eventos.pop(eventoIndex)
                        eventoIndex -= 1

            if self.__interrupcoes == True or self.__filaDados.numeroDePacotesNaFila() == 0:
                pacote.setTempoChegadaServico(self.__tempoAtual)
                
                tempoAAvancar = self.__agendador.agendarTempoDeServicoFilaVoz(pacote.getCanal(),pacote.getServico(),self.__filaVoz)
                novoEvento = Evento(EVENTO_PACOTE_VOZ_FINALIZADO, pacote.getCanal(), tempoAAvancar)
                self.__lista_de_eventos.append(novoEvento)
                pacote.setTempoServico(tempoAAvancar)

        for subcanal in range(30):
            if self.__agendador.deveAgendarChegadaFilaVoz(subcanal,pacote.getServico(),self.__filaVoz):
                servico, indice, tempoAAvancar = self.__agendador.agendarChegadaFilaVoz(subcanal)
                if tempoAAvancar != None:
                    novoEvento = Evento(EVENTO_PACOTE_VOZ_CHEGADA, subcanal, tempoAAvancar, indice, servico)
                    self.__lista_de_eventos.append(novoEvento)

        if self.__faseTransienteFinalizada == False:
            if self.__agendador.deveAgendarChegadaFilaVoz(pacote.getCanal(),pacote.getServico(),self.__filaVoz):
                servico, indice, tempoAAvancar = self.__agendador.agendarChegadaFilaVoz(pacote.getCanal())
                if tempoAAvancar != None:
                    novoEvento = Evento(EVENTO_PACOTE_VOZ_CHEGADA, pacote.getCanal(), tempoAAvancar, indice, servico)
                    self.__lista_de_eventos.append(novoEvento)
            return

        if self.__fase.getID() + 1 != self.__numero_de_fases or self.__fase.quantidadeDePacotes() != self.__numero_de_pacotes_por_fase:
            if self.__agendador.deveAgendarChegadaFilaVoz(pacote.getCanal(),pacote.getServico(),self.__filaVoz):
                servico, indice, tempoAAvancar = self.__agendador.agendarChegadaFilaVoz(pacote.getCanal())
                if tempoAAvancar != None:
                    novoEvento = Evento(EVENTO_PACOTE_VOZ_CHEGADA, pacote.getCanal(), tempoAAvancar, indice, servico)
                    self.__lista_de_eventos.append(novoEvento)


    """Evento: Pacote entra na fila de dados
       Com essa funcao realizamos todas as acoes que ocorrem em decorrencia da
       entrada de um Pacote na fila de dados, que sao: se nao houver ninguem na fila 
       de dados nem de voz, levar esse Pacote diretamente ao servico.
        
       Eh aqui tambem que decidimos qual sera a cor de um Pacote. O fim de uma fase/rodada
       tambem ocorre aqui, entao aqui tambem ocorrem os calculos estatisticos que sao 
       chamados ao fim de uma fase/rodada."""

    def PacoteEntraNaFilaDados (self, tempoAnterior):
        corDoPacote = self.corDeNovoPacote(tempoAnterior)
        pacote = Pacote(self.__indice_pacote_atual, self.__tempoAtual, corDoPacote)
        
        self.__fase.adicionarPacote(pacote)
        self.__filaDados.adicionarPacoteAFila(pacote)

        self.adicionarEvento(pacote, "chegou", self.__filaDados.getID(), self.__tempoAtual)
        if self.__filaVoz.numeroDePacotesNaFila() == 0 and self.__filaDados.numeroDePacotesNaFila() == 1:
            pacote.setTempoChegadaServico(self.__tempoAtual)
            
            tempoAAvancar = self.__agendador.agendarTempoDeServicoFilaDados()
            novoEvento = Evento(EVENTO_PACOTE_DADOS_FINALIZADO, pacote.getCanal(), tempoAAvancar)
            self.__lista_de_eventos.append(novoEvento)
            pacote.setTempoServico(novoEvento.tempoRestante())

        if self.__faseTransienteFinalizada == False:
            tempoAAvancar = self.__agendador.agendarChegadaFilaDados(self.__lambd)
            if tempoAAvancar != None:
                novoEvento = Evento(EVENTO_PACOTE_DADOS_CHEGADA, pacote.getCanal(), tempoAAvancar)
                self.__lista_de_eventos.append(novoEvento)
            return

        if self.__fase.getID() + 1 != self.__numero_de_fases:
            tempoAAvancar = self.__agendador.agendarChegadaFilaDados(self.__lambd)
            if tempoAAvancar != None:
                novoEvento = Evento(EVENTO_PACOTE_DADOS_CHEGADA, pacote.getCanal(), tempoAAvancar)
                self.__lista_de_eventos.append(novoEvento)
            return

        if self.__fase.quantidadeDePacotes() != self.__numero_de_pacotes_por_fase:
            tempoAAvancar = self.__agendador.agendarChegadaFilaDados(self.__lambd)
            if tempoAAvancar != None:
                novoEvento = Evento(EVENTO_PACOTE_DADOS_CHEGADA, pacote.getCanal(), tempoAAvancar)
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

        if self.__filaVoz.numeroDePacotesNaFila() > 0:
            novoPacote = self.__filaVoz.PacoteEmAtendimento()
            novoPacote.setTempoChegadaServico(self.__tempoAtual)
            
            tempoAAvancar = self.__agendador.agendarTempoDeServicoFilaVoz(novoPacote.getCanal(),novoPacote.getServico(),self.__filaVoz)
            novoEvento = Evento(EVENTO_PACOTE_VOZ_FINALIZADO, novoPacote.getCanal(), tempoAAvancar)
            self.__lista_de_eventos.append(novoEvento)
            novoPacote.setTempoServico(novoEvento.tempoRestante())
        else:
            if self.__filaDados.numeroDePacotesNaFila() > 0:
                proximoPacote = self.__filaDados.PacoteEmAtendimento()
                if proximoPacote.getTempoDecorridoServico() > 0: 
                    # Pacote da fila de dados que foi interrompido anteriormente retorna
                    tempoAAvancar = proximoPacote.getTempoServico() - proximoPacote.getTempoDecorridoServico()
                    novoEvento = Evento(EVENTO_PACOTE_DADOS_FINALIZADO, proximoPacote.getCanal(), tempoAAvancar)
                    self.__lista_de_eventos.append(novoEvento)
                    
                else: 
                    # Pacote da fila de dados eh atendido pela primeira vez
                    proximoPacote.setTempoChegadaServico(self.__tempoAtual)
                    
                    tempoAAvancar = self.__agendador.agendarTempoDeServicoFilaDados()
                    novoEvento = Evento(EVENTO_PACOTE_DADOS_FINALIZADO, proximoPacote.getCanal(), tempoAAvancar)
                    self.__lista_de_eventos.append(novoEvento)
                    proximoPacote.setTempoServico(novoEvento.tempoRestante())

        for subcanal in range(30):
            if self.__agendador.deveAgendarChegadaFilaVoz(subcanal,Pacote.getServico(),self.__filaVoz):
                servico, indice, tempoAAvancar = self.__agendador.agendarChegadaFilaVoz(subcanal)
                if tempoAAvancar != None:
                    novoEvento = Evento(EVENTO_PACOTE_VOZ_CHEGADA, subcanal, tempoAAvancar, indice, servico)
                    self.__lista_de_eventos.append(novoEvento)


    """Evento: Fim de servico na fila de dados
       Com essa funcao realizamos todas as acoes que ocorrem em decorrencia do 
       fim de um servico na fila de dados, que sao: tirar o Pacote que concluiu o servico 
       da fila de dados, e colocar em servico o proximo Pacote da fila de dados (se houver algum)."""

    def PacoteTerminaServicoNaFilaDados(self):
        Pacote = self.__filaDados.retirarPacoteEmAtendimento()
        Pacote.setTempoTerminoServico(self.__tempoAtual)
        
        self.adicionarEvento(Pacote, "terminou o atendimento", self.__filaDados.getID(), self.__tempoAtual)
        
        if self.__interrupcoes == False and self.__filaVoz.numeroDePacotesNaFila() > 0:
            novoPacote = self.__filaVoz.PacoteEmAtendimento()
            novoPacote.setTempoChegadaServico(self.__tempoAtual)
            
            tempoAAvancar = self.__agendador.agendarTempoDeServicoFilaVoz(novoPacote.getCanal(),novoPacote.getServico(),self.__filaVoz)
            novoEvento = Evento(EVENTO_PACOTE_VOZ_FINALIZADO, novoPacote.getCanal(), tempoAAvancar)
            self.__lista_de_eventos.append(novoEvento)
            novoPacote.setTempoServico(novoEvento.tempoRestante())
        else:
            if self.__filaDados.numeroDePacotesNaFila() > 0:
                proximoPacote = self.__filaDados.PacoteEmAtendimento()
                proximoPacote.setTempoChegadaServico(self.__tempoAtual)
                
                tempoAAvancar = self.__agendador.agendarTempoDeServicoFilaDados()
                novoEvento = Evento(EVENTO_PACOTE_DADOS_FINALIZADO, proximoPacote.getCanal(), tempoAAvancar)
                self.__lista_de_eventos.append(novoEvento)
                proximoPacote.setTempoServico(novoEvento.tempoRestante())

        for subcanal in range(30):
            if self.__agendador.deveAgendarChegadaFilaVoz(subcanal,Pacote.getServico(),self.__filaVoz):
                servico, indice, tempoAAvancar = self.__agendador.agendarChegadaFilaVoz(subcanal)
                if tempoAAvancar != None:
                    novoEvento = Evento(EVENTO_PACOTE_VOZ_CHEGADA, subcanal, tempoAAvancar, indice, servico)
                    self.__lista_de_eventos.append(novoEvento)


    def eventoDeDuracaoMinima(self):

        def tempoRestanteDeEvento(e):
            return e.tempoRestante()
        self.__lista_de_eventos.sort(key=tempoRestanteDeEvento)

        return self.__lista_de_eventos.pop(0) if len(self.__lista_de_eventos) > 0 else None


    """ O metodo executarProximoEvento(), como o proprio nome diz, executa o proximo evento,
        com base no que foi "decidido" no metodo eventoDeDuracaoMinima(). """
    def executarProximoEvento(self):

        proximoEvento = self.eventoDeDuracaoMinima()
        tempoRestante = proximoEvento.tempoRestante()
        for evento in self.__lista_de_eventos:
            evento.avancarTempo(tempoRestante)

        tempoAnterior = self.__tempoAtual
        self.__tempoAtual += tempoRestante
        
        self.agregarEmSomatorioPacotesPorTempo(tempoRestante)

        # Tres eventos principais, tres ifs principais.
        if proximoEvento.tipo() == EVENTO_PACOTE_VOZ_CHEGADA:
            self.PacoteEntraNaFilaVoz(proximoEvento.canal(), tempoAnterior, tempoRestante, proximoEvento.indiceEmCanal(), proximoEvento.servico())

        if proximoEvento.tipo() == EVENTO_PACOTE_DADOS_CHEGADA:
            self.PacoteEntraNaFilaDados(tempoAnterior)

        if proximoEvento.tipo() == EVENTO_PACOTE_VOZ_FINALIZADO:
            self.PacoteTerminaServicoNaFilaVoz()

        if proximoEvento.tipo() == EVENTO_PACOTE_DADOS_FINALIZADO:
            self.PacoteTerminaServicoNaFilaDados()
        
    def media(self, listaOriginal):
        value = 0
        count = 0
        lista = list(listaOriginal) # Transformando generator em lista
        for item in lista:
            if item != None:
                value += item
                count += 1
        if count == 0:
            return -1
        return value / count
    
    """ Principal metodo da classe Simulacao. Aqui a simulacao eh iniciada. """
    def executarSimulacao(self, seed, lambdaValue, transienteAmostras, transienteMargem, interrupcoes, numeroDePacotesPorFase, fases, hasOutputFile, variavelDeSaida, testeDeCorretude, intervaloDeConfianca, desabilitarvoz, desabilitardados):
        self.__lambd = lambdaValue
        self.__interrupcoes = interrupcoes
        self.__numero_de_pacotes_por_fase = numeroDePacotesPorFase
        self.__numero_de_fases = fases
        self.__intervaloDeConfianca = intervaloDeConfianca

        self.__quantidadeDeEventosPorVariancia = transienteAmostras
        self.__diferencaAceitavelDasVariancias = transienteMargem

        self.__output_type = variavelDeSaida
        self.__view = View()
        self.__view.setImprimirEmArquivo(hasOutputFile)

        self.__agendador.setTesteDeCorretude(testeDeCorretude)
        self.__agendador.setDesabilitarVoz(desabilitarvoz)
        self.__agendador.setDesabilitarDados(desabilitardados)

        self.__agendador.configurarSemente(seed)

        # Comecamos agendando a chegada do primeiro Pacote no sistema.
        # A partir dela os proximos eventos sao gerados no loop principal da simulacao (mais abaixo).

        if desabilitarvoz == False:
            for canal in range(30):
                servico, indice, tempoAAvancar = self.__agendador.agendarChegadaFilaVoz(canal)
                if tempoAAvancar != None:
                    novoEvento = Evento(EVENTO_PACOTE_VOZ_CHEGADA, canal, tempoAAvancar, indice, servico)
                    self.__lista_de_eventos.append(novoEvento)
        
        if desabilitardados == False:
            tempoAAvancar = self.__agendador.agendarChegadaFilaDados(self.__lambd)
            if tempoAAvancar != None:
                novoEvento = Evento(EVENTO_PACOTE_DADOS_CHEGADA, -1, tempoAAvancar)
                self.__lista_de_eventos.append(novoEvento)


        # Loop principal da simulacao
        while self.__numero_de_fases > self.__fase.getID() + 1 or self.__numero_de_pacotes_por_fase > self.__fase.quantidadeDePacotes():
            self.executarProximoEvento()

        if self.__output_type == 0:
            self.__fase.calcularEstatisticas(self.__tempoAtual, self.__view, self.__intervaloDeConfianca, self.__lambd)
            
            tamanho = len(self.__fases)
            p = (self.media((f.EX1() for f in self.__fases))*lambdaValue)/1000
            calculadora = CalculadoraIC(self.__intervaloDeConfianca)
            EDeltaK, EDelta, VDeltaK, VDelta = CalculadoraVoz.esperancaEVarianciaDaVarianciaDeChegadasDePacotesDeVoz(self.__fases)
            
            self.__view.imprimir("p (Dados):      %f" % (p))
            self.__view.imprimir("Fila e estavel: %s" % ("Sim" if p <= 0.8314 else "Nao"))
            self.__view.imprimir("")
            self.__view.imprimir("E[T]     (Dados):  %f" % (self.media((f.ET1()  for f in self.__fases))))
            self.__view.imprimir("IC E[T]  (Dados):  %f - %f" % (calculadora.intervaloDeConfiancaDeAmostras((f.ET1()  for f in self.__fases),tamanho)))
            self.__view.imprimir("E[W]     (Dados):  %f" % (self.media((f.EW1()  for f in self.__fases))))
            self.__view.imprimir("IC E[W]  (Dados):  %f - %f" % (calculadora.intervaloDeConfiancaDeAmostras((f.EW1()  for f in self.__fases),tamanho)))
            self.__view.imprimir("E[X]     (Dados):  %f" % (self.media((f.EX1()  for f in self.__fases))))
            self.__view.imprimir("IC E[X]  (Dados):  %f - %f" % (calculadora.intervaloDeConfiancaDeAmostras((f.EX1()  for f in self.__fases),tamanho)))
            self.__view.imprimir("E[Nq]    (Dados):  %f" % (self.media((f.ENq1() for f in self.__fases))))
            self.__view.imprimir("IC E[Nq] (Dados):  %f - %f" % (calculadora.intervaloDeConfiancaDeAmostras((f.ENq1() for f in self.__fases),tamanho)))
            self.__view.imprimir("")
            self.__view.imprimir("E[T]     (Voz): %f" % (self.media((f.ET2()  for f in self.__fases))))
            self.__view.imprimir("IC E[T]  (Voz): %f - %f" % (calculadora.intervaloDeConfiancaDeAmostras((f.ET2()  for f in self.__fases),tamanho)))
            self.__view.imprimir("E[W]     (Voz): %f" % (self.media((f.EW2()  for f in self.__fases))))
            self.__view.imprimir("IC E[W]  (Voz): %f - %f" % (calculadora.intervaloDeConfiancaDeAmostras((f.EW2()  for f in self.__fases),tamanho)))
            self.__view.imprimir("E[Nq]    (Voz): %f" % (self.media((f.ENq2() for f in self.__fases))))
            self.__view.imprimir("IC E[Nq] (Voz): %f - %f" % (calculadora.intervaloDeConfiancaDeAmostras((f.ENq2() for f in self.__fases),tamanho)))
            self.__view.imprimir("")
            self.__view.imprimir("Inicio da transmissao de pacotes de voz:")
            self.__view.imprimir("E[Delta]:     %f" % (EDelta))
            self.__view.imprimir("IC E[Delta]:  %f - %f" % (calculadora.intervaloDeConfiancaDeAmostras(EDeltaK, len(EDeltaK))))
            self.__view.imprimir("V(Delta):     %f" % (VDelta))
            self.__view.imprimir("IC V(Delta):  %f - %f" % (calculadora.intervaloDeConfiancaDeAmostras(VDeltaK, len(VDeltaK))))
            self.__view.imprimir("")
            self.__view.imprimir("E[X]    (Voz):   %f" % (self.media((f.EX2()  for f in self.__fases))))
            self.__view.imprimir("IC E[X] (Voz):   %f - %f" % (calculadora.intervaloDeConfiancaDeAmostras((f.EX2()  for f in self.__fases),tamanho)))
            self.__view.imprimir("E[N]    (Dados): %f" % (self.media((f.EN1()  for f in self.__fases))))
            self.__view.imprimir("IC E[N] (Dados): %f - %f" % (calculadora.intervaloDeConfiancaDeAmostras((f.EN1()  for f in self.__fases),tamanho)))
            self.__view.imprimir("V(W)    (Dados): %f" % (self.media((f.EVW1() for f in self.__fases))))
            self.__view.imprimir("IC V(W) (Dados): %f - %f" % (calculadora.intervaloDeConfiancaDeAmostras((f.EVW1() for f in self.__fases),tamanho)))
            self.__view.imprimir("E[N]    (Voz):   %f" % (self.media((f.EN2()  for f in self.__fases))))
            self.__view.imprimir("IC E[N] (Voz):   %f - %f" % (calculadora.intervaloDeConfiancaDeAmostras((f.EN2()  for f in self.__fases),tamanho)))
            self.__view.imprimir("V(W)    (Voz):   %f" % (self.media((f.EVW2() for f in self.__fases))))
            self.__view.imprimir("IC V(W) (Voz):   %f - %f" % (calculadora.intervaloDeConfiancaDeAmostras((f.EVW2() for f in self.__fases),tamanho)))

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

handler = logging.FileHandler('/simulador/templates/app.log')  # errors logged to this file
handler.setLevel(logging.ERROR)  # only log errors and above
app.logger.addHandler(handler)


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
    numeroDePacotesPorRodada = int(request.args.get('pacotesporrodada', default='20000'))
    lambdaValue          = float(request.args.get('lambda',       default='0.3'))
    rodadas              = int(  request.args.get('rodadas',      default='100'))
    simulacoes           = int(  request.args.get('simulacoes',   default='1'))
    outputFile           = (     request.args.get('progressivo',  default='false') == 'true')
    interrupcoes         = (     request.args.get('interrupcoes', default='false') == 'true')
    testeDeCorretude     = (     request.args.get('teste',        default='false') == 'true')
    variavelDeSaida      = int(  request.args.get('variavel',     default='1'))
    intervaloDeConfianca = float(request.args.get('confianca',    default='0.95'))
    sementeForcada       = int(  request.args.get('semente',      default='0'))
    transienteAmostras   = int(  request.args.get('transamostra', default='1000'))
    transienteMargem     = float(request.args.get('transmargem',  default='0.002'))

    desabilitarvoz   = (request.args.get('desabilitarvoz',   default='false') == 'true')
    desabilitardados = (request.args.get('desabilitardados', default='false') == 'true')

    seedsDistance = 0.01
    seedsList = []

    output = ''
    for i in range(simulacoes):
        tempSeed = randomNumberDistantFrom(seedsList, seedsDistance)
        newSeed = int(tempSeed*1000000000) if sementeForcada == 0 else sementeForcada
        sOutput = Simulacao().executarSimulacao(newSeed, lambdaValue, transienteAmostras, transienteMargem, interrupcoes, numeroDePacotesPorRodada, rodadas, outputFile, variavelDeSaida, testeDeCorretude, intervaloDeConfianca, desabilitarvoz, desabilitardados)
        seedsList.append(tempSeed)
        output = "%s\n%s" % (output, sOutput)
    return output

if __name__ == "__main__":
    # Inicia o Flask se o arquivo do Python for chamado diretamente (o que nunca deve ser o caso)
    app.run(host='0.0.0.0')
