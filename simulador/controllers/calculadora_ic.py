import math
import scipy.stats

class CalculadoraIC(object):

    def __init__(self, intervaloDeConfianca):
        self.__intervaloDeConfianca = intervaloDeConfianca

    def tabelaTStudent(self, grausDeLiberdade):
        return scipy.stats.t.ppf(1 - self.__intervaloDeConfianca, grausDeLiberdade)

    def intervaloDeConfiancaDeAmostras(self, amostrasOriginal, tamanho):
        n = tamanho
        if n <= 1:
            return 0, 0

        amostras = list(amostrasOriginal)

        countAmostral = 0
        mediaAmostral = 0.0
        for amostra in amostras:
            if amostra != None:
                mediaAmostral += amostra
                countAmostral += 1
        
        if countAmostral == 0:
            return -1, -1

        mediaAmostral /= countAmostral

        grausDeLiberdade = (countAmostral - 1)
        tc = self.tabelaTStudent(grausDeLiberdade)

        desvioPadrao = 0.0
        for amostra in amostras:
            if amostra != None:
                desvioPadrao += (amostra - mediaAmostral) ** 2
        desvioPadrao /= grausDeLiberdade
        desvioPadrao = math.sqrt(desvioPadrao)

        variancaoDoIntervalo = abs(tc * (desvioPadrao / math.sqrt(n)))
        intervaloBaixo = mediaAmostral - variancaoDoIntervalo
        intervaloAlto  = mediaAmostral + variancaoDoIntervalo

        intervaloValido = (variancaoDoIntervalo*10 < mediaAmostral)
        intervaloValidoString = "valido" if intervaloValido else "invalido"

        return intervaloBaixo, intervaloAlto, intervaloValidoString

