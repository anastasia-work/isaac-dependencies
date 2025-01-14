# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

from .base_command import Command
from ..utils import Utils

class InspectWaistHeight(Command):
    def __init__(self, character, command, navigation_manager = None):
        super().__init__(character, command, navigation_manager)
        if len(command)>1:
            self.duration = float(command[1])
        self._exit_time = 1.0
        self._is_exiting = False

    def setup(self):
        super().setup()
        self.character.set_variable("Action", "inspectWaistHeight")

    def exit_command(self):
        return super().exit_command()

    def update(self, dt):
        self.time_elapsed += dt
        if not self._is_exiting and self.time_elapsed > self.duration:
            self._is_exiting = True
            self.character.set_variable("Action", "None") # Allow state machine to return to Idle for a while before switching to the next action
        elif self._is_exiting and self.time_elapsed > self.duration + self._exit_time:
            return self.exit_command()
