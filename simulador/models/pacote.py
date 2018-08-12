""" Classe Pacote que guardara todas as informacoes pertinentes ao Pacote,
    do momento que chega, ate o momento que sai do sistema. """

class Pacote(object):

    def __init__(self, id, tempoChegadaNoSistema, indiceDaCor, canal=-1, indiceEmCanal=0, servico=0):
        self.__id = id

        self.__indiceDaCor = indiceDaCor
        self.__canal = canal # Usado apenas por pacotes de voz (0 a 29)
        self.__indice_em_canal = indiceEmCanal
        self.__servico = servico

        self.__tempoChegadaFila = tempoChegadaNoSistema
        self.__tempoChegadaServico = 0.0
        self.__tempoServico = 0.0
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

    ###############
    ## Getters
    ###############
    def getID(self):
        return self.__id

    def getIndiceDaCor(self):
        return self.__indiceDaCor

    def getServico(self):
        return self.__servico
    
    def getCanal(self):
        return self.__canal

    def getIndiceEmCanal(self):
        return self.__indice_em_canal

    def ehPacoteDeVoz(self):
        return self.__canal != -1
    
    def getTempoChegadaFila(self):
        return self.__tempoChegadaFila

    def getTempoChegadaServico(self):
        return self.__tempoChegadaServico

    def getTempoServico(self):
        return self.__tempoServico

    def getTempoTerminoServico(self):
        return self.__tempoTerminoServico

    ### Getters para calculos estatisticos
    def getTempoEsperaFila(self): # W1/2
        return self.getTempoChegadaServico() - self.getTempoChegadaFila()

    def getTempoTotalServico(self): # X1/2
        return self.getTempoTerminoServico() - self.getTempoChegadaServico()
    
    def getTempoTotalSistema(self): # T1/2
        return self.getTempoTerminoServico() - self.getTempoChegadaFila()


    def getVarianciaTempoEsperaFila(self, esperancaTempoEsperaFila): # VW1/2
        return (self.getTempoEsperaFila() - esperancaTempoEsperaFila) ** 2

    