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

import queue
from case import *
from executor import *
from tap import *
from test import *

class Scheduler:

    def __init__(self):
        pass

def schedule_tests(resources, suite, output):

    # Create the executors
    result_queue = queue.Queue()
    test_iter = iter(suite)
    executor_list = []
    for resource in resources:
        test_executor = Executor(resource, result_queue)
        try:
            test_executor.queue(next(test_iter))
        except StopIteration:
            break
        test_executor.start()
        executor_list.append(test_executor)

    # Schedule tests until we run out
    while len(executor_list) > 0:

        result = result_queue.get()
        output(result)

        if isinstance(result, TestExecutionResult):
            try:
                result.executor.queue(next(test_iter))
            except StopIteration:
                result.executor.terminate()
                result.executor.join()
                executor_list.remove(result.executor)
