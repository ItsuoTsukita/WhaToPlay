
import csv
import ijson

quantidade = 0

with open("Dados/games.json", "rb") as entrada:
    with open("Dados/jogos_tratados.csv", "w", encoding="utf-8-sig", newline="") as saida:
        escritor = csv.writer(saida)

        escritor.writerow([
            "appid", "nome", "generos", "tags",
            "imagem", "positivas", "negativas"
        ])

        for appid, jogo in ijson.kvitems(entrada, ""):
            nome = jogo.get("name") or ""
            generos = jogo.get("genres") or []
            tags = jogo.get("tags") or {}

            if not nome or (not generos and not tags):
                continue

            escritor.writerow([
                appid,
                nome,
                ", ".join(generos),
                ", ".join(list(tags.keys())[:12]),
                jogo.get("header_image") or "",
                jogo.get("positive") or 0,
                jogo.get("negative") or 0
            ])

            quantidade += 1

print("Jogos preparados:", quantidade)
print("Arquivo criado: Dados/jogos_tratados.csv")
