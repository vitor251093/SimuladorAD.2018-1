import random

""" O Agendador sera responsavel por agendar chegadas e servicos
    de acordo com as taxas lambda e mi, respectivamente."""

class Agendador(object):

    def __init__(self):
        self.__testeDeCorretude = False

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

    def agendarChegadaFilaVoz(self, lambd, canal):
        if self.__testeDeCorretude == True:
            return 2.0/lambd

        indice = self.__pacoteFilaVozIndice[canal]
        total = self.__pacoteFilaVozTotal[canal]
        if indice == total:
            indice = 0

        if indice == 0:
            self.__pacoteFilaVozIndice[canal] += 1
            
            n = 1
            p = 1.0/22.0
            randomValue = random.random()
            while pow(1 - p, n - 1)*p > randomValue:
                randomValue -= pow(1 - p, n - 1)*p
                n += 1
            self.__pacoteFilaVozTotal[canal] = n
                
            return random.expovariate(0.65)*1000

        return 16

    def agendarChegadaFilaDados(self, lambd):
        if self.__testeDeCorretude == True:
            return 2.0/lambd

        return random.expovariate(lambd)

    def agendarTempoDeServicoFilaVoz(self, mi):
        if self.__testeDeCorretude == True:
            return 2.0/mi

        return random.expovariate(mi)

    def agendarTempoDeServicoFilaDados(self, mi):
        if self.__testeDeCorretude == True:
            return 2.0/mi

        return random.expovariate(mi)