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
from executor import Executor
from test import TestExecutionResult
import logging

class Scheduler:

    def __init__(self, resources, suite, output):
        self.resources = resources
        self.suite = suite
        self.output = output

        self.result_queue = queue.Queue()

        self.executors = {}
        for resource in resources:
            self.executors[resource] = Executor(resource, self.result_queue)
            self.executors[resource].start()

        self.scheduled_tests = {}
        for resource in resources:
            self.scheduled_tests[resource] = None

    def wait_for_free_resource(self):
        while True:
            result = self.result_queue.get()
            self.output(result)

            if isinstance(result, TestExecutionResult):
                #result.collate()

                resource = str(result.executor)
                if result.test == self.scheduled_tests[resource]:
                    self.scheduled_tests[resource] = None
                    return resource


    def get_free_resources(self):
        """Get a list of free resources available to this scheduler"""

        # First see if there are any free resources without scheduled tests
        free_resources = []
        for resource in self.resources:
            if self.scheduled_tests[resource] == None:
                free_resources.append(resource)

        if len(free_resources) > 0:
            return free_resources

        # Otherwise wait for a resource to become free
        return [ self.wait_for_free_resource() ]

    def schedule_test(self, resource, test):
        """Schedule a test on a specific resource"""
        self.scheduled_tests[resource] = test
        self.executors[resource].queue(test)

    def __call__(self):
        """Start scheduling tests

        This is a simple scheduler method that other schedulers
        should overload to implement better scheduling algorithms."""

        # Run all the tests
        for test in self.suite:
            free_resources = self.get_free_resources()
            logging.debug("Scheduling %s on %s" % (str(test), str(free_resources[0])))
            self.schedule_test(free_resources[0], test)

        # Wait for all the resources to become free
        while set(self.resources) != set(self.get_free_resources()):
            self.wait_for_free_resource()
