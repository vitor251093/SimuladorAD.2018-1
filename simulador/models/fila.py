from pacote import *

class Fila(object):

    def __init__(self, id):
        self.id = id
        self.__pacotes = []

    # Retorna Pacote e remove do topo da array
    def retirarPacoteEmAtendimento(self):
        return self.__pacotes.pop(0)

    # Entra com um Pacote
    def adicionarPacoteAFila(self, pacote):
        self.__pacotes.append(pacote)

    # Retorna o Pacote no indice zero (ponteiro)
    def pacoteEmAtendimento(self):
        return self.__pacotes[0]

    # Numero de pacotes na fila
    def numeroDePacotesNaFila(self):
        return len(self.__pacotes)

    def numeroDePacotesNaFilaDeCanal(self, canal):
        count = 0
        for pacote in self.__pacotes:
            if pacote.canal == canal:
                count += 1
        return count
