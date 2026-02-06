# helene_demos


# Content

| Name | Demoed features | Notes |
|----------|----------|----------|
| 01-amadeus-pitr    | EA PITR     |     |
| 02-amadeus-streams    | Change Streams PNR events to Kafka topic  |     |
| 03-thalesradar-introMDB    | Simple queries & geo queries, indexing, aggregations & views, timeseries |      |
| 04-thales-k8s+upgrade-RBAC-QE   | Installation instruction, K8s deployment overview, Upgrades, RBAC, QE oss vs EA | Source K8s cluster is deployed [Thomas' repo](https://github.com/scott-thomas/Azure-AKS-MongoDB-EA-OPS-Manager). Changes to version and tenant names. There is no demo per say for QE, it's just two java files showing the differences between EA and community. [These are the slides that go with it](https://docs.google.com/presentation/d/1tyyB9HzyiFby4aSb7pviat-P0LPsgEDc6RZ9g_lUTmA/edit?slide=id.g3bc8e0d115f_0_2464#slide=id.g3bc8e0d115f_0_2464) |
| 05-ec2-om-deployment+overview    | EC2 Deployment based on [Sylvain Chambon's ](https://github.com/schambon/ec2-om), with an updated AMI, different machine types. Overview of OM, replicaset creation via UI and API.  | I tried to change the scripts so the nodes use private dns for internal communication, so that if I pause the VMs, the setup is not broken by change of public IP and public DNS. I've had issues with restarts though - to be worked on, files are in folder privdns|
| 06-AMP Walkthrough   | AMP Walkthrough  | This walkthrough was done prior to the release of this : https://amp-docs.prod.corp.mongodb.com/demo. It is likely to be outdated.     |
| 07-railwayassistantragapp    | This demos a RAG assistant for railway operators    | Uses mistral embeddings, langchain, and atlas.  Mistral AI API key required.   |
| 08-artium-modelindex-ts-search-voyageai | Indexing & geo, Aggregations, basic Search, basic Vector Search using VoyageAI API     | Voyage AI API key required    |
| 09-agentdemo-skillbadge    | Skill badge agent demo     | Requires openai key   |
| 10-zone-sharding   | Simple geosharding dispatch    |      |
| 11-flightid-movecollection   | Demo of the moveCollection() operation to rebalance a cluster  |   |
| 12-iceberg  | This is Bruno's iceberg demo, with my notes, and my example files.  |     |
| 13-hybridsearch   | Walkthrough of talking points for showing the [hybrid search demo from John Underwood](https://github.com/JohnGUnderwood/atlas-hybrid-search)   |     |
| 14-atlas Failover  |Failover demo, based on [proof point rep](https://github.com/10gen/pov-proof-exercises/tree/master/proofs/17) | Even without retryable writes, it happens that no error is shown.    |
| 15-mcp-atlas-api   | This shows how to use the mcp server by using Atlas Service Accounts and not a cluster connection string, allowing project-wide (or org-wide, if the service account is at the org level), actions.   |   |
| 16-baseetat-model,ts,geo   | Unorganized repo of multiple demos for SNCF base Etat, including a train position detector with timeseries, both in real time and over history (in batches).    |  The notes have not been reviewed yet  |
