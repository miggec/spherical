import pytest
import requests
import decimal
import statistics
import typing
import string

import hypothesis
import hypothesis.strategies

import task_two.evaluation_service


DEFAULT_TEST_SIZE = 10  # max num. of request objects to throw into each test

# parametrize tests with REST verbs - maybe not necessary, but harmless
VERB_PARAM = pytest.mark.parametrize('verb', ['GET', 'PUT', 'POST', 'DELETE', 'PATCH'])

# use hypothesis to generate some valid random JSON
JSON_BODY_STRAT = hypothesis.strategies.recursive(
    hypothesis.strategies.none() | hypothesis.strategies.booleans() | hypothesis.strategies.floats(),
    lambda children:
        hypothesis.strategies.dictionaries(
            hypothesis.strategies.text(string.printable), children, min_size=1, max_size=DEFAULT_TEST_SIZE
        ),
    max_leaves=4,
)
VERB_STRAT = hypothesis.strategies.sampled_from(['GET', 'PUT', 'POST', 'DELETE', 'PATCH'])

# use the json body and REST verbs strategies to generate random requests objects
@hypothesis.strategies.composite
def _requests_strat(draw, body=JSON_BODY_STRAT, verb=VERB_STRAT):
    return requests.Request(draw(verb), 'http://test-url/', draw(body))


JSON_REQUEST_STRAT = hypothesis.strategies.lists(
    elements=_requests_strat(), min_size=DEFAULT_TEST_SIZE, max_size=DEFAULT_TEST_SIZE,
)


def get_service():
    """Logic for instantiating an EvaluationService for testing (might need mocking in future)"""
    return task_two.evaluation_service.EvaluationService()


def gen_requests(num: int = DEFAULT_TEST_SIZE, verb: str = 'GET', body_iter: typing.Iterable = None):
    """
    Utility function for generating request-type objects
    :param num: how many requests to generate
    :param verb: idempotent verb (GET, PUT, etc) TODO validate this input
    :param body_iter: iterable of JSON body data e.g. a hypothesis start to generate valid json
    :return: generator of requsts.Request objects
    """
    body_iter = None if body_iter is None else iter(body_iter)
    for i in range(num):
        if body_iter is not None:
            body = body_iter.__next__()
        else:
            body = None
        yield requests.Request(verb, f'https://test-request/{i}', data=body)


@pytest.fixture()
def get_requests():
    return [r for r in gen_requests()]


@pytest.mark.parametrize(
    'expected_result', ["Typical", "Anomalous"]
)
def test_homogeneous_requests(
        monkeypatch: typing.Any,
        expected_result: str,
        get_requests: typing.List[requests.Request],
):
    """
    Test a simple happy path to make sure the list of requests are correctly classified by
    EvaluationService.evaluate()
    """
    service = task_two.evaluation_service.EvaluationService()

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

    assert len(expect_populated) == DEFAULT_TEST_SIZE, \
        f"Some {expected_result} requests are missing from the {expected_result} requests evaluation list: " \
        f"expected {DEFAULT_TEST_SIZE}, got {len(expect_populated)}: \n{expect_populated}"


@hypothesis.given(reqs=JSON_REQUEST_STRAT)
def test_json_processing(
        monkeypatch: typing.Any,
        reqs: typing.List[requests.Request],
):
    """
    Test that valid JSON bodies are parsed without error - for speed most tests are
    written using empty Requests objects
    """
    service = task_two.evaluation_service.EvaluationService()
    monkeypatch.setattr(service.scorer, 'evaluate', (lambda *x, **y: decimal.Decimal(1)))
    service.evaluate(reqs)


