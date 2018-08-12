import random
import numpy
import math

""" O Agendador sera responsavel por agendar chegadas e servicos
    de acordo com as taxas lambda e mi, respectivamente."""

class Agendador(object):

    def __init__(self):
        self.__testeDeCorretude = False
        self.__desabilitarVoz = False
        self.__desabilitarDados = False

        self.__tamanhoPacoteVoz = 512.0 # 512 bits = 64 bytes
        self.__taxaDeTransmissao = (2.0*1000*1000)/1000 ## 2 Megabits per segundo (em ms)
        
        self.__pacoteFilaVozIndice = []
        self.__pacoteFilaVozTotal = []
        self.__pacoteFilaVozTempoDeAguardo = []
        self.__pacoteIndiceServicoDeCanal = []
        for indice in range(30):
            self.__pacoteFilaVozIndice.append(0)
            self.__pacoteFilaVozTotal.append(0)
            self.__pacoteFilaVozTempoDeAguardo.append(0)
            self.__pacoteIndiceServicoDeCanal.append(-1)

        self.__probabilidade_de_L = []
        for indice in range(1500 - 64 + 1):
            x = indice + 64
            p = 0.0

            # Delta de Jirac
            if x == 64:
               p += 0.3
            if x == 512:
               p += 0.1
            if x == 1500:
               p += 0.3

            # Funcao degrau
            if x >= 64:
                p += (3.0/(10*1436))
            if x >= 1500:
                p -= (3.0/(10*1436))
            self.__probabilidade_de_L.append(p)
    
    def valorDeLComProbabilidade(self, prob):
        newProb = prob
        index = 0
        while newProb > self.__probabilidade_de_L[index]:
            newProb -= self.__probabilidade_de_L[index]
            index += 1
        return index + 64

    def setTesteDeCorretude(self, testeDeCorretude):
        self.__testeDeCorretude = testeDeCorretude

    def setDesabilitarVoz(self, desabilitarVoz):
        self.__desabilitarVoz = desabilitarVoz

    def setDesabilitarDados(self, desabilitarDados):
        self.__desabilitarDados = desabilitarDados

    def configurarSemente(self, seed):
        if self.__testeDeCorretude == True:
            return
        
        print "Semente: %d" % (seed)
        random.seed(seed)
        numpy.random.RandomState(seed=seed)

    def agendarChegadaFilaVoz(self, canal): 
        if self.__desabilitarVoz == True:
            return None, None, None

        espera_previa = 0
        
        indice = self.__pacoteFilaVozIndice[canal]
        total  = self.__pacoteFilaVozTotal[canal]
        if indice == total: # Inicio de uma nova remessa de pacotes de voz
            espera_previa = self.__pacoteFilaVozTempoDeAguardo[canal]
            self.__pacoteFilaVozTempoDeAguardo[canal] = 0
            indice = 0

        if indice == 0:
            self.__pacoteFilaVozIndice[canal] = 1
            self.__pacoteIndiceServicoDeCanal[canal] += 1
            
            quantidadePacotes = 22
            if self.__testeDeCorretude == False:
                quantidadePacotes = int(round(numpy.random.geometric(p=1.0/22.0)))

            tempoDeEspera = espera_previa + 650
            if self.__pacoteFilaVozTotal[canal] == 0 or self.__testeDeCorretude == False:
                tempoDeEspera = espera_previa + random.expovariate(1.0/650)
            
            # Definindo a quantidade de pacotes que virao na nova remessa
            self.__pacoteFilaVozTotal[canal] = quantidadePacotes
            
            # Calculando o tempo de silencio necessario para a nova remessa comecar
            return self.__pacoteIndiceServicoDeCanal[canal], self.__pacoteFilaVozIndice[canal], tempoDeEspera

        self.__pacoteFilaVozIndice[canal] += 1
        return self.__pacoteIndiceServicoDeCanal[canal], self.__pacoteFilaVozIndice[canal], 16

    def agendarChegadaFilaDados(self, lambd):
        if self.__desabilitarDados == True:
            return None

        if self.__testeDeCorretude == True:
            return 1000.0/lambd

        return random.expovariate(lambd/1000)

    def deveAgendarChegadaFilaVoz(self, canal, servico, filaVoz): 
        total  = self.__pacoteFilaVozTotal[canal]
        indice = self.__pacoteFilaVozIndice[canal]
        
        if indice == total and total != 0 and filaVoz.numeroDePacotesNaFilaDeCanal(canal) > 1:
            return False
        
        return True

    def deveAgendarChegadaServicoVoz(self, canal, filaVoz): 
        subindice = self.__pacoteFilaVozIndice[canal]
        subtotal  = self.__pacoteFilaVozTotal[canal]
        
        if subindice == subtotal and filaVoz.numeroDePacotesNaFilaDeCanal(canal) == 1:
            return True
        
        return False

    def agendarTempoDeServicoFilaVoz(self, canal, servico, filaVoz):
        tempo = self.__tamanhoPacoteVoz/self.__taxaDeTransmissao # 0.256 ms

        indice = self.__pacoteFilaVozIndice[canal]
        total  = self.__pacoteFilaVozTotal[canal]

        if indice == total and filaVoz.numeroDePacotesNaFilaDeCanal(canal) == 1:
            if self.__pacoteFilaVozTempoDeAguardo[canal] == 0:
                self.__pacoteFilaVozTempoDeAguardo[canal] = tempo + 16

        return tempo

    def agendarTempoDeServicoFilaDados(self):
        if self.__testeDeCorretude == True:
            return (754.8*8.0)/self.__taxaDeTransmissao # 3.0192 ms

        Lbytes = self.valorDeLComProbabilidade(random.random())
        return (Lbytes*8.0)/self.__taxaDeTransmissao