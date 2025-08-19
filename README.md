steps to setup hybrid_analytics_agent into your pc:
1. Clone the repository:
```bash
git clone  or download the git file
cd to the cloned repository

uv init
uv venv
source venv/bin/activate
uv add -r requirements.txt (or uv pip install -r requirements.txt)
```
setup the .env with 
OPENAI_API_KEY=""
MEILI_HOST=""
MEILI_MASTER_KEY=""
DATABASE_URL="postgresql://user:password@localhost:5432/hybrid_analytics_db"

2. Docker setup for postgres - run the following command to start the postgres container
```bash
docker-compose up -d
```

3. Run the following commands
```bash
python db_setup.py -> to setup the postgres db

python populate_db.py -> to populate the db with sample data

python meilisearch_sync.py -> to sync the data from postgres to meilisearch

python meilisearch_tools.py -> to test the meilisearch tools

```

4. Run the following command to start the agent
```bash
python main.py 
or
uvicorn app:app --reload --port 8007
```

5. You can now query the agent using the following command:
```bash
curl -X POST "http://127.0.0.1:8007/query" \
     -H "Content-Type: application/json" \
     -d '{ "query": "What are the total sales for each product category?" }'

curl -X POST "http://127.0.0.1:8007/query" \
     -H "Content-Type: application/json" \
     -d '{ "query": "Show me a bar chart of the total sales amount per product category for the last 6 months." }'

curl --location 'http://127.0.0.1:8007/query' \
--header 'Content-Type: application/json' \
--data '{"query":"Show me users from Bengaluru","variables":{}}'
```
6. Response Strcture:
```json
{
    "response": "",
    "tools_used": "execute_sql_query, meilisearch_query or generate_chart",
}
```
sql_tools.py, meilisearch_tools.py, chart_tools.py -> are the tools


## Generate the meilisearch host and key (Not Needed for Now - We are using local setup to build)
1. goto -> https://cloud.meilisearch.com/ -> register (if no account exists) or login
2. Create a project
3. At the bottom of projects page, you will see a list of projects.
4. Click on the project you created -> 
5. Copy API_KEY and HOST and add the same into .env file.
![alt text](image.png)

## postgres db setup (local)
1. Run the Docker as given the Step-2 above
2. then run db setup and then populate db 
3. postgres db is ready to use with the sample data.
4. sync the data from postgres to meilisearch using python meilisearch_sync.py
5. In meilisearch Click on the project you created and click on search preview to see the synced data with users and products


## Generate Chart using matplotlib
![alt text](./charts/chart_20250805_232053.png)

# In partnership with [Superteams.ai](https://www.superteams.ai)