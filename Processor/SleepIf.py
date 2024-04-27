#!/usr/local/autopkg/python
#
# Shamelessly stolen from https://github.com/autopkg/autopkg/blob/master/Code/autopkglib/StopProcessingIf.py
# Copyright 2013 Greg Neagle
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""See docstring for SleepIf class"""

from time import sleep
from autopkglib import Processor, ProcessorError, log

try:
    from Foundation import NSPredicate
except ImportError:
    log("WARNING: Failed 'from Foundation import NSPredicate' in " + __name__)

__all__ = ["SleepIf"]


class SleepIf(Processor):
    """Sets a variable to tell AutoPackager to stop processing a recipe if a
    predicate comparison evaluates to true."""

    description = __doc__
    input_variables = {
        "predicate": {
            "required": True,
            "description": (
                "NSPredicate-style comparison against an environment key. See "
                "http://developer.apple.com/library/mac/#documentation/"
                "Cocoa/Conceptual/Predicates/Articles/pSyntax.html"
            ),
        },
        "sleep_time": {
            "required": False,
            "description": "The number of seconds to sleep.",
            "default": "5",
        },
    }
    output_variables = {
        "sleep_recipe": {
            "description": "Boolean. Should we sleep the recipe?"
        }
    }

    def predicate_evaluates_as_true(self, predicate_string):
        """Evaluates predicate against our environment dictionary"""
        try:
            predicate = NSPredicate.predicateWithFormat_(predicate_string)
        except Exception as err:
            raise ProcessorError(f"Predicate error for '{predicate_string}': {err}")

        result = predicate.evaluateWithObject_(self.env)
        self.output(f"({predicate_string}) is {result}")
        return result

    def main(self):
        self.env["sleep_recipe"] = self.predicate_evaluates_as_true(
            self.env["predicate"]
        )
        if self.env["sleep_recipe"]:
            sleep_time = int(self.env.get("sleep_time"))
            sleep(sleep_time)


if __name__ == "__main__":
    PROCESSOR = SleepIf()
    PROCESSOR.execute_shell()
