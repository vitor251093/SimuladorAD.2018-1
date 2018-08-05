class Evento(object):

    def __init__(self, tipo, canal, distancia, indiceEmCanal=0):
        self.__tipo = tipo
        self.__canal = canal
        self.__distancia = distancia
        self.__indiceEmCanal = indiceEmCanal

    # Retorna Pacote e remove do topo da array
    def tipo(self):
        return self.__tipo

    def canal(self):
        return self.__canal

    def avancarTempo(self, tempo):
        self.__distancia -= tempo

    def tempoRestante(self):
        return self.__distancia

    def indiceEmCanal(self):
        return self.__indiceEmCanal
