""" Classe Pacote que guardara todas as informacoes pertinentes ao Pacote,
    do momento que chega, ate o momento que sai do sistema. """

class Pacote(object):

    def __init__(self, id, tempoChegadaNoSistema, indiceDaCor, canal=-1, indiceEmCanal=0, servico=0):
        self.id = id

        self.indiceDaCor = indiceDaCor
        self.canal = canal # Usado apenas por pacotes de voz (0 a 29)
        self.indiceEmCanal = indiceEmCanal
        self.servico = servico

        self.tempoChegadaFila = tempoChegadaNoSistema
        self.tempoChegadaServico = 0.0
        self.tempoServico = 0.0
        self.tempoTerminoServico = 0.0

    ###############
    ## Getters
    ###############
    
    ### Getters para calculos estatisticos
    def getTempoEsperaFila(self): # W1/2
        return self.tempoChegadaServico - self.tempoChegadaFila

    def getTempoTotalServico(self): # X1/2
        return self.tempoTerminoServico - self.tempoChegadaServico
    
    def getTempoTotalSistema(self): # T1/2
        return self.tempoTerminoServico - self.tempoChegadaFila


    def getVarianciaTempoEsperaFila(self, esperancaTempoEsperaFila): # VW1/2
        return ((self.tempoChegadaServico - self.tempoChegadaFila) - esperancaTempoEsperaFila) ** 2

    