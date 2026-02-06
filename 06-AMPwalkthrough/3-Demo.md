# Demo

Show the demo workflow [here](https://www.figma.com/proto/fM9rULTPS9sIqPmbSTcjKe/App-Mod-Demo-Journey?page-id=0%3A1&node-id=238-585&viewport=-436%2C-480%2C0.4&t=VvHgAhIwMfwvlHmS-1&scaling=min-zoom&content-scaling=fixed).

Give an intro on what the app is : ecommerce app with users, prcudts and orders. Java Beans + Stored Procedures. 
"On a perdu la connaissance de ce site ecommerce.
Oracle source db.
La première chose c'est l'analyse de l'application : .... "

# App Analysis - Java Source Code Analyzer
"On a développé des outils, qui va nous sortir une macro cartographie, qui va découper l'appli en blocks. pour organiser le travail des équipes AMP." 

Show the Macro cartographie (output of app analysis) and show we will focus on processOrder procédure stocké. 
La macrocartographie, qui analyse code, classes, dépendances entre les classes. 

"aujourd'hui on va s'intéresser au block processOrder. "

## Process order

Show create_stored_procedure.sql (docker/init)

"Série de méthodes : logger une activité suspicieuse, faire de la fraude détection, check les credits du client, regarder si le client existe. 
Puis après on a notre methode processOrder, qui exécute ces checks, update l'inventaire pour la totalité de la commande, conditionne la transaction à un nb de crédits suffisant, et puis enfin on insère la data dans la base. 
On va maintenant pouvoir faire une microcartophie pour décomposer notre procédure : "

# Stored procedure Analysis

- "Avec SPDA : on génère un fichier DDL après l'analyse du stored proc, et on récupère un fichier de procédures pour processOrder -> on une analyse de la procédure, et si on ajoute un filtre sur Tables dans Vizualize, on voit les tables -> ça va être utilisé pour splitter le travail pour des outisl d'IA qui vont convertir la procédure. 
-> on explique les étapes de la stored procedure. "
-> Show it in localhost:5173/app-analysis

"On retrouve toutes les méthodes de notre procédure."

- Add the filter tables to the processOrder procedure : on peut mettre en évidence les appels vers tables. 
- "Pourquoi? pour donner de l'intelligence à nos outils d'IA gen pour moderniser notre code applicatif. "
- "une fois qu'on a fait cette analyse, on va mapper notre schema de données source, vers Mdb."

# Relational Migrator - define the mappings for code conversion and data migration, denormalized mdb model

- localhost:8278 : Show the mapping

- "Pour ça on va utiliser le relational migrator, qui va se connecter au système soruce et permettre de mapper le schema côté mdb. on va avoir des transfo qui vont pouvoir être faite. On voit la collection order, avec des orderItems à l'intérieur -> on a dénormalisé la data. "

"-Et puis avec l'onglet Migration, le relational migrator va nous permettre d'ingérer de la données dans ce nouveau format : pourquoi? pour qu'on puiosse exécuter derrière, avec nos autres outils, des tests unitaires : afin de valider que les tests de la source, et les tests de la cible sur mdb, retournent bien le même résultat."

- "Maintenant il faut générer l'app cible, modernisée."

# AMP Workflow Engine - langflow

- localhost =7860 : PLSQL_to_Java_All_Routineswith_unit_tests

"La modernisation en elle-même se fait au niveau du workflow engine. Dedans on a une liste de tools que nos équipes vont construire pour vous, votre environnement. chaque contexte client a ses contraintes, ses particularités -> donc on crée ou on adapate des tools ad hoc." 

- "On construit ensuite un workflow de tâche qui va décomposer cette modernisation. "-> exécuter le flow et parler des différentes étapes : 

- - Générer un projet spring (framework de notre app cible) -> Dans Docker, on voit qu'on a un demo project qui vient d'apparaître -> on retrouve une structure de projet spring avec des controllers, des entity, des services. AMP est en train de générer des fichiers, de moderniser l'app. 
- - splitter : split procedure stockées : on a remarqué que si on 500 lignes de code, qu'on l'envoie dans un LLM, et qu'on lui fait générr du code modernizer -> ça ne marche pas. En revanche si on fait des bouts de code de 50 lignes, là on remarque que ça marche. c'est pour ça que la procédure stockée a été découpée en différents blocks, ou routines, , on l'a vu à l'étape précédente, et ce sont ces blocks qu'on va envoyer au LLM pour convertir le code. 
- - loop : c'est là que la modernization intervient. Le loop est en mouvement ici? il fauit quoi? il modernize (les convertit en java code wui interagit avec mdb) nos blocks de code, les builds, et les tests de manière séquentielle. processus itératif, parfois les buids ne fonctionne pas -> on renvoie au LLM, qui répare, et on réessaie et ainsi de suite... Ces tests ce sont ceux issus du travails de relational migrator, et sont générés par l'AMP workflow. 


# Aller dans les logs pour meubler les 13mn
- docker-compose : montrer Routine Names (peut nécessiter un screenshot d'un précédent run) : ce sont les blocks qu'on va moderniser un par en : checkuserExists, fraudDetection, checkCustomercredit etc... 
- montrer ce que fais le docker compose en cours
- docker folder : cat system.log : les étapes de conversion, on voit quand il échoue et recommence





# Stop and restart

## Stop
- neo4 stop :
docker exec -it neo4j-gds bash
neo4j stop
-> + stop container

- docker compose ctrlC
- stop frontend and backend
- delete demo_project

## Restart

- restart neo4J 
- restart backend
- restart frontend
- restart docker compose

## URIs
http://localhost:7474/
http://localhost:5173/app-analysis
http://localhost:7860/ 
localhost:8278