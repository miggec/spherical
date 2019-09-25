import abc
import typing
import requests as requests_lib  # template code already defines a variable named "requests"
import decimal

import task_one.evaluation
import task_one.scorer_http_client

# using absolute imports for better immediate readability


class EvaluationServiceInterface(abc.ABC):
    """
    Task 1: Implement the interface for task_one/evaluation_service.py

    'evaluate' takes a list of requests, and returns an Evaluation, as defined in task_one/evaluation.py.
    A request, like an HTTP request, is formed of a method, a path, and a body.

    The evaluate method must take the requests and send their contents to the ScorerHttpClient,
    the interface for which can be found in task_one/http_client.py. It returns a score as a Decimal.
    If the score is positive then the request is typical, if it is 0 or negative then the request is anomalous.

    Your class must take each request it receives, get the score, and use it to partition the requests into two
    lists stored in the returned Evaluation.

    N.B. Do not implement ScorerHttpClient. This interface is provided for mocking purposes.
    """
    def __init__(self):
        self.scorer = task_one.scorer_http_client.ScorerHttpClient()

    @abc.abstractmethod
    def evaluate(self, requests: typing.List[requests_lib.Request]) -> task_one.evaluation.Evaluation:
        """
        The interface to the requests objects is not documented in the task, so I have assumed a list of
        requests.Request objects.

        These are easily + cheaply constructed if the request object arrives in raw JSON or some other form instead,
        and provide a dependable interface to allow replacing of the underlying implementation if necessary.
        """
        pass


class EvaluationService(EvaluationServiceInterface):

    def evaluate(self, requests: typing.List[requests_lib.Request]) -> task_one.evaluation.Evaluation:
        # rather than building up two potentially long lists of objects, and then instantiating a
        # new object with copies of those lists, create a stateful instance here and append to it
        # while processing requests
        evaluation = task_one.evaluation.Evaluation([], [])
        for request in requests:

            if not isinstance(request, requests_lib.Request):
                raise TypeError(f"Instance of type {type(request)} not recognised, expected requests.Request object")

            score = self.scorer.evaluate(request.url, request.method, request.json)

            if not isinstance(score, decimal.Decimal):
                raise TypeError(f"'{score}' not recognised: expected a decimal.Decimal object, got {type(score)}")

            if score <= 0:
                evaluation.anomalous_requests.append(request)
            else:
                evaluation.typical_requests.append(request)

        return evaluation
