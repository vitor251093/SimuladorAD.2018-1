import random
import numpy
import math

""" O Agendador sera responsavel por agendar chegadas e servicos
    de acordo com as taxas lambda e mi, respectivamente."""

class Agendador(object):

    def __init__(self):
        self.__testeDeCorretude = False
        self.__tamanhoPacoteVoz = 512.0 # 512 bits = 64 bytes
        self.__taxaDeTransmissao = 2.0*1000*1000 ## 2 Megabits per segundo
        
        self.__pacoteFilaVozIndice = []
        self.__pacoteFilaVozTotal = []
        self.__pacoteFilaVozTempoDeAguardo = []
        for indice in range(30):
            self.__pacoteFilaVozIndice.append(0)
            self.__pacoteFilaVozTotal.append(0)
            self.__pacoteFilaVozTempoDeAguardo.append(-1)

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

    def configurarSemente(self, seed):
        if self.__testeDeCorretude == True:
            return
        
        random.seed(seed)

    def agendarChegadaFilaVoz(self, canal): 
        indice = self.__pacoteFilaVozIndice[canal]
        total = self.__pacoteFilaVozTotal[canal]
        
        espera_previa = 0
        if indice == total: # Inicio de uma nova remessa de pacotes de voz
            espera_previa = self.__pacoteFilaVozTempoDeAguardo[canal]
            if espera_previa == -1:
                return -1 # Ou nao...
            indice = 0

        if indice == 0:
            self.__pacoteFilaVozIndice[canal] = 1
            
            # Definindo a quantidade de pacotes que virao na nova remessa
            if self.__testeDeCorretude == True:
                self.__pacoteFilaVozTotal[canal] = 22
            else:
                p = 1.0/22.0
                n = numpy.random.geometric(p=p)
                self.__pacoteFilaVozTotal[canal] = math.ceil(n)

            # Calculando o tempo de silencio necessario para a nova remessa comecar
            if self.__testeDeCorretude == True:
                return espera_previa + 650
            else:
                return espera_previa + random.expovariate(0.65)*1000

        self.__pacoteFilaVozIndice[canal] += 1
        return 16

    def agendarChegadaFilaDados(self, lambd):
        if self.__testeDeCorretude == True:
            return 1.0/lambd

        return random.expovariate(lambd)

    def agendarTempoDeServicoFilaVoz(self, canal):
        tempo = ((self.__tamanhoPacoteVoz*1000)/self.__taxaDeTransmissao) # ms

        indice = self.__pacoteFilaVozIndice[canal]
        total = self.__pacoteFilaVozTotal[canal]
        if indice == total:
            self.__pacoteFilaVozTempoDeAguardo[canal] = tempo + 16
        else:
            self.__pacoteFilaVozTempoDeAguardo[canal] = -1

        return tempo

    def agendarTempoDeServicoFilaDados(self):
        if self.__testeDeCorretude == True:
            return (754.8*8.0*1000)/self.__taxaDeTransmissao

        Lbytes = self.valorDeLComProbabilidade(random.random())
        return (Lbytes*8.0*1000)/self.__taxaDeTransmissao