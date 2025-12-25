'''In this exercise you need to put all code together to make the robot be able to stand up by its own.

* Task:
    complete the `StandingUpAgent.standing_up` function, e.g. call keyframe motion corresponds to current posture

'''


from recognize_posture import PostureRecognitionAgent
from keyframes import *

class StandingUpAgent(PostureRecognitionAgent):

    def __init__(self, simspark_ip='localhost',
                simspark_port=3100,
                teamname='DAInamite',
                player_id=0,
                sync_mode=True):
        super(StandingUpAgent, self).__init__(simspark_ip, simspark_port, teamname, player_id, sync_mode)
        self.start_keyframe = False
        self.last_posture = None

    def think(self, perception):
        self.standing_up()
        return super(StandingUpAgent, self).think(perception)

    def standing_up(self):
        posture = self.posture

        if posture != self.last_posture:
            print(f"Pose changed!")
            self.start_keyframe = False
            self.last_posture = posture

        #already standing
        if posture in ("Stand", "StandInit"):
            self.start_keyframe = False
            return

        if not self.start_keyframe:
            self.start_keyframe = True
            current_time = self.perception.time

            if posture == "Back":
                print("Standing up from Back")
                names, times, keys = rightBackToStand()
            elif posture == "Belly":
                print("Standing up from Belly")
                names, times, keys = leftBellyToStand()
            else:
                print("Unknown posture:", posture)
                return

            
            adjusted_times = [[t + current_time for t in joint_times] for joint_times in times]
            self.keyframes = (names, adjusted_times, keys)
            self.start_keyframe = True

class TestStandingUpAgent(StandingUpAgent):
    '''this agent turns off all motor to falls down in fixed cycles
    '''
    def __init__(self, simspark_ip='localhost',
                 simspark_port=3100,
                 teamname='DAInamite',
                 player_id=0,
                 sync_mode=True):
        super(TestStandingUpAgent, self).__init__(simspark_ip, simspark_port, teamname, player_id, sync_mode)
        self.stiffness_on_off_time = 0
        self.stiffness_on_cycle = 10  # in seconds
        self.stiffness_off_cycle = 3  # in seconds

    def think(self, perception):
        action = super(TestStandingUpAgent, self).think(perception)
        time_now = perception.time
        if time_now - self.stiffness_on_off_time < self.stiffness_off_cycle:
            action.stiffness = {j: 0 for j in self.joint_names}  # turn off joints
        else:
            action.stiffness = {j: 1 for j in self.joint_names}  # turn on joints
        if time_now - self.stiffness_on_off_time > self.stiffness_on_cycle + self.stiffness_off_cycle:
            self.stiffness_on_off_time = time_now

        return action


if __name__ == '__main__':
    agent = TestStandingUpAgent()
    agent.run()
