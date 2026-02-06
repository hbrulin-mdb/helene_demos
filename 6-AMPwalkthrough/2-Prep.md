# JSCA ANalysis
In app-analysis/backend :
```sh
uv run -m src.cli_main app-analysis source-code analyze --parse-code ../../legacy-demo-app --java-parser
```

Path for openjdk if installed with home brew : 
```sh
echo 'export JAVA_HOME="/opt/homebrew/opt/openjdk@21"' >> ~/.zshrc
echo 'export PATH="$JAVA_HOME/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
echo $JAVA_HOME
```

Next, run this command to detect the invocation point of the “processOrder” stored procedure:
```sh
uv run -m src.cli_main app-analysis source-code analyze --stored-procedures processOrder ../../legacy-demo-app
```

In neo4J, run : MATCH path=(n:StoredProcedure)-[]-() return path

## SPDA UI
Run app analyis (already running if haven't stopped before). 
```sh
# frontend
npm run dev
# backend
uv run fastapi dev src/main.py
```

## Press Connect DDL file and provide the absolute path to the “spda” subdirectory inside the demo app (.../legacy-demo-app/database/spda). For this demo, select Oracle as the dialect.
Example : /Users/helene.brulin/Desktop/AMP/legacy-demo-app/database/spda

You should now see a bunch of items populated on the left sidebar. Click “processOrder” (which is the stored procedure we will be showing).

Next, click the down arrow on the box next to “Visualize” and select “Tables” as an option

You should now see the main “processOrder” and the other stored procedures, functions, and tables involved in its invocation.

# Spin up storedproc2java

From the root directory of the storedproc2java repository, run the following command:
```sh
cd docker && docker-compose --env-file .env up --force-recreate
```                     

If GHCR issue : double check the SSO auth : https://mongodb.slack.com/archives/C09G1LYA9J9/p1765279221035749 

Visit http://localhost:7860/ to verify storedproc2java is running successfully. 

