import asyncio
from playwright.async_api import async_playwright
import pandas as pd
from typing import List, Dict
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

BASE_URL = "https://br.investing.com/indices/"

engine = create_engine(os.getenv("DB_URL"))
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

def create_tables() -> None:
    """Cria as tabelas no banco de dados, se não existirem."""
    Base.metadata.create_all(engine)

class Pais(Base):
    __tablename__ = "pais"
    id = Column(Integer, primary_key=True)
    nome = Column(String, unique=True, nullable=False)

class Setor(Base):
    __tablename__ = "setor"
    id = Column(Integer, primary_key=True)
    nome = Column(String, unique=True, nullable=False)

class IndiceFinanceiro(Base):
    __tablename__ = "indice_financeiro"
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    pais_id = Column(Integer, ForeignKey("pais.id"))
    setor_id = Column(Integer, ForeignKey("setor.id"))
    valor_atual = Column(Float)
    maxima = Column(Float)
    minima = Column(Float)
    variacao = Column(Float)
    data_coleta = Column(DateTime, default=datetime.utcnow)

URLS = {
    "Brasil": f"{BASE_URL}brazil-indices?include-major-indices=true&include-additional-indices=true&include-primary-sectors=true&include-other-indices=true",
    "China": f"{BASE_URL}china-indices?include-primary-sectors=true",
    "EUA": f"{BASE_URL}usa-indices?include-primary-sectors=true"
}

SETOR_POR_PAIS = {
    "China": "Primário",
    "EUA": "Primário"
}

SETOR_POR_INDICE_BRASIL = {
    "Ibovespa": "Financeiro",
    "IBrX 50": "Financeiro",
    "IBrX 100": "Financeiro",
    "Brasil Amplo IBrA": "Diversificado",
    "MidLarge Cap MLCX": "Indústria",
    "Small Cap SMLL": "Indústria",
    "Tag Along ITAG": "Financeiro",
    "Gov. Corporativa Novo Mercado IGC-NM": "Governança Corporativa",
    "Ibov Smart Dividendos": "Financeiro",
    "BDRs Não Patrocinados BDRX": "Internacional",
    "Inv. Imobiliários IFIX": "Imobiliário",
    "Carbono Eficiente ICO2": "Sustentabilidade",
    "Gov. Corporativa Trade IGCT": "Governança Corporativa",
    "FTSE Brazil": "Internacional",
    "Gov. Corporativa IGC": "Governança Corporativa",
    "IVBX 2": "Diversificado",
    "Dividendos IDIV": "Financeiro",
    "Ibovespa USD": "Câmbio",
    "Ibovespa EUR": "Câmbio",
    "IFIL": "Financeiro",
    "Indice de GPTW B3": "Governança Corporativa",
    "Sustentabilidade Empresarial": "Sustentabilidade",
    "S&P/B3 Ibovespa VIX": "Volatilidade",
    "Ibovespa B3 Br+": "Financeiro",
    "Bovespa B3 Estatais": "Financeiro",
    "Bovespa B3 Empresas Privada": "Financeiro"
}

async def buscar_indices_playwright(url: str, pais_nome: str) -> List[Dict[str, float]]:
    """Busca índices financeiros usando Playwright e retorna uma lista de dicionários."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)

        indices = []
        linhas = await page.query_selector_all("tbody tr")

        for linha in linhas:
            colunas = await linha.query_selector_all("td")
            if len(colunas) >= 6:
                try:
                    nome = await (await colunas[1].query_selector("a")).inner_text()
                    valor_atual = float((await colunas[2].inner_text()).strip().replace(".", "").replace(",", "."))
                    maxima = float((await colunas[3].inner_text()).strip().replace(".", "").replace(",", "."))
                    minima = float((await colunas[4].inner_text()).strip().replace(".", "").replace(",", "."))
                    variacao = float((await colunas[5].inner_text()).strip().replace(".", "").replace(",", ".").replace("+", "").replace("%", ""))

                    setor = SETOR_POR_INDICE_BRASIL.get(nome, "Diversificado") if pais_nome == "Brasil" else SETOR_POR_PAIS.get(pais_nome, "Primário")

                    indices.append({
                        "nome": nome,
                        "valor_atual": valor_atual,
                        "maxima": maxima,
                        "minima": minima,
                        "variacao": variacao,
                        "setor": setor
                    })
                except (ValueError, AttributeError):
                    continue

        await browser.close()
        return indices

def inserir_dados(df: pd.DataFrame, pais_nome: str) -> None:
    """Insere os índices financeiros no banco de dados usando SQLAlchemy."""
    pais = session.query(Pais).filter_by(nome=pais_nome).first()
    if not pais:
        pais = Pais(nome=pais_nome)
        session.add(pais)
        session.commit()

    for _, row in df.iterrows():
        setor = session.query(Setor).filter_by(nome=row["setor"]).first()
        if not setor:
            setor = Setor(nome=row["setor"])
            session.add(setor)
            session.commit()

        indice = IndiceFinanceiro(
            nome=row["nome"],
            pais_id=pais.id,
            setor_id=setor.id,
            valor_atual=row["valor_atual"],
            maxima=row["maxima"],
            minima=row["minima"],
            variacao=row["variacao"]
        )
        session.add(indice)
        session.commit()

def obter_top_10_indices() -> pd.DataFrame:
    """Recupera os 10 principais índices do setor primário da China e EUA com os maiores valores máximos."""
    query = session.query(IndiceFinanceiro.nome, Pais.nome.label("pais"), Setor.nome.label("setor"), IndiceFinanceiro.maxima)
    query = query.join(Pais, IndiceFinanceiro.pais_id == Pais.id)
    query = query.join(Setor, IndiceFinanceiro.setor_id == Setor.id)
    query = query.filter(Setor.nome == 'Primário', Pais.nome.in_(["China", "EUA"]))
    query = query.order_by(IndiceFinanceiro.maxima.desc()).limit(10)
    df = pd.DataFrame(query.all(), columns=["nome", "pais", "setor", "maxima"])
    return df

async def main() -> None:
    """Orquestra a coleta, armazenamento e exibição dos dados."""
    create_tables()

    dados_brasil = await buscar_indices_playwright(URLS["Brasil"], "Brasil")
    dados_china = await buscar_indices_playwright(URLS["China"], "China")
    dados_eua = await buscar_indices_playwright(URLS["EUA"], "EUA")

    df_brasil = pd.DataFrame(dados_brasil)
    df_china = pd.DataFrame(dados_china)
    df_eua = pd.DataFrame(dados_eua)

    inserir_dados(df_brasil, "Brasil")
    inserir_dados(df_china, "China")
    inserir_dados(df_eua, "EUA")

if __name__ == "__main__":
    asyncio.run(main())
    print(obter_top_10_indices())
