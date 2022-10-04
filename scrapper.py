import dataclasses
import datetime
import json
import os
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from time import sleep
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


@dataclass_json
@dataclass
class PesquisaEleitoralCandidato:
    candidato_nome: str
    partido: str
    valor_referencia: int
    data_publicacao: datetime.datetime
    instituto_nome: str
    resultado_tse: int
    margem_erro: int
    diferenca: int
    acertou_posicao: bool
    acertou_margem: bool


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


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
    ambitos = [x.get_attribute('value') for x in select_ambitos.find_elements(By.TAG_NAME, "option")]
    select_anos = selects[2]
    ano = [x.get_attribute('value') for x in select_anos.find_elements(By.TAG_NAME, "option")]
    select_turnos = selects[3]
    turnos = [x.get_attribute('value') for x in select_turnos.find_elements(By.TAG_NAME, "option")]
    select_institutos = selects[7]
    instituto_pesquisa = [x.get_attribute('value') for x in select_institutos.find_elements(By.TAG_NAME, "option")][:1]

finally:
    driver.quit()