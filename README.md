COMO EXECUTAR O WHATOPLAY?

1. Instale o Python 3.12 ou superior.

2. Abra o terminal na pasta principal do projeto e instale as bibliotecas necessárias:

python -m pip install pandas streamlit requests python-dotenv ijson scikit-learn

3. Para utilizar o histórico de jogos da Steam, crie um arquivo .env na pasta principal do projeto com o conteúdo:

STEAM_API_KEY=sua_steam_api_key

A Steam API Key pode ser obtida em:
https://steamcommunity.com/dev/apikey

Essa configuração é opcional. Sem ela, o programa funciona utilizando apenas os gêneros selecionados.

4. Para localizar o SteamID:

- Abra a Steam e clique no nome da sua conta.
- Acesse Detalhes da conta.
- Localize o ID Steam, um número de 17 dígitos exibido abaixo do nome da conta.


5. O dataset original games.json pode ser baixado em:

https://www.kaggle.com/datasets/fronkongames/steam-games-dataset/data

O arquivo jogos_tratados.csv já está incluído na pasta Dados, portanto não é necessário baixar o JSON original para executar o programa.

Para gerar novamente o CSV, coloque games.json na pasta Dados e execute:

python src/main.py

6. Para iniciar o programa, execute na pasta principal do projeto:

python -m streamlit run src/app.py

7. O WhaToPlay? será aberto no navegador. Caso isso não aconteça, acesse:

http://localhost:8501

8. Selecione os gêneros desejados ou informe seu SteamID e clique em Recomendar.
