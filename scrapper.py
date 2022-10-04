import dataclasses
import datetime
import json
import os
import re
from dataclasses import dataclass

from dataclasses_json import dataclass_json
from time import sleep
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select


@dataclass_json
@dataclass
class PesquisaEleitoralCandidato:
    candidato_nome: str
    partido: str
    valor_referencia: float
    data_publicacao: datetime.datetime
    instituto_nome: str
    resultado_tse: float
    margem_erro: int
    diferenca: float
    acertou_posicao: bool
    acertou_margem: bool


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


def obter_data(cabecalho):
    return datetime.datetime.now()


def obter_resultado_tse(nome_candidato):
    return 0


def calcular_diferenca(valor, valor_tse):
    return valor-valor_tse


def obter_valor(linha):
    resultado = re.search(".{4}%", linha)
    if resultado:
        return float(resultado.group(0)[0:4])
    return .0


def obter_nome_candidato(linha):
    resultado = linha.split(" ")
    if resultado and len(resultado) > 3:
        return ' '.join(resultado[:-2])
    return ""


def obter_partido(linha):
    resultado = linha.split(" ")
    if resultado and len(resultado) > 3:
        return resultado[len(resultado)-2]
    return ""


def verificar_posicao():
    return False


def verificar_margem(diferenca, margem_erro):
    return diferenca <= margem_erro


def obter_margem_erro():
    return 0


def criar_registro_pesquisa(intituto, margem_erro):
    tabela = driver.find_element(By.CLASS_NAME, "poll")
    cabecalho = tabela.find_elements(By.TAG_NAME, 'tr')[:1]
    data = obter_data(cabecalho)
    linhas = tabela.find_elements(By.TAG_NAME, 'tr')[1:-2]
    resultados = []
    for linha in linhas:
        texto_linha = linha.text
        nome_candidato = obter_nome_candidato(texto_linha)
        valor_tse = obter_resultado_tse(nome_candidato)
        valor = obter_valor(texto_linha)
        diferenca = calcular_diferenca(valor, valor_tse)
        resultado = PesquisaEleitoralCandidato(
            candidato_nome=nome_candidato, partido=obter_partido(texto_linha), valor_referencia=valor,
            data_publicacao=data, instituto_nome=intituto, resultado_tse=valor_tse,
            margem_erro=margem_erro, diferenca=diferenca,
            acertou_posicao=verificar_posicao(),
            acertou_margem=verificar_margem(diferenca, margem_erro)
        )
        resultados.append(resultado)
    return resultados


options = Options()
options.headless = True
load_dotenv()
webdriver_path = os.getenv('WEBDRIVER_PATH')
driver = webdriver.Chrome(options=options, executable_path=webdriver_path)




try:
    base_url = f'https://www.poder360.com.br/agregador-de-pesquisas/'
    sleep(0.1)
    driver.get(base_url)
    sleep(0.5)
    selects = driver.find_elements(By.TAG_NAME, "select")
    select_cargos = selects[0]
    cargos = [x.get_attribute('value') for x in select_cargos.find_elements(By.TAG_NAME, "option")]
    select_ambitos = selects[1]
    ambitos = [x.get_attribute('value') for x in select_ambitos.find_elements(By.TAG_NAME, "option")][1:]
    select_anos = selects[2]
    ano = [x.get_attribute('value') for x in select_anos.find_elements(By.TAG_NAME, "option")]
    select_turnos = selects[3]
    turnos = [x.get_attribute('value') for x in select_turnos.find_elements(By.TAG_NAME, "option")]


    for cargo in cargos:
        Select(select_cargos).select_by_value(cargo)
        sleep(0.5)
        if cargo != 'Presidente':
            for ambito in ambitos:
                Select(select_ambitos).select_by_value(ambito)
                select_institutos = driver.find_elements(By.TAG_NAME, "select")[7]
                institutos_pesquisa = [x.get_attribute('value') for x in
                                       select_institutos.find_elements(By.TAG_NAME, "option")][1:]
                sleep(0.5)
                for instituto in institutos_pesquisa:
                    try:
                        nome_arquivo = instituto+ambito+cargo
                        Select(select_institutos).select_by_value(instituto)
                        sleep(0.5)
                        resultados = criar_registro_pesquisa(instituto, obter_margem_erro())
                        resultados_compilados = PesquisaEleitoralCandidato.schema().dumps(resultados, many=True)
                        with open(f'data/{nome_arquivo}.json', 'w') as f:
                            f.write(resultados_compilados)
                            print(f'{nome_arquivo}.json was created')
                    except:
                        pass
finally:
    driver.quit()
