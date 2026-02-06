# Disclaimer

This walkthrough was done prior to the release of this : https://amp-docs.prod.corp.mongodb.com/demo. It is likely to be outdated. 

Steps needed to update this demo : 
- demo App Analysis : https://docs.google.com/document/d/1QVOejKQbIaAg15Rt90SC5iDtHvDnELJvDczcc6sogv0/edit?tab=t.0#heading=h.netk7m96ltqz 
- https://docs.google.com/document/d/172k15o9cPSkxy73R_Hh9ZmYWxNvMnMK8MeRWn31lr9E/edit?tab=t.0 : show more of relational migration modeling
- build the target app and run API calls to check it gives same results as source app

# PreReq

- Python 3.11 and uv package manager
- Node.js 24.x+
- Docker Desktop (latest stable version)
- Git
- JDK21
- Acces 1 password vault 
- Accept on github the invitation to modernization-factory/modfac-PS/legacy-demo-app
- Create a classic Personal Access Token (PAT) in Github on the github repo (https://github.com/Modernization-Factory/legacy-demo-app ) with these scopes : read:packages, repo, workflow
- configure SSO on this PAT and authorize the token for modernization factory.

# Clone Legacy app
git clone with the PAT : 
```sh
git clone https://hbrulin-mdb:<PAT>@github.com/Modernization-Factory/legacy-demo-app.git
```

# App analysis
```sh
brew install git-lfs

docker run -d --name neo4j-gds -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=none -e 'NEO4J_PLUGINS=["graph-data-science"]' -e 'NEO4J_dbms_security_procedures_unrestricted=gds.*' neo4j:5.15.0
```

http://localhost:7474/ - set credentiels : hbrulin - pwd

Note : 
- After the demo, run neo4j stop before stopping the container
- If you stop the neo4j Docker container w/out first stopping neo4j (neo4j stop), neo4j will fail to restart with the message "neo4j is already running". To rectify, stop, remove, and recreate the container: docker stop neo4j-gds, docker rm neo4j-gds, Create the container again using the command above

## run the following command to clone the repository containing the analysis tools (JSCA/SPDA) and switch to the demo branch:
```sh
git clone https://github.com/Modernization-Factory/app-analysis.git && cd app-analysis && git fetch && git checkout demo/legacy-demo-app
```

## Run the following command from the root directory (app-analysis) to install the frontend and backend dependencies:
```sh
cd frontend && npm install && cd .. && uv venv .venv && source .venv/bin/activate && cd backend && uv sync --all-groups
```


## Create env file in backend folder
```sh
# Default LLM model name
APP_MOD_DEFAULT_LLM_MODEL="azure-openai" # See llm_config.yaml for available models

# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=""
AZURE_API_BASE="https://gabriel-gpn-openai.openai.azure.com"
AZURE_DEPLOYMENT_NAME="o4-mini"
AZURE_API_VERSION="2024-12-01-preview"

# Neo4j configurtation
APP_MOD_NEO4J_HOST= 127.0.0.1
APP_MOD_NEO4J_PORT= 7687
# APP_MOD_NEO4J_PORT= 7588

APP_MOD_JRE_21_HOME="/Library/Java/JavaVirtualMachines/openjdk-21.jdk/Contents/Home"
APP_MOD_JRE_21_JAVA="/usr/bin/java"
```

## Test config
```sh
uv run -m src.cli_main app-analysis source-code --help
```
-> see in this doc the expected output : https://docs.google.com/document/d/172k15o9cPSkxy73R_Hh9ZmYWxNvMnMK8MeRWn31lr9E/edit?tab=t.0

## Run this command from the /frontend subdirectory to test the frontend (you can terminate the process with ctrl + C once you verify it runs)
```sh
npm run dev
```
http://localhost:5173/app-analysis

## Run this command from the /backend subdirectory to test the backend (you can terminate the process with ctrl + C once you verify it runs)
```sh
uv run fastapi dev src/main.py
```

# Stored proc

```sh
git clone https://github.com/Modernization-Factory/storedproc2java.git && cd storedproc2java && git checkout demo-2025-07
```

1Password vault. Download the env file and copy it to the storedproc2java/docker and rename it to “.env”.

Export your username and PAT as environment variables as well. If you use zsh, you can use the following command:
```sh
echo 'export GH_USER=hbrulin-mdb' >> ~/.zshenv && echo 'export GH_PAT=<PAT>' >> ~/.zshenv
source ~/.zshenv
```

Log into GHCR with the following command: 
```sh
echo $GH_PAT | docker login ghcr.io -u $GH_USER --password-stdin
```
