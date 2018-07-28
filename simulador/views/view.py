import os
from time import gmtime, strftime

class View(object):
    def __init__(self):
        self.__output_file = None
        
    def setImprimirEmArquivo(self, imprimirEmArquivo):
        if imprimirEmArquivo == True:
            dir_path = os.path.dirname(os.path.abspath(__file__))
            file_path = "/../../plot/%s.csv" % (strftime("%Y-%m-%d %H.%M.%S", gmtime()))
            self.__output_file = open(dir_path + file_path, "w")
        else:
            self.__output_file = None

    def gravarArquivoDeSaida(self):
        self.__output_file.close()

    """Imprime textos para o programa"""
    def imprimir(self, texto):
        if self.__output_file == None:
            # Imprime um texto na tela
            print texto
        else:
            # Imprime um texto no arquivo de texto
            self.__output_file.write("%s\n" % (texto))
