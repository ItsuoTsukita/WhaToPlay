
from datetime import datetime

import pandas as pd
import streamlit as st
from sklearn.feature_extraction import DictVectorizer
from sklearn.neighbors import NearestNeighbors

from steam_api import consultar_biblioteca

st.set_page_config(page_title="WhaToPlay?")


def separar(texto):
    return {item.strip().lower() for item in texto.split(",") if item.strip()}


def caracteristicas(generos, tags):
    atributos = {}
    for genero in separar(generos):
        atributos["genero:" + genero] = 1
    for tag in separar(tags):
        atributos["tag:" + tag] = 1
    return atributos


@st.cache_resource(show_spinner=False)
def carregar_jogos():
    jogos = pd.read_csv("Dados/jogos_tratados.csv", dtype={"appid": str}).fillna("")
    jogos = jogos.drop_duplicates("appid")
    jogos = jogos[
        ~jogos["nome"].str.contains(r"\b(?:Playtest|Demo|Soundtrack)\b", case=False, regex=True)
        & ~jogos["generos"].str.contains(
            "Utilities|Design & Illustration|Animation & Modeling", case=False, regex=True
        )
    ].reset_index(drop=True)

    jogos["positivas"] = pd.to_numeric(jogos["positivas"], errors="coerce").fillna(0)
    jogos["negativas"] = pd.to_numeric(jogos["negativas"], errors="coerce").fillna(0)
    total = jogos["positivas"] + jogos["negativas"]
    jogos["total_avaliacoes"] = total
    jogos["aprovacao"] = jogos["positivas"] / total.clip(lower=1)

    jogos["atributos"] = [
        caracteristicas(generos, tags)
        for generos, tags in zip(jogos["generos"], jogos["tags"])
    ]
    generos = sorted({
        genero.strip()
        for texto in jogos["generos"]
        for genero in texto.split(",")
        if genero.strip()
    })
    vetorizador = DictVectorizer()
    matriz = vetorizador.fit_transform(jogos["atributos"].tolist())
    return jogos, generos, vetorizador, matriz


def montar_perfil(jogos, escolhidos, biblioteca, recentes):
    perfil = {"genero:" + genero.lower(): 5 for genero in escolhidos}
    referencias = []
    ids = {str(jogo["appid"]) for jogo in biblioteca}
    catalogo = jogos[jogos["appid"].isin(ids)].set_index("appid")

    recentes_validos = [
        jogo for jogo in sorted(
            recentes, key=lambda item: item.get("playtime_2weeks", 0), reverse=True
        )
        if str(jogo["appid"]) in catalogo.index
        and jogo.get("playtime_2weeks", 0) >= 120
    ][:5]
    ids_recentes = {str(jogo["appid"]) for jogo in recentes_validos}

    mais_jogados = [
        jogo for jogo in sorted(
            biblioteca, key=lambda item: item.get("playtime_forever", 0), reverse=True
        )
        if str(jogo["appid"]) in catalogo.index
        and str(jogo["appid"]) not in ids_recentes
        and jogo.get("playtime_forever", 0) > 0
    ][:5]

    for lista, peso in [(recentes_validos, 2), (mais_jogados, 1)]:
        for jogo in lista:
            registro = catalogo.loc[str(jogo["appid"])]
            for atributo in registro["atributos"]:
                perfil[atributo] = perfil.get(atributo, 0) + peso
            referencias.append(registro)

    return perfil, referencias


def recomendar(candidatos, matriz, vetor_perfil):
    if candidatos.empty:
        return candidatos

    modelo = NearestNeighbors(metric="cosine", algorithm="brute")
    modelo.fit(matriz[candidatos.index.to_numpy()])
    distancias, indices = modelo.kneighbors(
        vetor_perfil, n_neighbors=min(100, len(candidatos))
    )
    resultado = candidatos.iloc[indices[0]].copy()
    resultado["pontuacao"] = 1 - distancias[0]
    return resultado[resultado["pontuacao"] > 0]


def explicar(jogo, escolhidos, referencias):
    generos = separar(jogo["generos"])
    if escolhidos:
        comuns = [genero for genero in escolhidos if genero.lower() in generos]
        return "Gêneros em comum: " + ", ".join(comuns)

    tags = separar(jogo["tags"])
    melhor_nome = ""
    melhores_generos = set()
    melhores_tags = set()
    maior = 0

    for referencia in referencias:
        comuns_generos = generos & separar(referencia["generos"])
        comuns_tags = tags & separar(referencia["tags"])
        pontos = 2 * len(comuns_generos) + len(comuns_tags)
        if pontos > maior:
            maior = pontos
            melhor_nome = referencia["nome"]
            melhores_generos = comuns_generos
            melhores_tags = comuns_tags

    if melhores_generos:
        return "Gêneros em comum com " + melhor_nome + ": " + ", ".join(sorted(melhores_generos))
    if melhores_tags:
        return "Tags em comum com " + melhor_nome + ": " + ", ".join(sorted(melhores_tags)[:3])
    return "Recomendado com base no histórico da Steam" if referencias else ""


