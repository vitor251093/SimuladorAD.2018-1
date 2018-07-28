""" Classe Pacote que guardara todas as informacoes pertinentes ao Pacote,
    do momento que chega, ate o momento que sai do sistema. """

class Pacote(object):

    def __init__(self, id, tempoChegadaNoSistema, indiceDaCor, canal):
        self.__id = id

        self.__indiceDaCor = indiceDaCor
        self.__canal = canal # Usado apenas por pacotes de voz (0 a 29)

        self.__tempoChegadaFila = tempoChegadaNoSistema
        self.__tempoChegadaServico = 0.0
        self.__tempoServico = 0.0
        self.__tempoDecorridoServico = 0.0 # Usada em caso de interrupcao
        self.__tempoTerminoServico = 0.0

    ##############
    ## Setters
    ##############
    def setTempoChegadaServico(self, tempo):
        self.__tempoChegadaServico = tempo

    def setTempoServico(self, tempo):
        self.__tempoServico = tempo

    def setTempoTerminoServico(self, tempo):
        self.__tempoTerminoServico = tempo

    def setTempoDecorridoServico(self, tempo):
        self.__tempoDecorridoServico = tempo

    ###############
    ## Getters
    ###############
    def getID(self):
        return self.__id

    def getIndiceDaCor(self):
        return self.__indiceDaCor
    
    def getCanal(self):
        return self.__canal
    
    def getTempoChegadaFila(self):
        return self.__tempoChegadaFila

    def getTempoChegadaServicoVoz(self):
        return self.__tempoChegadaServicoVoz

    def getTempoServicoVoz(self):
        return self.__tempoServicoVoz

    def getTempoChegadaFilaDados(self):
        return self.__tempoChegadaFilaDados

    def getTempoServicoDados(self):
        return self.__tempoServicoDados

    def getTempoTerminoServicoDados(self):
        return self.__tempoTerminoServicoDados

    def getTempoDecorridoServicoDados(self):
        return self.__tempoDecorridoServicoDados

    ### Getters para calculos estatisticos
    def getTempoEsperaFilaVoz(self): # W1
        return self.getTempoChegadaServicoVoz() - self.getTempoChegadaFila()

    def getTempoTotalFilaVoz(self): # T1
        return self.getTempoEsperaFilaVoz() + self.getTempoServicoVoz()

    def getVarianciaTempoEsperaFilaVoz(self, esperancaTempoEsperaFilaVoz): #VW1
        return (self.getTempoEsperaFilaVoz() - esperancaTempoEsperaFilaVoz) ** 2


    def getTempoEsperaFilaDados(self): # W2
        return self.getTempoTerminoServicoDados() - self.getTempoChegadaFilaDados() - self.getTempoServicoDados()

    def getTempoTotalFilaDados(self): # T2
        return self.getTempoTerminoServicoDados() - self.getTempoChegadaFilaDados()

    def getVarianciaTempoEsperaFilaDados(self, esperancaTempoEsperaFilaDados): # VW2
        return (self.getTempoEsperaFilaDados() - esperancaTempoEsperaFilaDados) ** 2

    