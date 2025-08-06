## Responses
```bash
curl --location 'http://127.0.0.1:8007/query' \
--header 'Content-Type: application/json' \
--data '{"query":"Show me a bar chart of the total sales amount per product category for the last 6 months.","variables":{}}'
```
```json
{
    "response": "Here is a bar chart showing the total sales amount per product category for the last 6 months. You can view the chart [here](sandbox:/charts/chart_20250806_233904.png).",
    "tools_used": "execute_sql_query, generate_chart"
}
```
![alt text](./charts/charts/chart_20250806_233904.png)


```bash
curl --location 'http://127.0.0.1:8007/query' \
--header 'Content-Type: application/json' \
--data '{"query":"What are the total sales for each product category","variables":{}}'
```
```json

    {
    "response": "The total sales for each product category are as follows:\n- Groceries: $345,579.95\n- Electronics: $411,921.45\n- Sports: $142,165.60\n- Apparel: $271,252.55\n- Books: $241,754.06\n- Home Goods: $113,250.71",
    "tools_used": "execute_sql_query"
    }

```

```bash
curl --location 'http://127.0.0.1:8007/query' \
--header 'Content-Type: application/json' \
--data '{"query":"Find products named iphon","variables":{}}'
```
```json
{
    "response": "I found a product named \"iPhone 14\" by Apple in the Electronics category with a price of $599.02.",
    "tools_used": "meilisearch_query"
}
```

```bash
curl --location 'http://127.0.0.1:8007/query' \
--header 'Content-Type: application/json' \
--data '{"query":"How many times has the user User1 made a purchase?","variables":{}}'
```
```json
{
    "response": "User1 has made a total of 4 purchases.",
    "tools_used": "execute_sql_query, meilisearch_query"
}
```