from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9200")


def create_index(index_name: str, mapping: dict):
    if not es.indices.exists(index=index_name):
        es.indices.create(index=index_name, body={"mappings": {"properties": mapping}})
        print(f"[OK] Created index: {index_name}")
    else:
        print(f"[SKIP] Index already exists: {index_name}")

def initialize_all_indexes():
    create_index("users", {
        "username": {"type": "keyword"},
        "email": {"type": "keyword"},
        "hashed_password": {"type": "keyword"},
        "created_at": {"type": "date"}
    })

    create_index("groups", {
        "name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
        "description": {"type": "text"},
        "created_by": {"type": "keyword"},
        "created_at": {"type": "date"},
        "members": {"type": "keyword"} # To store a list of user_ids
    })

    create_index("challenges", {
        "topic": {"type": "text"},
        "difficulty": {"type": "keyword"},
        "group_id": {"type": "keyword"},
        "created_by": {"type": "keyword"},
        "created_at": {"type": "date"},
        "problem_statement": {"type": "text"}
    })

    # This index is for the Agent 2 breakdown output
    create_index("breakdowns", {
        "challenge_id": {"type": "keyword"},
        "breakdown": {"type": "text"}
    })

    # --- UPDATED MAPPING ---
    create_index("testcases", {
        "challenge_id": {"type": "keyword"},
        # Storing the (potentially large) string of test cases from Agent 3
        "testcases": {"type": "text", "index": False} # 'index: False' saves space if you don't need to search this text
    })

    create_index("submissions", {
        "challenge_id": {"type": "keyword"},
        "user_id": {"type": "keyword"},
        "username": {"type": "keyword"},
        "status": {"type": "keyword"},
        "score": {"type": "float"},
        "feedback": {"type": "text", "index": False},
        "submitted_at": {"type": "date"}
    })

    create_index("leaderboard", {
        "user_id": {"type": "keyword"},
        "username": {"type": "keyword"},
        "group_id": {"type": "keyword"},
        "xp": {"type": "float"}
    })

if __name__ == "__main__":
    initialize_all_indexes()



def create_password_reset_index(es):
    if es.indices.exists(index="password_resets"):
        return

    es.indices.create(
        index="password_resets",
        body={
            "mappings": {
                "properties": {
                    "email": {"type": "keyword"},
                    "token_hash": {"type": "keyword"},
                    "expires_at": {"type": "date"},
                    "used": {"type": "boolean"}
                }
            }
        }
    )
