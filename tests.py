import requests

def test_static_to_que():
    "Test calling que"
    response =requests.get("http://localhost:5000/").text
    assert("Silly Rabit" in response)
