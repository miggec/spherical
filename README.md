Spherical Defence Python Tasks:

Please complete the following tasks. You may use any libraries you think are
appropriate and you may Google as much as you like.

If you are unsure of any requirements then please do ask via email.
Also, please make sure to fully test your code and consider error scenarios.

Task 1:
  Implement the interface for task_one/evaluation_service.py. Its method 'evaluate'
  takes a list of requests, and returns an Evaluation, as defined in task_one/evaluation.py.

  A request, like an HTTP request, is formed of a method, a path, and a body.

  The evaluate method must take the requests and send their contents to the
  ScorerHttpClient, the interface for which can be found in
  task_one/http_client.py. It returns a score as a Decimal.

  If the score is positive then the request is typical, if it is 0 or negative then the
  request is anomalous.

  Your class must take each request it receives, get the score, and use it to
  partition the requests into two lists stored in the returned Evaluation.

  N.B. Do not implement ScorerHttpClient. This interface is provided for mocking
       purposes.

Task 2:
  In task_two/evaluation.py you'll find an extended Evaluation object. Now
  EvaluationService must add the standard deviation of the requests to the
  returned Evaluation.
