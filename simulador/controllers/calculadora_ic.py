import math
import scipy.stats

class CalculadoraIC(object):

    def __init__(self, intervaloDeConfianca):
        self.__intervaloDeConfianca = intervaloDeConfianca

    def tabelaTStudent(self, grausDeLiberdade):
        return scipy.stats.t.ppf(1 - self.__intervaloDeConfianca, grausDeLiberdade)

    def intervaloDeConfiancaDeAmostras(self, amostras):
        n = len(amostras)
        grausDeLiberdade = (n - 1)
        tc = self.tabelaTStudent(grausDeLiberdade)

        mediaAmostral = 0.0
        for amostra in amostras:
            mediaAmostral += amostra
        mediaAmostral /= n

        desvioPadrao = 0.0
        for amostra in amostras:
            desvioPadrao += (amostra - mediaAmostral) ** 2
        desvioPadrao /= grausDeLiberdade
        desvioPadrao = math.sqrt(desvioPadrao)

        variancaoDoIntervalo = tc * (desvioPadrao / math.sqrt(n))
        intervaloBaixo = mediaAmostral - variancaoDoIntervalo
        intervaloAlto  = mediaAmostral + variancaoDoIntervalo

        return intervaloBaixo, intervaloAlto

    def intervaloDeConfiancaDeAmostrasComMedia(self, amostras, mediaAmostral):
        n = len(amostras)
        grausDeLiberdade = (n - 1)
        tc = self.tabelaTStudent(grausDeLiberdade)

        desvioPadrao = 0.0
        for amostra in amostras:
            desvioPadrao += (amostra - mediaAmostral) ** 2
        desvioPadrao /= grausDeLiberdade
        desvioPadrao = math.sqrt(desvioPadrao)

        variancaoDoIntervalo = tc * (desvioPadrao / math.sqrt(n))
        intervaloBaixo = mediaAmostral - variancaoDoIntervalo
        intervaloAlto  = mediaAmostral + variancaoDoIntervalo

        return intervaloBaixo, intervaloAlto
