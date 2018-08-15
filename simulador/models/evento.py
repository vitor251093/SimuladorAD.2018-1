class Evento(object):

    def __init__(self, tipo, canal, distancia, indiceEmCanal=0, servico=0):
        self.tipo = tipo
        self.canal = canal
        self.tempoRestante = distancia
        self.indiceEmCanal = indiceEmCanal
        self.servico = servico
