import os
from time import gmtime, strftime
import shutil

class View(object):
    def __init__(self, printing):
        self.__save_at_file = False
        self.__output_file = None
        self.__output_text = ""
        self.__index = -1
        self.__entries_per_file = 100
        self.__printing = printing
        shutil.rmtree('/simulador/templates/plot')
        newpath = r'/simulador/templates/plot'
        os.makedirs(newpath)
        
    def setImprimirEmArquivo(self, imprimirEmArquivo):
        self.__save_at_file = imprimirEmArquivo

    def gravarArquivoDeSaida(self):
        if self.__save_at_file == False:
            return self.__output_text
        else:
            self.__output_file.write("%s\n" % (self.__output_text))
            self.__output_file.close()
            return ''

    """Imprime textos para o programa"""
    def imprimir(self, texto):
        if self.__printing:
            print texto

        self.__output_text = "%s\n%s" % (self.__output_text, texto)

        if self.__save_at_file == True:
            # Imprime um texto no arquivo de texto
            self.__index += 1

            separateBy = self.__entries_per_file
            if self.__index % separateBy == 0:
                if self.__output_file != None:
                    self.__output_file.write("%s\n" % (self.__output_text))
                    self.__output_file.close()
                    self.__output_text = ""
                file_path = "/simulador/templates/plot/%d.csv" % (self.__index / separateBy)
                self.__output_file = open(file_path, "w")

