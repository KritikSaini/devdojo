from elasticsearch import AsyncElasticsearch, NotFoundError

es = AsyncElasticsearch("http://localhost:9200")
TESTCASE_INDEX = "testcases"

async def get_testcases_by_challenge(challenge_id: str) -> str | None:
    """
    Fetches the test cases document for a specific challenge from Elasticsearch.
    
    Returns the 'testcases' field as a string, or None if not found.
    """
    try:
        # The document ID for test cases is the challenge_id
        res = await es.get(index=TESTCASE_INDEX, id=challenge_id)
        return res["_source"]["testcases"]
    except NotFoundError:
        print(f"No test cases found for challenge_id: {challenge_id}")
        return None
    except Exception as e:
        print(f"An error occurred while fetching test cases: {e}")
        return None
