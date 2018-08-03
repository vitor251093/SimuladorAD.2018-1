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

    def getTempoChegadaServico(self):
        return self.__tempoChegadaServico

    def getTempoServico(self):
        return self.__tempoServico

    def getTempoTerminoServico(self):
        return self.__tempoTerminoServico

    def getTempoDecorridoServico(self):
        return self.__tempoDecorridoServico

    ### Getters para calculos estatisticos
    def getTempoEsperaFila(self): # W2
        return self.getTempoTerminoServico() - self.getTempoChegadaFila() - self.getTempoServico()

    def getTempoTotalSistema(self): # T2
        return self.getTempoTerminoServico() - self.getTempoChegadaFila()

    def getVarianciaTempoEsperaFila(self, esperancaTempoEsperaFila): # VW2
        return (self.getTempoEsperaFila() - esperancaTempoEsperaFila) ** 2

    