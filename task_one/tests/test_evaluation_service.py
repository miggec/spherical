import pytest
import requests
import decimal
import typing

import hypothesis

import task_one.evaluation_service


@pytest.fixture()
def default_test_size():
    return 10


@pytest.fixture()
def get_requests(default_test_size: int):
    return [requests.Request('GET', f'https://test-get-request/{i}') for i in range(default_test_size)]


@pytest.mark.parametrize(
    'expected_result', ["Typical", "Anomalous"]
)
def test_homogeneous_requests(
        monkeypatch: typing.Any,
        expected_result: str,
        get_requests: typing.List[requests.Request],
        default_test_size: int,
):
    """
    Test a simple happy path to make sure the list of requests are correctly classified by
    EvaluationService.evaluate()
    """
    service = task_one.evaluation_service.EvaluationService()

    homogeneous_outputs = {"Typical": decimal.Decimal(1), "Anomalous": decimal.Decimal(0)}
    monkeypatch.setattr(service.scorer, 'evaluate', (lambda *x, **y: homogeneous_outputs[expected_result]))

    evaluation = service.evaluate(get_requests)

    if expected_result == 'Typical':
        expect_populated = evaluation.typical_requests
        expect_empty = evaluation.anomalous_requests

    elif expected_result == 'Anomalous':
        expect_populated = evaluation.anomalous_requests
        expect_empty = evaluation.typical_requests

    else:
        raise ValueError(f"Expected result type {expected_result} not defined")

    assert len(expect_empty) == 0, \
        f"{len(expect_empty)} {expected_result} requests incorrectly evaluated"

    assert len(expect_populated) == default_test_size, \
        f"Some {expected_result} requests are missing from the {expected_result} requests evaluation list: " \
        f"expected {default_test_size}, got {len(expect_populated)}: \n{expect_populated}"


@pytest.mark.parametrize('verb', ['GET', 'PUT', 'POST', 'DELETE', 'PATCH'])
@hypothesis.given(score=hypothesis.strategies.decimals(min_value=6.62e-34, max_value=100))
def test_positive_scores(verb: str, score: float, monkeypatch: typing.Any):  # how to type hint these pytest fixtures?
    """
    Test a substantial range of positive decimals to ensure there are no edge cases
    e.g. requests evaluating to anomalous due to precision errors

    See:
        https://hypothesis.readthedocs.io/en/latest/index.html
    """
    service = task_one.evaluation_service.EvaluationService()
    score = decimal.Decimal(score)
    monkeypatch.setattr(service.scorer, 'evaluate', (lambda *x, **y: score))
    evaluation = service.evaluate([requests.Request(verb, 'https://test-get-request/0')])

    assert len(evaluation.anomalous_requests) == 0, f"Score of {score} incorrectly evaluated as anomalous"


@pytest.mark.parametrize('verb', ['GET', 'PUT', 'POST', 'DELETE', 'PATCH'])
@hypothesis.given(score=hypothesis.strategies.decimals(min_value=-100, max_value=0))
def test_negative_scores(verb: str, score: float, monkeypatch: typing.Any):
    """
    Test a substantial range of negative decimals to ensure there are no edge case failures
    """
    service = task_one.evaluation_service.EvaluationService()
    score = decimal.Decimal(score)
    monkeypatch.setattr(service.scorer, 'evaluate', (lambda *x, **y: score))
    evaluation = service.evaluate([requests.Request(verb, 'https://test-get-request/0')])

    assert len(evaluation.typical_requests) == 0, f"Score of {score} incorrectly evaluated as typical"


@pytest.mark.parametrize('verb', ['GET', 'PUT', 'POST', 'DELETE', 'PATCH'])
def test_alternating_categories(verb: str, monkeypatch: typing.Any):
    """
    Crudely patch the scorer to alternate between typical + anomalous to test for weird
    stateful bugs or broken if-branches etc.
    """
    n_requests = 10

    service = task_one.evaluation_service.EvaluationService()
    service.scorer.iteration = 0

    def alternate(*args, **kwargs):
        """Alternate between returning typical and anomalous scores"""
        ret = -1 if service.scorer.iteration % 2 == 0 else 1
        service.scorer.iteration += 1
        return decimal.Decimal(ret)

    monkeypatch.setattr(service.scorer, 'evaluate', alternate)

    reqs = [requests.Request(verb, f'https://test-get-request/{i}') for i in range(n_requests)]
    evaluation = service.evaluate(reqs)

    assert len(evaluation.anomalous_requests) == n_requests // 2
    assert len(evaluation.typical_requests) == n_requests // 2


def test_empty_list():
    """Passing an empty list shouldn't cause any breaks"""
    service = task_one.evaluation_service.EvaluationService()
    evaluation = service.evaluate([])  # object on its own
    assert evaluation.anomalous_requests == []
    assert evaluation.typical_requests == []


@pytest.mark.parametrize('obj', ['abc', {}, decimal.Decimal])
def test_unrecognized_objects_raises_type_error(obj: typing.Any, get_requests: typing.List[requests.Request]):
    """Expect to throw ValueError if a non-request object is passed to evaluate()"""
    service = task_one.evaluation_service.EvaluationService()
    with pytest.raises(TypeError):
        service.evaluate([obj])  # object on its own
        service.evaluate(get_requests + [obj] + get_requests)  # object amongst genuine requests objects


@pytest.mark.parametrize('score', [None, 'foo'])
def test_unrecognized_scores_raises_type_error(monkeypatch: typing.Any, score: typing.Any):
    service = task_one.evaluation_service.EvaluationService()
    monkeypatch.setattr(service.scorer, 'evaluate', (lambda *x, **y: score))
    with pytest.raises(TypeError):
        service.evaluate([requests.Request('GET', 'https://test-get-request/0')])
