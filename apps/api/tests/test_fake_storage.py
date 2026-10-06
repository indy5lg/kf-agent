from indy_kf_utils import get_seaweedfs_client


def test_put_stores_bytes_the_fake_client_can_fetch_back(client):
    response = client.put("/fake-storage/alice/proj-storage", content=b"print('hi')")

    assert response.status_code == 200
    assert get_seaweedfs_client().fetch_script("alice", "proj-storage") == b"print('hi')"
