# Install and start in vscode

Create an .env file with the following : 
```sh
MDB_MCP_API_CLIENT_ID = "YOUR_ATLAS_SERVICE_ACCOUNT_CLIENT_ID"
MDB_MCP_API_CLIENT_SECRET = "YOUR_ATLAS_SERVICE_ACCOUNT_SECRET"
```

```sh
npm install mongodb-mcp-server
```

In mcp.json : click start

(remove read-only option if needed)

# What to ask 

- list collections in my cluster0
- Describe the aircraft database

- find all air france aircrafts which have a fleetStatus of retired
- which index should I create to cover the last query?
- what indexes do I have for the data collection?
- can you show me the explain? 

- build an aggregation pipeline that counts faults per aircraft? 
- count OPEN resolutionStatus faults by severity 
- on the timeseries collection : calculate the average speed per aircraft per day  

- insert one sample record in the data collection
- how can i push a new activity into an aircraft document?
- how can I make a fault resolved? 

- ask about metrics, current load... 