from pacote import *

class Fila(object):

    def __init__(self, id):
        self.__id = id
        self.__pacotes = []

    # Retorna Pacote e remove do topo da array
    def retirarPacoteEmAtendimento(self):
        Pacote = self.__pacotes[0]
        self.__pacotes.pop(0)
        return Pacote

    # Entra com um Pacote
    def adicionarPacoteAFila(self, Pacote):
        self.__pacotes.append(Pacote)

    # Retorna o Pacote no indice zero (ponteiro)
    def PacoteEmAtendimento(self):
        return self.__pacotes[0]

    # Numero de pacotes na fila
    def numeroDePacotesNaFila(self):
        return len(self.__pacotes)

    def numeroDePacotesNaFilaDeCanal(self, canal):
        count = 0
        for pacote in self.__pacotes:
            if pacote.ehPacoteDeVoz() and pacote.getCanal() == canal:
                count += 1
        return count

    # Getters
    def getID(self):
        return self.__id

    # Setters
    def setID(self,id):
        self.__id = id