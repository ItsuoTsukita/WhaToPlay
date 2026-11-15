
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")


def consultar_biblioteca(steamid):
    chave = os.getenv("STEAM_API_KEY", "").strip()

    if not chave:
        return [], [], "Chave da Steam não configurada."

    if not steamid.isdigit() or len(steamid) != 17:
        return [], [], "SteamID64 inválido."

    url = "https://api.steampowered.com/IPlayerService/"

    try:
        resposta = requests.get(
            url + "GetOwnedGames/v1/",
            params={
                "key": chave,
                "steamid": steamid,
                "include_appinfo": 1,
                "include_played_free_games": 1
            },
            timeout=20
        )

        resposta.raise_for_status()
        biblioteca = resposta.json().get("response", {}).get("games", [])

        if not biblioteca:
            return [], [], "Biblioteca não encontrada ou privada."

        resposta = requests.get(
            url + "GetRecentlyPlayedGames/v1/",
            params={"key": chave, "steamid": steamid},
            timeout=20
        )

        resposta.raise_for_status()
        recentes = resposta.json().get("response", {}).get("games", [])

        return biblioteca, recentes, ""

    except (requests.RequestException, ValueError):
        return [], [], "Não foi possível consultar a Steam."
