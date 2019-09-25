import typing
import requests as requests_lib  # template code already defines a variable named "requests"
import decimal
import statistics
import numpy

import task_one.evaluation_service
import task_two.evaluation  # the new object
import task_one.scorer_http_client

# using absolute imports for better immediate readability


class EvaluationService(task_one.evaluation_service.EvaluationServiceInterface):

    def __init__(self):
        super().__init__()
        self.n_requests = 0
        self.scores = numpy.

    def evaluate(self, requests: typing.List[requests_lib.Request]) -> task_one.evaluation.Evaluation:
        # rather than building up two potentially long lists of objects, and then instantiating a
        # new object with copies of those lists, create a stateful instance here and append to it
        # while processing requests
        evaluation = task_two.evaluation.Evaluation([], [], decimal.Decimal(0))
        for request in requests:

            self.n_requests += 1

            if not isinstance(request, requests_lib.Request):
                raise TypeError(f"Instance of type {type(request)} not recognised, expected requests.Request object")

            score = self.scorer.evaluate(request.url, request.method, request.json)
            self.scores.append(score)

            if not isinstance(score, decimal.Decimal):
                raise TypeError(f"'{score}' not recognised: expected a decimal.Decimal object, got {type(score)}")

            if score <= 0:
                evaluation.anomalous_requests.append(request)
            else:
                evaluation.typical_requests.append(request)

        # Considered an "online" algorithm for updating the std dev on the fly, e.g.:
        #     https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance#Welford's_online_algorithm
        #
        # But given that the method takes complete lists rather than iterators there's no real need for that level
        # of complexity.
        #
        # For higher performance
        evaluation.standard_deviation = decimal.Decimal(statistics.stdev(self.scores))

        return evaluation
