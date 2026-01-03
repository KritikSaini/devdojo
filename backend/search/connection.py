from elasticsearch import AsyncElasticsearch
from elasticsearch_dsl import connections


es = AsyncElasticsearch("http://localhost:9200")
connections.create_connection(hosts=["http://localhost:9200"])