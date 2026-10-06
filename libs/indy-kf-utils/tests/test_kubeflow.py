from indy_kf_utils.kubeflow import FakeKubeflowClient, Stage


def test_reports_running_immediately_after_submit():
    client = FakeKubeflowClient()

    run_id = client.submit(pipeline_inputs={"name": "demo"})

    assert client.get_stage(run_id).name == Stage.RUNNING


def test_reports_terminal_succeeded_with_result_after_polling():
    client = FakeKubeflowClient(steps_to_terminal=2)
    run_id = client.submit(pipeline_inputs={"name": "demo"})

    client.get_stage(run_id)
    final = client.get_stage(run_id)

    assert final.name == Stage.SUCCEEDED
    assert final.result is not None


def test_reports_terminal_failed_with_error_when_simulating_failure():
    client = FakeKubeflowClient(steps_to_terminal=1, simulate_failure=True)
    run_id = client.submit(pipeline_inputs={"name": "demo"})

    final = client.get_stage(run_id)

    assert final.name == Stage.FAILED
    assert final.error is not None
