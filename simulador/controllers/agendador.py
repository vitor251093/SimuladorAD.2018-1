import random
import numpy
import math

""" O Agendador sera responsavel por agendar chegadas e servicos
    de acordo com as taxas lambda e mi, respectivamente."""

class Agendador(object):

    def __init__(self):
        self.__testeDeCorretude = False
        self.__tamanhoPacoteVoz = 512.0 # bits
        self.__taxaDeTransmissao = 2.0*1024*1024*8 ## 2 Megabytes per segundo
        
        self.__pacoteFilaVozIndice = []
        self.__pacoteFilaVozTotal = []
        for indice in range(30):
            self.__pacoteFilaVozIndice.append(0)
            self.__pacoteFilaVozTotal.append(0)

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
        # TODO: A primeira chegada de um novo periodo de atividade soh 
        # deve comecar 16ms depois do ultimo servico do periodo anterior.
        indice = self.__pacoteFilaVozIndice[canal]
        total = self.__pacoteFilaVozTotal[canal]
        if indice == total:
            indice = 0

        if indice == 0:
            self.__pacoteFilaVozIndice[canal] += 1
            
            if self.__testeDeCorretude == True:
                self.__pacoteFilaVozTotal[canal] = 22
                return 650
            else:
                p = 1.0/22.0
                n = numpy.random.geometric(p=p)
                self.__pacoteFilaVozTotal[canal] = math.ceil(n)
                
                return random.expovariate(0.65)*1000

        return 16

    def agendarChegadaFilaDados(self, lambd):
        if self.__testeDeCorretude == True:
            return 1.0/lambd

        return random.expovariate(lambd)

    def agendarTempoDeServicoFilaVoz(self):
        # TODO: Tamanho do pacote de voz varia
        # Nao foi possível determinar quando um tamanho deveria ser escolhido
        # em relacao a outro.
        return ((self.__tamanhoPacoteVoz*1000)/self.__taxaDeTransmissao) # ms

    def agendarTempoDeServicoFilaDados(self):
        if self.__testeDeCorretude == True:
            return (754.8*8.0*1000)/self.__taxaDeTransmissao

        Lbytes = self.valorDeLComProbabilidade(random.random())
        return (Lbytes*8.0*1000)/self.__taxaDeTransmissao