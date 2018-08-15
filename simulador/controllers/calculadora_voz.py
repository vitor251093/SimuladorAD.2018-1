
class CalculadoraVoz(object):

    @staticmethod
    def varianciaPorPeriodosDeChegadasDePacotesDeVoz(todosOsPacotesVoz):
        valoresJ = []
        somatorioJ = []
        
        for pacote in todosOsPacotesVoz:
            if pacote.tempoChegadaServico != 0:
                servico = pacote.servico # 0+
                indice = pacote.indiceEmCanal # 1+
                canal = pacote.canal # 0+
                
                indiceValor = (servico*30 + canal)
                while indiceValor >= len(somatorioJ):
                    valoresJ.append([])
                    somatorioJ.append(-1)
                    
                chegada = pacote.tempoChegadaServico/1000.0 # segundos
                valoresJ[indiceValor].append(chegada)
                if somatorioJ[indiceValor] == -1:
                    somatorioJ[indiceValor] = 0
                somatorioJ[indiceValor] += chegada

        mediaIntervaloDeChegadaPorPeriodo = []
        for indice in xrange(len(somatorioJ)):
            mediaIntervaloDeChegadaPorPeriodo.append(somatorioJ[indice]/len(valoresJ[indice]) if len(valoresJ[indice]) != 0 else 0)

        varianciaPorPeriodos = [] # Delta J
        for servico in xrange(len(valoresJ)):
            if mediaIntervaloDeChegadaPorPeriodo[servico] != 0:
                varianciaPorPeriodo = 0
                if len(valoresJ[servico]) > 0:
                    for canal in xrange(len(valoresJ[servico])):
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
                vdeltaJ += ((varianciaPorPeriodo - esperancaDaVarianciaPorFase[fase.id]) ** 2)
            vdeltaJ /= (len(varianciaPorPeriodos) - 1)
            varianciaDaVarianciaPorFase.append(vdeltaJ)

        varianciaDaVarianciaTotal = 0 # V(Delta)
        for varianciaDaVariancia in varianciaDaVarianciaPorFase:
            varianciaDaVarianciaTotal += varianciaDaVariancia
        varianciaDaVarianciaTotal /= len(varianciaDaVarianciaPorFase)

        return esperancaDaVarianciaPorFase, esperancaDaVarianciaTotal, varianciaDaVarianciaPorFase, varianciaDaVarianciaTotal
