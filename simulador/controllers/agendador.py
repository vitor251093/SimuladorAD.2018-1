import random

""" O Agendador sera responsavel por agendar chegadas e servicos
    de acordo com as taxas lambda e mi, respectivamente."""

class Agendador(object):

    def __init__(self):
        self.__testeDeCorretude = False

    def setTesteDeCorretude(self, testeDeCorretude):
        self.__testeDeCorretude = testeDeCorretude

    def configurarSemente(self, seed):
        if self.__testeDeCorretude == True:
            return
        
        random.seed(seed)

    def agendarChegadaFilaVoz(self, lambd):
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