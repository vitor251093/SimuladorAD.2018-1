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
import timeit
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
        self.__numero_de_eventos_voz_por_fase = None
        self.__numero_de_eventos_dados_por_fase = None
        self.__numero_de_fases = None
        self.__intervaloDeConfianca = None

        self.__seedsDistance = 0.01
        self.__seedsList = []
        self.__view = None
        self.__output_type = None
        
        self.__agendador = Agendador()
        
        self.__numero_de_pacotes_que_passaram_pelo_sistema = 0
        self.__filaVoz = Fila(1)
        self.__filaDados = Fila(2)
        
        self.__fase = Fase(-1, 0)
        self.__fases = []
        
        self.__tempoAtual = 0.0
        self.__indice_pacote_atual = 0
        self.__indice_primeiro_pacote_nao_transiente = 0
        self.__faseTransienteFinalizada = False

        self.__lista_de_eventos = []

        self.__EN_history = []
        self.__EN1_history = []
        self.__EN2_history = []
        self.__ENq1_history = []
        self.__ENq2_history = []
        self.__EX1_history = []
        self.__ET1_history = []
        self.__ET2_history = []
        self.__EW1_history = []
        self.__EW2_history = []
        self.__VW1_history = []
        self.__VW2_history = []

        self.__possivel_terminar_sob_demanda = False
        self.__forcar_termino = False

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
        # E[N]
        self.__fase.inserirNumeroDePacotesPorTempoNaFilaVoz(self.__filaVoz.numeroDePacotesNaFila(), tempo)
        self.__fase.inserirNumeroDePacotesPorTempoNaFilaDados(self.__filaDados.numeroDePacotesNaFila(), tempo)

        # E[Nq]
        if self.__filaVoz.numeroDePacotesNaFila() > 0:
            self.__fase.inserirNumeroDePacotesPorTempoNaFilaEsperaVoz(self.__filaVoz.numeroDePacotesNaFila() - 1, tempo)
        else:
            self.__fase.inserirNumeroDePacotesPorTempoNaFilaEsperaVoz(0, tempo)

        if self.__filaDados.numeroDePacotesNaFila() > 0:
            self.__fase.inserirNumeroDePacotesPorTempoNaFilaEsperaDados(self.__filaDados.numeroDePacotesNaFila() - 1, tempo)
        else: 
            self.__fase.inserirNumeroDePacotesPorTempoNaFilaEsperaDados(0, tempo)

    def adicionarEvento(self, pacote, evento, fila, momento):
        declararFinal = False
        diferencaDeclararFinal = 0.0001
        requisitosTermino = (self.__fase.quantidadeDeEventosVoz >= self.__numero_de_eventos_voz_por_fase and self.__fase.quantidadeDeEventosDados >= self.__numero_de_eventos_dados_por_fase and self.__faseTransienteFinalizada)
        if self.__output_type != 0 and ((self.__numero_de_fases > 1 and requisitosTermino) or self.__numero_de_fases == 1):
            calculadora = CalculadoraIC(self.__intervaloDeConfianca)

            if self.__output_type == 1:
                newValue = self.__fase.getEsperancaDeN(momento)
                if len(self.__EN_history) == 0 or abs(self.__EN_history[len(self.__EN_history)-1] - newValue) != 0:
                    mediaold,iclold,ichold,statusold = calculadora.intervaloDeConfiancaDeAmostras(self.__EN_history,len(self.__EN_history))
                    self.__EN_history.append(newValue)
                    media,icl,ich,status = calculadora.intervaloDeConfiancaDeAmostras(self.__EN_history,len(self.__EN_history))
                    if len(self.__EN_history) > 0:
                        declararFinal = abs(mediaold - media) < diferencaDeclararFinal
                    if self.__numero_de_fases > 1 and requisitosTermino:
                        newValue = media
                    self.__view.imprimir("%f,%f,%f,%d" % (newValue,icl,ich,self.__fase.id))

            elif self.__output_type == 2:
                newValue = self.__fase.getEsperancaDeN1(momento)
                if len(self.__EN1_history) == 0 or abs(self.__EN1_history[len(self.__EN1_history)-1] - newValue) != 0:
                    mediaold,iclold,ichold,statusold = calculadora.intervaloDeConfiancaDeAmostras(self.__EN1_history,len(self.__EN1_history))
                    self.__EN1_history.append(newValue)
                    media,icl,ich,status = calculadora.intervaloDeConfiancaDeAmostras(self.__EN1_history,len(self.__EN1_history))
                    if len(self.__EN1_history) > 0:
                        declararFinal = abs(mediaold - media) < diferencaDeclararFinal
                    if self.__numero_de_fases > 1 and requisitosTermino:
                        newValue = media
                    self.__view.imprimir("%f,%f,%f,%d" % (newValue,icl,ich,self.__fase.id))

            elif self.__output_type == 3:
                newValue = self.__fase.getEsperancaDeN2(momento)
                if len(self.__EN2_history) == 0 or abs(self.__EN2_history[len(self.__EN2_history)-1] - newValue) != 0:
                    mediaold,iclold,ichold,statusold = calculadora.intervaloDeConfiancaDeAmostras(self.__EN2_history,len(self.__EN2_history))
                    self.__EN2_history.append(newValue)
                    media,icl,ich,status = calculadora.intervaloDeConfiancaDeAmostras(self.__EN2_history,len(self.__EN2_history))
                    if len(self.__EN2_history) > 0:
                        declararFinal = abs(mediaold - media) < diferencaDeclararFinal
                    if self.__numero_de_fases > 1 and requisitosTermino:
                        newValue = media
                    self.__view.imprimir("%f,%f,%f,%d" % (newValue,icl,ich,self.__fase.id))

            elif self.__output_type == 4:
                newValue = self.__fase.getEsperancaDeNq1(momento)
                if len(self.__ENq1_history) == 0 or abs(self.__ENq1_history[len(self.__ENq1_history)-1] - newValue) != 0:
                    mediaold,iclold,ichold,statusold = calculadora.intervaloDeConfiancaDeAmostras(self.__ENq1_history,len(self.__ENq1_history))
                    self.__ENq1_history.append(newValue)
                    media,icl,ich,status = calculadora.intervaloDeConfiancaDeAmostras(self.__ENq1_history,len(self.__ENq1_history))
                    if len(self.__ENq1_history) > 0:
                        declararFinal = abs(mediaold - media) < diferencaDeclararFinal
                    if self.__numero_de_fases > 1 and requisitosTermino:
                        newValue = media
                    self.__view.imprimir("%f,%f,%f,%d" % (newValue,icl,ich,self.__fase.id))

            elif self.__output_type == 5:
                newValue = self.__fase.getEsperancaDeNq2(momento)
                if len(self.__ENq2_history) == 0 or abs(self.__ENq2_history[len(self.__ENq2_history)-1] - newValue) != 0:
                    mediaold,iclold,ichold,statusold = calculadora.intervaloDeConfiancaDeAmostras(self.__ENq2_history,len(self.__ENq2_history))
                    self.__ENq2_history.append(newValue)
                    media,icl,ich,status = calculadora.intervaloDeConfiancaDeAmostras(self.__ENq2_history,len(self.__ENq2_history))
                    if len(self.__ENq2_history) > 0:
                        declararFinal = abs(mediaold - media) < diferencaDeclararFinal
                    if self.__numero_de_fases > 1 and requisitosTermino:
                        newValue = media
                    self.__view.imprimir("%f,%f,%f,%d" % (newValue,icl,ich,self.__fase.id))

            elif self.__output_type == 6:
                newValue = self.__fase.getEsperancaDeTVoz()
                if len(self.__ET1_history) == 0 or abs(self.__ET1_history[len(self.__ET1_history)-1] - newValue) != 0:
                    mediaold,iclold,ichold,statusold = calculadora.intervaloDeConfiancaDeAmostras(self.__ET1_history,len(self.__ET1_history))
                    self.__ET1_history.append(newValue)
                    media,icl,ich,status = calculadora.intervaloDeConfiancaDeAmostras(self.__ET1_history,len(self.__ET1_history))
                    if len(self.__ET1_history) > 0:
                        declararFinal = abs(mediaold - media) < diferencaDeclararFinal
                    if self.__numero_de_fases > 1 and requisitosTermino:
                        newValue = media
                    self.__view.imprimir("%f,%f,%f,%d" % (newValue,icl,ich,self.__fase.id))

            elif self.__output_type == 7:
                newValue = self.__fase.getEsperancaDeTDados()
                if len(self.__ET2_history) == 0 or abs(self.__ET2_history[len(self.__ET2_history)-1] - newValue) != 0:
                    mediaold,iclold,ichold,statusold = calculadora.intervaloDeConfiancaDeAmostras(self.__ET2_history,len(self.__ET2_history))
                    self.__ET2_history.append(newValue)
                    media,icl,ich,status = calculadora.intervaloDeConfiancaDeAmostras(self.__ET2_history,len(self.__ET2_history))
                    if len(self.__ET2_history) > 0:
                        declararFinal = abs(mediaold - media) < diferencaDeclararFinal
                    if self.__numero_de_fases > 1 and requisitosTermino:
                        newValue = media
                    self.__view.imprimir("%f,%f,%f,%d" % (newValue,icl,ich,self.__fase.id))

            elif self.__output_type == 8:
                newValue = self.__fase.getEsperancaDeWVoz()
                if len(self.__EW1_history) == 0 or abs(self.__EW1_history[len(self.__EW1_history)-1] - newValue) != 0:
                    mediaold,iclold,ichold,statusold = calculadora.intervaloDeConfiancaDeAmostras(self.__EW1_history,len(self.__EW1_history))
                    self.__EW1_history.append(newValue)
                    media,icl,ich,status = calculadora.intervaloDeConfiancaDeAmostras(self.__EW1_history,len(self.__EW1_history))
                    if len(self.__EW1_history) > 0:
                        declararFinal = abs(mediaold - media) < diferencaDeclararFinal
                    if self.__numero_de_fases > 1 and requisitosTermino:
                        newValue = media
                    self.__view.imprimir("%f,%f,%f,%d" % (newValue,icl,ich,self.__fase.id))
                
            elif self.__output_type == 9:
                newValue = self.__fase.getEsperancaDeWDados()
                if len(self.__EW2_history) == 0 or abs(self.__EW2_history[len(self.__EW2_history)-1] - newValue) != 0:
                    mediaold,iclold,ichold,statusold = calculadora.intervaloDeConfiancaDeAmostras(self.__EW2_history,len(self.__EW2_history))
                    self.__EW2_history.append(newValue)
                    media,icl,ich,status = calculadora.intervaloDeConfiancaDeAmostras(self.__EW2_history,len(self.__EW2_history))
                    if len(self.__EW2_history) > 1:
                        declararFinal = abs(mediaold - media) < diferencaDeclararFinal
                    if self.__numero_de_fases > 1 and requisitosTermino:
                        newValue = media
                    self.__view.imprimir("%f,%f,%f,%d" % (newValue,icl,ich,self.__fase.id))

            elif self.__output_type == 10:
                newValue = self.__fase.getVarianciaDeW1()
                if len(self.__VW1_history) == 0 or abs(self.__VW1_history[len(self.__VW1_history)-1] - newValue) != 0:
                    mediaold,iclold,ichold,statusold = calculadora.intervaloDeConfiancaDeAmostras(self.__VW1_history,len(self.__VW1_history))
                    self.__VW1_history.append(newValue)
                    media,icl,ich,status = calculadora.intervaloDeConfiancaDeAmostras(self.__VW1_history,len(self.__VW1_history))
                    if len(self.__VW1_history) > 0:
                        declararFinal = abs(mediaold - media) < diferencaDeclararFinal
                    if self.__numero_de_fases > 1 and requisitosTermino:
                        newValue = media
                    self.__view.imprimir("%f,%f,%f,%d" % (newValue,icl,ich,self.__fase.id))

            elif self.__output_type == 11:
                newValue = self.__fase.getVarianciaDeW2()
                if len(self.__VW2_history) == 0 or abs(self.__VW2_history[len(self.__VW2_history)-1] - newValue) != 0:
                    mediaold,iclold,ichold,statusold = calculadora.intervaloDeConfiancaDeAmostras(self.__VW2_history,len(self.__VW2_history))
                    self.__VW2_history.append(newValue)
                    media,icl,ich,status = calculadora.intervaloDeConfiancaDeAmostras(self.__VW2_history,len(self.__VW2_history))
                    if len(self.__VW2_history) > 0:
                        declararFinal = abs(mediaold - media) < diferencaDeclararFinal
                    if self.__numero_de_fases > 1 and requisitosTermino:
                        newValue = media
                    self.__view.imprimir("%f,%f,%f,%d" % (newValue,icl,ich,self.__fase.id))

            elif self.__output_type == 12:
                newValue = self.__fase.getEsperancaDeX1()
                if len(self.__EX1_history) == 0 or abs(self.__EX1_history[len(self.__EX1_history)-1] - newValue) != 0:
                    mediaold,iclold,ichold,statusold = calculadora.intervaloDeConfiancaDeAmostras(self.__EX1_history,len(self.__EX1_history))
                    self.__EX1_history.append(newValue)
                    media,icl,ich,status = calculadora.intervaloDeConfiancaDeAmostras(self.__EX1_history,len(self.__EX1_history))
                    if len(self.__EX1_history) > 0:
                        declararFinal = abs(mediaold - media) < diferencaDeclararFinal
                    if self.__numero_de_fases > 1 and requisitosTermino:
                        newValue = media
                    self.__view.imprimir("%f,%f,%f,%d" % (newValue,icl,ich,self.__fase.id))

            elif self.__output_type == 13:
                tipo = ("de voz de canal %d (%d)" % (pacote.canal + 1,pacote.indiceEmCanal)) if pacote.canal != -1 else "de dados"
                self.__view.imprimir("%f: Pacote %s (%d) de rodada %d %s na fila %d" % (momento, tipo, pacote.id, pacote.indiceDaCor, evento, fila))

        if declararFinal and self.__possivel_terminar_sob_demanda:
            self.__forcar_termino = True
            return
        
        if self.__faseTransienteFinalizada == True:
            self.__eventosDaVariancia1 = []
            self.__duracaoEventosDaVariancia1 = []
            self.__eventosDaVariancia2 = []
            self.__duracaoEventosDaVariancia2 = []
            return

        
        EWt = self.__fase.getEsperancaDeWVoz()


        # Daqui para baixo, essa funcao realiza o calculo que define quando
        # a fase transiente acaba. 

        if len(self.__eventosDaVariancia1) < self.__quantidadeDeEventosPorVariancia:
            self.__eventosDaVariancia1.append(EWt)
            self.__duracaoEventosDaVariancia1.append(momento)

            if len(self.__eventosDaVariancia1) == self.__quantidadeDeEventosPorVariancia:
                media1 = 0
                duracao1 = 0
                for indiceEvento in xrange(self.__quantidadeDeEventosPorVariancia):
                    media1 += self.__eventosDaVariancia1[indiceEvento]*self.__duracaoEventosDaVariancia1[indiceEvento]
                    duracao1 += self.__duracaoEventosDaVariancia1[indiceEvento]
                
                if duracao1 > 0:
                    media1 /= duracao1
                else:
                    media1 = 0
                
                self.__variancia1 = 0
                for indiceEvento in xrange(self.__quantidadeDeEventosPorVariancia):
                    self.__variancia1 += (self.__eventosDaVariancia1[indiceEvento] - media1)**2

                if self.__quantidadeDeEventosPorVariancia > 1:
                    self.__variancia1 /= (self.__quantidadeDeEventosPorVariancia - 1)
                else:
                    self.__variancia1 = 0

            return

        if len(self.__eventosDaVariancia2) < self.__quantidadeDeEventosPorVariancia:
            self.__eventosDaVariancia2.append(EWt)
            self.__duracaoEventosDaVariancia2.append(momento)

        if len(self.__eventosDaVariancia2) == self.__quantidadeDeEventosPorVariancia:
            media2 = 0
            duracao2 = 0
            for indiceEvento in xrange(self.__quantidadeDeEventosPorVariancia):
                media2 += self.__eventosDaVariancia2[indiceEvento]*self.__duracaoEventosDaVariancia2[indiceEvento]
                duracao2 += self.__duracaoEventosDaVariancia2[indiceEvento]
            
            if duracao2 > 0:
                media2 /= duracao2
            else:
                media2 = 0
            
            self.__variancia2 = 0
            for indiceEvento in xrange(self.__quantidadeDeEventosPorVariancia):
                self.__variancia2 += (self.__eventosDaVariancia2[indiceEvento] - media2)**2
            
            if self.__quantidadeDeEventosPorVariancia > 1:
                self.__variancia2 /= (self.__quantidadeDeEventosPorVariancia - 1)
            else:
                self.__variancia2 = 0

            print abs(self.__variancia1 - self.__variancia2)
            if abs(self.__variancia1 - self.__variancia2) <= self.__diferencaAceitavelDasVariancias:
                print "Fase transiente finalizada"
                print "Finalizada com %d pacotes" % (len(self.__fase.pacotes))
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
            indiceDaFase = self.__fase.id
            if indiceDaFase == -1 or (self.__fase.quantidadeDeEventosVoz >= self.__numero_de_eventos_voz_por_fase and self.__fase.quantidadeDeEventosDados >= self.__numero_de_eventos_dados_por_fase):
                indiceDaFase += 1

            # A entrada nesse 'if' indica o fim de uma fase e o inicio de uma nova
            if indiceDaFase > self.__fase.id: 
                if self.__output_type == 0 and self.__fase.id != -1:
                    self.__fase.calcularEstatisticas(tempoAnterior, self.__view, self.__intervaloDeConfianca, self.__lambd)

                print "Finalizada rodada %d com %d pacotes" % (indiceDaFase, len(self.__fase.pacotes))
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

        self.__numero_de_pacotes_que_passaram_pelo_sistema += 1
        self.adicionarEvento(pacote, "chegou", self.__filaVoz.id, self.__tempoAtual)
        if self.__filaVoz.numeroDePacotesNaFila() == 1: # So o atual se encontra na fila
            if self.__interrupcoes == True and self.__filaDados.numeroDePacotesNaFila() > 0: 
                # Interrompe individuo da fila de dados em servico
                # removendo evento de completude do individuo interrompido
                for eventoIndex in xrange(len(self.__lista_de_eventos)):
                    if len(self.__lista_de_eventos) > eventoIndex and self.__lista_de_eventos[eventoIndex].tipo == EVENTO_PACOTE_DADOS_FINALIZADO:
                        self.__lista_de_eventos.pop(eventoIndex)
                        eventoIndex -= 1

            if self.__interrupcoes == True or self.__filaDados.numeroDePacotesNaFila() == 0:
                pacote.tempoChegadaServico = self.__tempoAtual
                
                tempoAAvancar = self.__agendador.agendarTempoDeServicoFilaVoz(pacote.canal,pacote.servico,self.__filaVoz)
                novoEvento = Evento(EVENTO_PACOTE_VOZ_FINALIZADO, pacote.canal, tempoAAvancar)
                self.__lista_de_eventos.append(novoEvento)
                pacote.tempoServico = tempoAAvancar

                subcanal = pacote.canal
                if self.__agendador.deveAgendarChegadaServicoVoz(subcanal,self.__filaVoz) and self.podeAdicionarEventoDeTipoECanalALista(EVENTO_PACOTE_VOZ_CHEGADA, subcanal):
                    servico, indice, tempoAAvancar = self.__agendador.agendarChegadaFilaVoz(subcanal)
                    if tempoAAvancar != None:
                        novoEvento = Evento(EVENTO_PACOTE_VOZ_CHEGADA, subcanal, tempoAAvancar, indice, servico)
                        self.__lista_de_eventos.append(novoEvento)

        if self.__faseTransienteFinalizada == False:
            if self.__agendador.deveAgendarChegadaFilaVoz(pacote.canal,pacote.servico,self.__filaVoz) and self.podeAdicionarEventoDeTipoECanalALista(EVENTO_PACOTE_VOZ_CHEGADA, pacote.canal):
                servico, indice, tempoAAvancar = self.__agendador.agendarChegadaFilaVoz(pacote.canal)
                if tempoAAvancar != None:
                    novoEvento = Evento(EVENTO_PACOTE_VOZ_CHEGADA, pacote.canal, tempoAAvancar, indice, servico)
                    self.__lista_de_eventos.append(novoEvento)
            return

        if self.__fase.id + 1 != self.__numero_de_fases or self.__fase.quantidadeDeEventosVoz < self.__numero_de_eventos_voz_por_fase or self.__fase.quantidadeDeEventosDados < self.__numero_de_eventos_dados_por_fase:
            if self.__agendador.deveAgendarChegadaFilaVoz(pacote.canal,pacote.servico,self.__filaVoz) and self.podeAdicionarEventoDeTipoECanalALista(EVENTO_PACOTE_VOZ_CHEGADA, pacote.canal):
                servico, indice, tempoAAvancar = self.__agendador.agendarChegadaFilaVoz(pacote.canal)
                if tempoAAvancar != None:
                    novoEvento = Evento(EVENTO_PACOTE_VOZ_CHEGADA, pacote.canal, tempoAAvancar, indice, servico)
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
        pacote = Pacote(self.__indice_pacote_atual, self.__tempoAtual, corDoPacote, -1)
        
        self.__fase.adicionarPacote(pacote)
        self.__filaDados.adicionarPacoteAFila(pacote)

        self.__numero_de_pacotes_que_passaram_pelo_sistema += 1
        self.adicionarEvento(pacote, "chegou", self.__filaDados.id, self.__tempoAtual)
        if self.__filaVoz.numeroDePacotesNaFila() == 0 and self.__filaDados.numeroDePacotesNaFila() == 1:
            pacote.tempoChegadaServico = self.__tempoAtual
            
            tempoAAvancar = self.__agendador.agendarTempoDeServicoFilaDados()
            novoEvento = Evento(EVENTO_PACOTE_DADOS_FINALIZADO, pacote.canal, tempoAAvancar)
            self.__lista_de_eventos.append(novoEvento)
            pacote.tempoServico = novoEvento.tempoRestante

        if self.__faseTransienteFinalizada == False:
            tempoAAvancar = self.__agendador.agendarChegadaFilaDados(self.__lambd)
            if tempoAAvancar != None:
                novoEvento = Evento(EVENTO_PACOTE_DADOS_CHEGADA, pacote.canal, tempoAAvancar)
                self.__lista_de_eventos.append(novoEvento)
            return

        if self.__fase.id + 1 != self.__numero_de_fases:
            tempoAAvancar = self.__agendador.agendarChegadaFilaDados(self.__lambd)
            if tempoAAvancar != None:
                novoEvento = Evento(EVENTO_PACOTE_DADOS_CHEGADA, pacote.canal, tempoAAvancar)
                self.__lista_de_eventos.append(novoEvento)
            return

        if self.__fase.quantidadeDeEventosVoz < self.__numero_de_eventos_voz_por_fase or self.__fase.quantidadeDeEventosDados < self.__numero_de_eventos_dados_por_fase:
            tempoAAvancar = self.__agendador.agendarChegadaFilaDados(self.__lambd)
            if tempoAAvancar != None:
                novoEvento = Evento(EVENTO_PACOTE_DADOS_CHEGADA, pacote.canal, tempoAAvancar)
                self.__lista_de_eventos.append(novoEvento)


    """Evento: Fim de servico na fila de voz
       Com essa funcao realizamos todas as acoes que ocorrem em decorrencia do 
       fim de um servico na fila de voz, que sao: tirar o Pacote que concluiu o servico 
       da fila de voz, e colocar em servico o proximo Pacote da fila de voz se houver 
       algum (se nao houver, colocar em servico o proximo Pacote da fila de dados, 
       se houver algum)."""

    def PacoteTerminaServicoNaFilaVoz(self):
        pacote = self.__filaVoz.retirarPacoteEmAtendimento()
        pacote.tempoTerminoServico = self.__tempoAtual

        if pacote.indiceDaCor == self.__fase.id:
            self.__fase.quantidadeDeEventosVoz += 1
        
        self.adicionarEvento(pacote, "terminou o atendimento", self.__filaVoz.id, self.__tempoAtual)

        if self.__filaVoz.numeroDePacotesNaFila() > 0:
            novoPacote = self.__filaVoz.pacoteEmAtendimento()
            novoPacote.tempoChegadaServico = self.__tempoAtual
            
            tempoAAvancar = self.__agendador.agendarTempoDeServicoFilaVoz(novoPacote.canal,novoPacote.servico,self.__filaVoz)
            novoEvento = Evento(EVENTO_PACOTE_VOZ_FINALIZADO, novoPacote.canal, tempoAAvancar)
            self.__lista_de_eventos.append(novoEvento)
            novoPacote.tempoServico = novoEvento.tempoRestante

            subcanal = novoPacote.canal
            if self.__agendador.deveAgendarChegadaServicoVoz(subcanal,self.__filaVoz) and self.podeAdicionarEventoDeTipoECanalALista(EVENTO_PACOTE_VOZ_CHEGADA, subcanal):
                servico, indice, tempoAAvancar = self.__agendador.agendarChegadaFilaVoz(subcanal)
                if tempoAAvancar != None:
                    novoEvento = Evento(EVENTO_PACOTE_VOZ_CHEGADA, subcanal, tempoAAvancar, indice, servico)
                    self.__lista_de_eventos.append(novoEvento)
        else:
            if self.__filaDados.numeroDePacotesNaFila() > 0:
                proximoPacote = self.__filaDados.pacoteEmAtendimento()
                if proximoPacote.tempoServico > 0: 
                    # Pacote da fila de dados que foi interrompido anteriormente retorna
                    tempoAAvancar = proximoPacote.tempoServico
                    novoEvento = Evento(EVENTO_PACOTE_DADOS_FINALIZADO, proximoPacote.canal, tempoAAvancar)
                    self.__lista_de_eventos.append(novoEvento)
                    
                else: 
                    # Pacote da fila de dados eh atendido pela primeira vez
                    proximoPacote.tempoChegadaServico = self.__tempoAtual
                    
                    tempoAAvancar = self.__agendador.agendarTempoDeServicoFilaDados()
                    novoEvento = Evento(EVENTO_PACOTE_DADOS_FINALIZADO, proximoPacote.canal, tempoAAvancar)
                    self.__lista_de_eventos.append(novoEvento)
                    proximoPacote.tempoServico = novoEvento.tempoRestante


    """Evento: Fim de servico na fila de dados
       Com essa funcao realizamos todas as acoes que ocorrem em decorrencia do 
       fim de um servico na fila de dados, que sao: tirar o Pacote que concluiu o servico 
       da fila de dados, e colocar em servico o proximo Pacote da fila de dados (se houver algum)."""

    def PacoteTerminaServicoNaFilaDados(self):
        pacote = self.__filaDados.retirarPacoteEmAtendimento()
        pacote.tempoTerminoServico = self.__tempoAtual

        if pacote.indiceDaCor == self.__fase.id:
            self.__fase.quantidadeDeEventosDados += 1
        
        self.adicionarEvento(pacote, "terminou o atendimento", self.__filaDados.id, self.__tempoAtual)
        
        if self.__interrupcoes == False and self.__filaVoz.numeroDePacotesNaFila() > 0:
            novoPacote = self.__filaVoz.pacoteEmAtendimento()
            novoPacote.tempoChegadaServico = self.__tempoAtual
            
            tempoAAvancar = self.__agendador.agendarTempoDeServicoFilaVoz(novoPacote.canal,novoPacote.servico,self.__filaVoz)
            novoEvento = Evento(EVENTO_PACOTE_VOZ_FINALIZADO, novoPacote.canal, tempoAAvancar)
            self.__lista_de_eventos.append(novoEvento)
            novoPacote.tempoServico = novoEvento.tempoRestante

            subcanal = novoPacote.canal
            if self.__agendador.deveAgendarChegadaServicoVoz(subcanal,self.__filaVoz) and self.podeAdicionarEventoDeTipoECanalALista(EVENTO_PACOTE_VOZ_CHEGADA, subcanal):
                servico, indice, tempoAAvancar = self.__agendador.agendarChegadaFilaVoz(subcanal)
                if tempoAAvancar != None:
                    novoEvento = Evento(EVENTO_PACOTE_VOZ_CHEGADA, subcanal, tempoAAvancar, indice, servico)
                    self.__lista_de_eventos.append(novoEvento)
        else:
            if self.__filaDados.numeroDePacotesNaFila() > 0:
                proximoPacote = self.__filaDados.pacoteEmAtendimento()
                proximoPacote.tempoChegadaServico = self.__tempoAtual
                
                tempoAAvancar = self.__agendador.agendarTempoDeServicoFilaDados()
                novoEvento = Evento(EVENTO_PACOTE_DADOS_FINALIZADO, proximoPacote.canal, tempoAAvancar)
                self.__lista_de_eventos.append(novoEvento)
                proximoPacote.tempoServico = novoEvento.tempoRestante


    def podeAdicionarEventoDeTipoECanalALista(self, tipo, canal):
        subeventos = [evento for evento in self.__lista_de_eventos if evento.tipo == tipo and evento.canal == canal]
        return len(subeventos) == 0

    def eventoDeDuracaoMinima(self):

        def tempoRestanteDeEvento(e):
            return e.tempoRestante
        self.__lista_de_eventos.sort(key=tempoRestanteDeEvento)

        return self.__lista_de_eventos.pop(0) if len(self.__lista_de_eventos) > 0 else None


    """ O metodo executarProximoEvento(), como o proprio nome diz, executa o proximo evento,
        com base no que foi "decidido" no metodo eventoDeDuracaoMinima(). """
    def executarProximoEvento(self):

        proximoEvento = self.eventoDeDuracaoMinima()
        tempoRestante = proximoEvento.tempoRestante
        tipo = proximoEvento.tipo
        for evento in self.__lista_de_eventos:
            evento.tempoRestante -= tempoRestante

        tempoAnterior = self.__tempoAtual
        self.__tempoAtual += tempoRestante
        
        self.agregarEmSomatorioPacotesPorTempo(tempoRestante)

        # Tres eventos principais, tres ifs principais.
        if tipo == EVENTO_PACOTE_VOZ_CHEGADA:
            self.PacoteEntraNaFilaVoz(proximoEvento.canal, tempoAnterior, tempoRestante, proximoEvento.indiceEmCanal, proximoEvento.servico)

        elif tipo == EVENTO_PACOTE_DADOS_CHEGADA:
            self.PacoteEntraNaFilaDados(tempoAnterior)

        elif tipo == EVENTO_PACOTE_VOZ_FINALIZADO:
            self.PacoteTerminaServicoNaFilaVoz()

        elif tipo == EVENTO_PACOTE_DADOS_FINALIZADO:
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
    def executarSimulacao(self, seed, lambdaValue, transienteAmostras, transienteMargem, interrupcoes, numeroDeEventosVozPorRodada, numeroDeEventosDadosPorRodada, fases, hasOutputFile, variavelDeSaida, testeDeCorretudeChegadaVoz, testeDeCorretudeChegadaDados, testeDeCorretudePacotesVoz, testeDeCorretudeServicoDados, terminarcomdemanda, intervaloDeConfianca, desabilitarvoz, desabilitardados):
        self.__lambd = lambdaValue
        self.__interrupcoes = interrupcoes
        self.__numero_de_eventos_voz_por_fase = numeroDeEventosVozPorRodada
        self.__numero_de_eventos_dados_por_fase = numeroDeEventosDadosPorRodada
        self.__numero_de_fases = fases
        self.__intervaloDeConfianca = intervaloDeConfianca
        self.__possivel_terminar_sob_demanda = terminarcomdemanda

        self.__quantidadeDeEventosPorVariancia = transienteAmostras
        self.__diferencaAceitavelDasVariancias = transienteMargem
        
        self.__output_type = variavelDeSaida
        self.__view = View(variavelDeSaida == 0 or variavelDeSaida == 13)
        self.__view.setImprimirEmArquivo(hasOutputFile)

        self.__agendador.setTesteDeCorretude(testeDeCorretudeChegadaVoz, testeDeCorretudeChegadaDados, testeDeCorretudePacotesVoz, testeDeCorretudeServicoDados)
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
            novoEvento = Evento(EVENTO_PACOTE_DADOS_CHEGADA, -1, 0)
            self.__lista_de_eventos.append(novoEvento)


        # Loop principal da simulacao
        while self.__forcar_termino == False and (self.__numero_de_fases > self.__fase.id + 1 or self.__fase.quantidadeDeEventosVoz < self.__numero_de_eventos_voz_por_fase or self.__fase.quantidadeDeEventosDados < self.__numero_de_eventos_dados_por_fase):
            self.executarProximoEvento()

        if self.__forcar_termino == True:
            print "Terminado com %d rodadas com %d pacotes" % (self.__fase.id + 1, self.__numero_de_pacotes_que_passaram_pelo_sistema)
            self.__forcar_termino = False

        if self.__output_type == 0:
            self.__fase.calcularEstatisticas(self.__tempoAtual, self.__view, self.__intervaloDeConfianca, self.__lambd)
            
            tamanho = len(self.__fases)
            p = (self.media((f.EX1 for f in self.__fases))*lambdaValue)/1000
            calculadora = CalculadoraIC(self.__intervaloDeConfianca)
            EDeltaK, EDelta, VDeltaK, VDelta = CalculadoraVoz.esperancaEVarianciaDaVarianciaDeChegadasDePacotesDeVoz(self.__fases)
            
            self.__view.imprimir("p (Dados):      %f" % (p))
            self.__view.imprimir("Fila e estavel: %s" % ("Sim" if p <= 0.8314 else "Nao"))
            self.__view.imprimir("")
            self.__view.imprimir("E[T]  (Dados):  %f (%f - %f) - Intervalo %s" % (calculadora.intervaloDeConfiancaDeAmostras((f.ET1  for f in self.__fases),tamanho)))
            self.__view.imprimir("E[W]  (Dados):  %f (%f - %f) - Intervalo %s" % (calculadora.intervaloDeConfiancaDeAmostras((f.EW1  for f in self.__fases),tamanho)))
            self.__view.imprimir("E[X]  (Dados):  %f (%f - %f) - Intervalo %s" % (calculadora.intervaloDeConfiancaDeAmostras((f.EX1  for f in self.__fases),tamanho)))
            self.__view.imprimir("E[Nq] (Dados):  %f (%f - %f) - Intervalo %s" % (calculadora.intervaloDeConfiancaDeAmostras((f.ENq1 for f in self.__fases),tamanho)))
            self.__view.imprimir("")
            self.__view.imprimir("E[T]  (Voz): %f (%f - %f) - Intervalo %s" % (calculadora.intervaloDeConfiancaDeAmostras((f.ET2  for f in self.__fases),tamanho)))
            self.__view.imprimir("E[W]  (Voz): %f (%f - %f) - Intervalo %s" % (calculadora.intervaloDeConfiancaDeAmostras((f.EW2  for f in self.__fases),tamanho)))
            self.__view.imprimir("E[Nq] (Voz): %f (%f - %f) - Intervalo %s" % (calculadora.intervaloDeConfiancaDeAmostras((f.ENq2 for f in self.__fases),tamanho)))
            self.__view.imprimir("")
            self.__view.imprimir("Inicio da transmissao de pacotes de voz:")
            self.__view.imprimir("E[Delta]:  %f (%f - %f) - Intervalo %s" % (calculadora.intervaloDeConfiancaDeAmostras(EDeltaK, len(EDeltaK))))
            self.__view.imprimir("V(Delta):  %f (%f - %f) - Intervalo %s" % (calculadora.intervaloDeConfiancaDeAmostras(VDeltaK, len(VDeltaK))))
            self.__view.imprimir("")
            self.__view.imprimir("E[X] (Voz):   %f (%f - %f) - Intervalo %s" % (calculadora.intervaloDeConfiancaDeAmostras((f.EX2  for f in self.__fases),tamanho)))
            self.__view.imprimir("E[N] (Dados): %f (%f - %f) - Intervalo %s" % (calculadora.intervaloDeConfiancaDeAmostras((f.EN1  for f in self.__fases),tamanho)))
            self.__view.imprimir("V(W) (Dados): %f (%f - %f) - Intervalo %s" % (calculadora.intervaloDeConfiancaDeAmostras((f.EVW1 for f in self.__fases),tamanho)))
            self.__view.imprimir("E[N] (Voz):   %f (%f - %f) - Intervalo %s" % (calculadora.intervaloDeConfiancaDeAmostras((f.EN2  for f in self.__fases),tamanho)))
            self.__view.imprimir("V(W) (Voz):   %f (%f - %f) - Intervalo %s" % (calculadora.intervaloDeConfiancaDeAmostras((f.EVW2 for f in self.__fases),tamanho)))

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
    numeroDeEventosVozPorRodada   = int(  request.args.get('eventosporrodadavoz',   default='100000'))
    numeroDeEventosDadosPorRodada = int(  request.args.get('eventosporrodadadados', default='100000'))
    lambdaValue                   = float(request.args.get('lambda',                default='0.3'))
    rodadas                       = int(  request.args.get('rodadas',               default='100'))
    simulacoes                    = int(  request.args.get('simulacoes',            default='1'))
    outputFile                    = (     request.args.get('progressivo',           default='false') == 'true')
    interrupcoes                  = (     request.args.get('interrupcoes',          default='false') == 'true')
    testeDeCorretudeChegadaVoz    = (     request.args.get('testechegadavoz',       default='false') == 'true')
    testeDeCorretudeChegadaDados  = (     request.args.get('testechegadadados',     default='false') == 'true')
    testeDeCorretudePacotesVoz    = (     request.args.get('testepacotesvoz',       default='false') == 'true')
    testeDeCorretudeServicoDados  = (     request.args.get('testeservicodados',     default='false') == 'true')
    terminarcomdemanda            = (     request.args.get('terminarcomdemanda',    default='false') == 'true')
    variavelDeSaida               = int(  request.args.get('variavel',              default='1'))
    intervaloDeConfianca          = float(request.args.get('confianca',             default='0.95'))
    sementeForcada                = int(  request.args.get('semente',               default='0'))
    transienteAmostras            = int(  request.args.get('transamostra',          default='1000'))
    transienteMargem              = float(request.args.get('transmargem',           default='0.002'))
    
    desabilitarvoz   = (request.args.get('desabilitarvoz',   default='false') == 'true')
    desabilitardados = (request.args.get('desabilitardados', default='false') == 'true')

    seedsDistance = 0.01
    seedsList = []

    output = ''
    for i in xrange(simulacoes):
        print "SIMULACAO %d" % (i+1)
        start = timeit.default_timer()
        tempSeed = randomNumberDistantFrom(seedsList, seedsDistance)
        newSeed = int(tempSeed*1000000000) if sementeForcada == 0 else sementeForcada
        sOutput = Simulacao().executarSimulacao(newSeed, lambdaValue, transienteAmostras, transienteMargem, interrupcoes, numeroDeEventosVozPorRodada, numeroDeEventosDadosPorRodada, rodadas, outputFile, variavelDeSaida, testeDeCorretudeChegadaVoz, testeDeCorretudeChegadaDados, testeDeCorretudePacotesVoz, testeDeCorretudeServicoDados, terminarcomdemanda, intervaloDeConfianca, desabilitarvoz, desabilitardados)
        seedsList.append(tempSeed)
        end = timeit.default_timer()
        print "Tempo de execucao: %f" % (end - start)
        output = "%s\n%s" % (output, sOutput)
    return output

if __name__ == "__main__":
    # Inicia o Flask se o arquivo do Python for chamado diretamente (o que nunca deve ser o caso)
    app.run(host='0.0.0.0')