def salvar_lista(tipo, jogos):
    lista = jogos.to_dict("records")
    quantidade = min(5, len(lista))
    st.session_state[tipo] = {
        "jogos": lista,
        "exibidos": list(range(quantidade)),
        "proximo": quantidade
    }


def trocar_jogo(tipo, posicao):
    lista = st.session_state[tipo]
    if lista["proximo"] < len(lista["jogos"]):
        lista["exibidos"][posicao] = lista["proximo"]
        lista["proximo"] += 1


def mostrar_jogos(tipo):
    lista = st.session_state[tipo]
    if not lista["exibidos"]:
        st.write("Nenhum jogo encontrado.")
        return

    for posicao, indice in enumerate(lista["exibidos"]):
        jogo = lista["jogos"][indice]
        imagem, texto = st.columns([1, 4])
        with imagem:
            if jogo["imagem"]:
                st.image(jogo["imagem"], width=120)
        with texto:
            st.write(f"**{jogo['nome']}**")
            st.write(jogo["generos"])
            if tipo == "biblioteca":
                info = st.session_state["biblioteca_usuario"].get(jogo["appid"], {})
                st.caption("Para retomar" if info.get("playtime_forever", 0) else "Ainda não jogado")
                if info.get("rtime_last_played", 0):
                    data = datetime.fromtimestamp(info["rtime_last_played"])
                    st.caption("Última execução: " + data.strftime("%d/%m/%Y"))
            else:
                st.caption(f"{round(jogo['aprovacao'] * 100)}% de avaliações positivas")

            motivo = explicar(jogo, st.session_state["escolhidos"], st.session_state["referencias"])
            if motivo:
                st.caption(motivo)
            st.markdown(f"[Ver na Steam](https://store.steampowered.com/app/{jogo['appid']}/)")
            st.button(
                "Trocar", key=f"{tipo}_{posicao}",
                on_click=trocar_jogo, args=(tipo, posicao),
                disabled=lista["proximo"] >= len(lista["jogos"])
            )


jogos, generos, vetorizador, matriz = carregar_jogos()
st.title("WhaToPlay?")

with st.form("formulario"):
    steamid = st.text_input("SteamID")
    escolhidos = st.multiselect("Selecione os gêneros", generos)
    enviar = st.form_submit_button("Recomendar")

if enviar:
    st.session_state["modo"] = None
    biblioteca, recentes = [], []
    if steamid.strip():
        biblioteca, recentes, erro = consultar_biblioteca(steamid.strip())
        if erro:
            st.warning(erro)

    if not escolhidos and not biblioteca:
        st.warning("Selecione um gênero ou informe um SteamID64 válido.")
    else:
        perfil, referencias = montar_perfil(jogos, escolhidos, biblioteca, recentes)
        if not perfil:
            st.warning("Não foi possível identificar preferências. Selecione um gênero.")
        else:
            vetor_perfil = vetorizador.transform([perfil])
            candidatos = jogos
            if escolhidos:
                generos_escolhidos = {genero.lower() for genero in escolhidos}
                candidatos = jogos[
                    jogos["generos"].apply(
                        lambda texto: bool(separar(texto) & generos_escolhidos)
                    )
                ]

            st.session_state["escolhidos"] = escolhidos
            st.session_state["referencias"] = referencias
            ids = {str(jogo["appid"]) for jogo in biblioteca}

            ids_jogados_recentemente = {str(jogo["appid"]) for jogo in recentes}
            novos = candidatos[~candidatos["appid"].isin(ids | ids_jogados_recentemente)]
            novos = novos[
                (novos["total_avaliacoes"] >= 3000)
                & (novos["aprovacao"] >= 0.80)
            ]

            if biblioteca:
                ids_recentes = {
                    str(jogo["appid"]) for jogo in recentes
                    if jogo.get("playtime_2weeks", 0) > 0
                }
                da_biblioteca = candidatos[
                    candidatos["appid"].isin(ids)
                    & ~candidatos["appid"].isin(ids_recentes)
                ]
                st.session_state["biblioteca_usuario"] = {
                    str(jogo["appid"]): jogo for jogo in biblioteca
                }
                salvar_lista("biblioteca", recomendar(da_biblioteca, matriz, vetor_perfil))
                salvar_lista("novos", recomendar(novos, matriz, vetor_perfil))
                st.session_state["modo"] = "steam"
            else:
                salvar_lista("geral", recomendar(novos, matriz, vetor_perfil))
                st.session_state["modo"] = "geral"

if st.session_state.get("modo") == "steam":
    st.subheader("Jogos da biblioteca")
    mostrar_jogos("biblioteca")
    st.subheader("Novos jogos")
    mostrar_jogos("novos")
elif st.session_state.get("modo") == "geral":
    st.subheader("Jogos recomendados")
    mostrar_jogos("geral")
