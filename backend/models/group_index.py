
from elasticsearch_dsl import Document, Text, Date, Keyword

class Group(Document):
    name = Text()
    description = Text()
    created_by = Keyword()
    created_at = Date()  

    class Index:
        name = "groups"
