# ai-summit-hackaton-backend


# initialisation
pip install langgraph-cli
pip install uv

## installation des dépendances (avec uv)
uv venv # création de l'environnement virtuel 
source .venv/bin/activate # activation de l'environnement
uv pip install -e . # installation d dépendances du fichier toml

# test local
uv run langgraph dev
