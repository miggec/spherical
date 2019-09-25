from decimal import Decimal


class Evaluation:

    def __init__(self, typical_requests: list, anomalous_requests: list, standard_deviation: Decimal):
        self.typical_requests = typical_requests
        self.anomalous_requests = anomalous_requests
        self.standard_deviation = standard_deviation
