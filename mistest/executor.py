#
# Copyright 2014 Nils Carlson
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import threading
import queue
from test import Test
import tap


class ExecutorMessage:
    """A communication message to or from the executor"""

    def __init__(self, executor=None):
        self.executor = executor

    def __str__(self):
        return "Executor Message: " + self.__class__.__name__


class TerminateExecutor(ExecutorMessage):
    """Executor should terminate"""
    pass


class UnknownExecutorMessage(Exception):
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
        self.completed_dependencies = []

    def queue(self, test_or_message):
        self.test_queue.put(test_or_message)

    def terminate(self):
        self.test_queue.put(TerminateExecutor())

    def __str__(self):
        return self.resource

    def queue_result(self, result):
        result.resource = self.resource
        result.executor = self
        self.result_queue.put(result)

    def run(self):
        while True:
            message = self.test_queue.get()

            # Early exit of the loop on a terminate message
            if isinstance(message, TerminateExecutor):
                break

            if not isinstance(message, Test):
                raise UnknownExecutorMessage("Unknown message of type " +
                                             str(type(message)))
            else:
                test = message

            # Execute dependencies and then the actual test
            for dep in test.dependencies:

                # Only run dependencies if they have not already been run.
                if dep in self.completed_dependencies:
                    continue
                else:
                    self.completed_dependencies.append(dep)

                for result in dep(self.parser, self.resource):
                    self.queue_result(result)

            for result in test(self.parser, self.resource):
                self.queue_result(result)
