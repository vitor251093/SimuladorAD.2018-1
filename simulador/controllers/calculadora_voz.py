
class CalculadoraVoz(object):

    @staticmethod
    def varianciaPorPeriodosDeChegadasDePacotesDeVoz(todosOsPacotesVoz):
        valoresJ = []
        somatorioJ = []
        
        for pacote in todosOsPacotesVoz:
            servico = pacote.getServico() # 0+
            indice = pacote.getIndiceEmCanal() # 1+
            canal = pacote.getCanal() # 0+
            
            indiceValor = (servico*30 + canal)
            while indiceValor >= len(somatorioJ):
                valoresJ.append([])
                somatorioJ.append(-1)
                
            chegada = pacote.getTempoChegadaFila()/1000.0 # segundos
            valoresJ[indiceValor].append(chegada)
            if somatorioJ[indiceValor] == -1:
                somatorioJ[indiceValor] = 0
            somatorioJ[indiceValor] += chegada

        mediaIntervaloDeChegadaPorPeriodo = []
        for indice in range(len(somatorioJ)):
            if somatorioJ[indice] != -1:
                mediaIntervaloDeChegadaPorPeriodo.append(somatorioJ[indice]/len(valoresJ[indice]) if len(valoresJ[indice]) != 0 else 0)

        varianciaPorPeriodos = [] # Delta J
        for servico in range(len(valoresJ)):
            varianciaPorPeriodo = 0
            if len(valoresJ[servico]) > 0:
                for canal in range(len(valoresJ[servico])):
                    varianciaPorCanal = (valoresJ[servico][canal] - mediaIntervaloDeChegadaPorPeriodo[servico]) ** 2
                    varianciaPorPeriodo += varianciaPorCanal
                
                varianciaPorPeriodo /= len(valoresJ[servico])
                varianciaPorPeriodos.append(varianciaPorPeriodo)

        return varianciaPorPeriodos

    @staticmethod
    def esperancaEVarianciaDaVarianciaDeChegadasDePacotesDeVoz(fases):
        esperancaDaVarianciaPorFase = [] # E[DeltaK]
        for fase in fases:
            deltaJ = 0
            varianciaPorPeriodos = fase.varianciaPorPeriodosDeChegadasDePacotesDeVoz() # Delta J
            for varianciaPorPeriodo in varianciaPorPeriodos:
                deltaJ += varianciaPorPeriodo
            if len(varianciaPorPeriodos) > 0:
                deltaJ /= len(varianciaPorPeriodos)
            esperancaDaVarianciaPorFase.append(deltaJ)
        
        esperancaDaVarianciaTotal = 0 # E[Delta]
        for esperancaDaVariancia in esperancaDaVarianciaPorFase:
            esperancaDaVarianciaTotal += esperancaDaVariancia
        esperancaDaVarianciaTotal /= len(esperancaDaVarianciaPorFase)

        varianciaDaVarianciaPorFase = [] # V(DeltaK)
        for fase in fases:
            vdeltaJ = 0
            varianciaPorPeriodos = fase.varianciaPorPeriodosDeChegadasDePacotesDeVoz() # Delta J
            for varianciaPorPeriodo in varianciaPorPeriodos:
                vdeltaJ += ((varianciaPorPeriodo - esperancaDaVarianciaPorFase[fase.getID()]) ** 2)
            vdeltaJ /= (len(varianciaPorPeriodos) - 1)
            varianciaDaVarianciaPorFase.append(vdeltaJ)

        varianciaDaVarianciaTotal = 0 # V(Delta)
        for varianciaDaVariancia in varianciaDaVarianciaPorFase:
            varianciaDaVarianciaTotal += varianciaDaVariancia
        varianciaDaVarianciaTotal /= len(varianciaDaVarianciaPorFase)

        return esperancaDaVarianciaPorFase, esperancaDaVarianciaTotal, varianciaDaVarianciaPorFase, varianciaDaVarianciaTotal
