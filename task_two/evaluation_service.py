import typing
import requests as requests_lib  # template code already defines a variable named "requests"
import decimal
import statistics

import task_one.evaluation_service
import task_one.scorer_http_client

import task_two.evaluation  # the new object

# using absolute imports for better immediate readability


class EvaluationService(task_one.evaluation_service.EvaluationServiceInterface):

    def __init__(self):
        super().__init__()
        self.scores: typing.List[decimal.Decimal] = []

    def evaluate(self, requests: typing.List[requests_lib.Request]) -> task_one.evaluation.Evaluation:
        # rather than building up two potentially long lists of objects, and then instantiating a
        # new object with copies of those lists, create a stateful instance here and append to it
        # while processing requests
        evaluation = task_two.evaluation.Evaluation([], [], decimal.Decimal('NaN'))
        for request in requests:

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
        # But given that the method takes complete lists rather than lazy iterators there's no real need for that level
        # of complexity.
        #
        # For higher performance could use numpy arrays, though floating point stuff would negate the use of the decimal
        # library. Since the decimal library was part of the original skeleton code/interface I've gone for the less
        # performant option which preserves the decimal precision.
        if len(self.scores) >= 2:
            evaluation.standard_deviation = statistics.stdev(self.scores)

        elif len(self.scores) == 1:
            evaluation.standard_deviation = 0
        # else: default remains as NaN

        return evaluation
