'''In this exercise you need to implement an angle interploation function which makes NAO executes keyframe motion

* Tasks:
    1. complete the code in `AngleInterpolationAgent.angle_interpolation`,
       you are free to use splines interploation or Bezier interploation,
       but the keyframes provided are for Bezier curves, you can simply ignore some data for splines interploation,
       please refer data format below for details.
    2. try different keyframes from `keyframes` folder

* Keyframe data format:
    keyframe := (names, times, keys)
    names := [str, ...]  # list of joint names
    times := [[float, float, ...], [float, float, ...], ...]
    # times is a matrix of floats: Each line corresponding to a joint, and column element to a key.
    keys := [[float, [int, float, float], [int, float, float]], ...]
    # keys is a list of angles in radians or an array of arrays each containing [float angle, Handle1, Handle2],
    # where Handle is [int InterpolationType, float dTime, float dAngle] describing the handle offsets relative
    # to the angle and time of the point. The first Bezier param describes the handle that controls the curve
    # preceding the point, the second describes the curve following the point.
'''


from pid import PIDAgent
from keyframes import *
from scipy.interpolate import CubicSpline
import numpy as np
import matplotlib.pyplot as plt

class AngleInterpolationAgent(PIDAgent):
    def __init__(self, simspark_ip='localhost',
                 simspark_port=3100,
                 teamname='DAInamite',
                 player_id=0,
                 sync_mode=True):
        super(AngleInterpolationAgent, self).__init__(simspark_ip, simspark_port, teamname, player_id, sync_mode)
        self.keyframes = ([], [], [])

    def think(self, perception):
        target_joints = self.angle_interpolation(self.keyframes, perception)
        #target_joints['RHipYawPitch'] = target_joints['LHipYawPitch'] # copy missing joint in keyframes
        self.target_joints.update(target_joints)
        return super(AngleInterpolationAgent, self).think(perception)

    def angle_interpolation(self, keyframes, perception):
        target_joints = {}
        
        current_time = perception.time
        

        for index, name in enumerate(keyframes[0]):
            times = keyframes[1][index]
            angles = []

            for key in keyframes[2][index]:
                angle = key[0]
                
                angles.append(angle)

            cs = CubicSpline(times,angles, bc_type='natural')

            if current_time <= times[0]:
                target_joints[name] = angles[0]
            elif current_time >= times[-1]:
                target_joints[name] = angles[-1]
            else:
                target_joints[name] = float(cs(current_time))

        return target_joints

'''
def plot_keyframe(joint_name,keyframes):
    names, times_list, keys_list = keyframes

    if joint_name not in names:
        raise ValueError(f"Gelenk '{joint_name}' nicht in {names}")

    idx = names.index(joint_name)
    t = np.array(times_list[idx])
    angles = np.array([k[0] for k in keys_list[idx]])

    plt.figure(figsize=(7, 4))
    plt.plot(t, angles, 'o-', label='Linear Interpolation (Keyframes)', markersize=8)
    plt.title(f"Raw Data – {joint_name}")
    plt.xlabel("Time [t]")
    plt.ylabel("Angle [rad]")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()
'''



if __name__ == '__main__':
    agent = AngleInterpolationAgent()
    agent.keyframes = hello()  # CHANGE DIFFERENT KEYFRAMES
    agent.run()