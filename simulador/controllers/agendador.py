import random
import numpy

""" O Agendador sera responsavel por agendar chegadas e servicos
    de acordo com as taxas lambda e mi, respectivamente."""

class Agendador(object):

    def __init__(self):
        self.__testeDeCorretude = False
        self.__tamanhoPacoteVoz = 512.0 # bits
        self.__taxaDeTransmissao = 2*1024*1024*8 ## bits por segundo
        
        self.__pacoteFilaVozIndice = []
        self.__pacoteFilaVozTotal = []
        for indice in range(30):
            self.__pacoteFilaVozIndice.append(0)
            self.__pacoteFilaVozTotal.append(0)
    

    def setTesteDeCorretude(self, testeDeCorretude):
        self.__testeDeCorretude = testeDeCorretude

    def configurarSemente(self, seed):
        if self.__testeDeCorretude == True:
            return
        
        random.seed(seed)

    def agendarChegadaFilaVoz(self, canal): 
        # TODO: 
        # A primeira chegada de um novo periodo de atividade so 
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
                self.__pacoteFilaVozTotal[canal] = n
                
                return random.expovariate(0.65)*1000

        return 16

    def agendarChegadaFilaDados(self, lambd):
        if self.__testeDeCorretude == True:
            return 1.0/lambd

        return random.expovariate(lambd)

    def agendarTempoDeServicoFilaVoz(self):
        return ((self.__tamanhoPacoteVoz*1000)/self.__taxaDeTransmissao) # ms

    def agendarTempoDeServicoFilaDados(self, mi):
        # TODO: Configurar corretamente
        if self.__testeDeCorretude == True:
            return 2.0/mi

        return random.expovariate(mi)