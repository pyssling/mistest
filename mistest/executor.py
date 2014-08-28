import threading
import queue
import suite
import case
import tap

class ExecutorMessage:
    """A communication message to or from the executor"""

    def __init__(self, executor=None):
        self.executor = executor

    def __str__(self):
        return "Executor Message: " + self.__class__.__name__

class ExecutionComplete(ExecutorMessage):
    """Executor ran to completion"""
    pass

class TerminateExecutor(ExecutorMessage):
    """Executor should terminate"""
    pass

class Executor(threading.Thread):
    """An executor of test cases and suites

    Runs the execution in a thread, receiving cases from a queue
    and placing the result in another queue."""

    def __init__(self, resource, result_queue):
        threading.Thread.__init__(self)
        self.daemon = True

        self.resource = resource
        self.test_queue = queue.Queue()
        self.result_queue = result_queue
        self.parser = tap.Parser()

    def queue(self, test_or_message):
        self.test_queue.put(test_or_message)

    def put(self, test_or_message):
        test_or_message.resource = self.resource
        self.result_queue.put(test_or_message)

    def terminate(self):
        self.test_queue.put(TerminateExecutor())

    def __str__(self):
        return str(self.resource)

    def run(self):
        while True:
            test_or_message = self.test_queue.get()

            if isinstance(test_or_message, suite.Suite):
                for test_case in test_or_message:
                    result = test_case(self.result_queue)

            elif isinstance(test_or_message, case.Case):
                test_or_message(self)

            elif isinstance(test_or_message, TerminateExecutor):
                break

            self.result_queue.put(ExecutionComplete(self))