@hypothesis.given(
    verb=VERB_STRAT,
    score=hypothesis.strategies.decimals(min_value=6.62e-34, allow_infinity=False, allow_nan=False),
)
def test_typical_scores(verb: str, score: decimal.Decimal, monkeypatch: typing.Any):  # how to type hint these pytest fixtures?
    """
    Test a substantial range of positive decimals to ensure there are no edge cases
    e.g. requests evaluating to anomalous due to precision errors

    See:
        https://hypothesis.readthedocs.io/en/latest/index.html
    """
    service = get_service()
    score = decimal.Decimal(score)
    monkeypatch.setattr(service.scorer, 'evaluate', (lambda *x, **y: score))
    evaluation = service.evaluate([requests.Request(verb, 'https://test-get-request/0')])

    assert len(evaluation.anomalous_requests) == 0, f"Score of {score} incorrectly evaluated as anomalous"


@VERB_PARAM
@hypothesis.given(score=hypothesis.strategies.decimals(max_value=0, allow_infinity=False, allow_nan=False))
def test_anomalous_scores(verb: str, score: decimal.Decimal, monkeypatch: typing.Any):
    """
    Test a substantial range of negative decimals to ensure there are no edge case failures
    """
    service = get_service()
    score = decimal.Decimal(score)
    monkeypatch.setattr(service.scorer, 'evaluate', (lambda *x, **y: score))
    evaluation = service.evaluate([requests.Request(verb, 'https://test-get-request/0')])

    assert len(evaluation.typical_requests) == 0, f"Score of {score} incorrectly evaluated as typical"


@VERB_PARAM
def test_alternating_categories(verb: str, monkeypatch: typing.Any):
    """
    Crudely patch the scorer to alternate between typical + anomalous to test for weird
    stateful bugs or broken if-branches etc.
    """
    n_requests = 10

    service = get_service()
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


def test_empty_requests_list():
    """Passing an empty list of requests shouldn't cause any breaks"""
    service = get_service()
    evaluation = service.evaluate([])  # object on its own
    assert evaluation.anomalous_requests == []
    assert evaluation.typical_requests == []


@pytest.mark.parametrize('obj', ['abc', {}, decimal.Decimal])
def test_unrecognized_objects_raises_type_error(obj: typing.Any, get_requests: typing.List[requests.Request]):
    """Expect to throw TypeError if a non-request object is passed to evaluate()"""
    service = get_service()
    with pytest.raises(TypeError):
        service.evaluate([obj])  # object on its own
        service.evaluate(get_requests + [obj] + get_requests)  # object amongst genuine requests objects


@pytest.mark.parametrize('score', [None, 'foo'])
def test_unrecognized_scores_raises_type_error(monkeypatch: typing.Any, score: typing.Any):
    """Expect downstream to break if scorer starts returning the wrong objects"""
    service = get_service()
    monkeypatch.setattr(service.scorer, 'evaluate', (lambda *x, **y: score))
    with pytest.raises(TypeError):
        service.evaluate([requests.Request('GET', 'https://test-get-request/0')])


@hypothesis.given(scores=hypothesis.strategies.lists(
    hypothesis.strategies.decimals(allow_infinity=False, allow_nan=False),
    min_size=2,
))
def test_std_dev_calculation(monkeypatch, scores: typing.Tuple[typing.List[decimal.Decimal]]):
    """
    Happy-path test that a range of different scores give the correct std dev result
    """
    service = get_service()
    scores_iter = iter(scores)

    def gen(*args, **kwargs):
        return scores_iter.__next__()

    monkeypatch.setattr(service.scorer, 'evaluate', gen)
    evaluation = service.evaluate([r for r in gen_requests(len(scores))])

    assert evaluation.standard_deviation == statistics.stdev(scores)


def test_std_dev_one_value(monkeypatch: typing.Any):  # TODO do type stubs exist for this?
    """Always expect a variance of 0 if N=1"""
    service = get_service()
    monkeypatch.setattr(service.scorer, 'evaluate', lambda *x, **y: decimal.Decimal(1))
    evaluation = service.evaluate([r for r in gen_requests(1)])

    assert evaluation.standard_deviation == 0


def test_std_dev_no_values():
    """No std dev == NaN"""
    service = get_service()
    evaluation = service.evaluate([])

    assert evaluation.standard_deviation.is_nan()
