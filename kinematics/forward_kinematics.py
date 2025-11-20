'''In this exercise you need to implement forward kinematics for NAO robot

* Tasks:
    1. complete the kinematics chain definition (self.chains in class ForwardKinematicsAgent)
       The documentation from Aldebaran is here:
       http://doc.aldebaran.com/2-1/family/robots/bodyparts.html#effector-chain
    2. implement the calculation of local transformation for one joint in function
       ForwardKinematicsAgent.local_translation. The necessary documentation are:
       http://doc.aldebaran.com/2-1/family/nao_h21/joints_h21.html
       http://doc.aldebaran.com/2-1/family/nao_h21/links_h21.html
    3. complete function ForwardKinematicsAgent.forward_kinematics, save the transforms of all body parts in torso
       coordinate into self.transforms of class ForwardKinematicsAgent

* Hints:
    1. the local_translation has to consider different joint axes and link parameters for different joints
    2. Please use radians and meters as unit.
'''

# add PYTHONPATH
import os
import sys
import json
from numpy.matlib import *

sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'joint_control'))
from recognize_posture import PostureRecognitionAgent

class ForwardKinematicsAgent(PostureRecognitionAgent):
    def __init__(self, simspark_ip='localhost',
                 simspark_port=3100,
                 teamname='DAInamite',
                 player_id=0,
                 sync_mode=True):
        super(ForwardKinematicsAgent, self).__init__(simspark_ip, simspark_port, teamname, player_id, sync_mode)
        self.transforms = {n: identity(4) for n in self.joint_names}

        # chains defines the name of chain and joints of the chain / topologie
        self.chains = { "Head": ["HeadYaw", "HeadPitch"],
                        "LArm": ["LShoulderPitch", "LShoulderRoll", "LElbowYaw", "LElbowRoll", "LWristYaw"],
                        "RArm": ["RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll", "RWristYaw"],
                        "LLeg": ["LHipYawPitch", "LHipRoll", "LHipPitch", "LKneePitch", "LAnklePitch", "LAnkleRoll"],
                        "RLeg": ["RHipYawPitch", "RHipRoll", "RHipPitch", "RKneePitch", "RAnklePitch", "RAnkleRoll"]
                       }
        # geometrie in meters
        self.translation = {
            #head
            "HeadYaw": [0, 0, 0.1265],
            "HeadPitch": [0, 0, 0],
            #left arm
            "LShoulderPitch": [0, 0.098, 0.100],
            "LShoulderRoll": [0, 0, 0],
            "LElbowYaw": [0.105, 0.015,0],
            "LElbowRoll": [0,0,0],
            "LWristYaw": [0.05595,0,0],
            #right arm
            "RShoulderPitch": [0.0, -0.098, 0.100],
            "RShoulderRoll": [0.0, 0.0, 0.0],
            "RElbowYaw": [0.105, -0.015, 0.0], 
            "RElbowRoll": [0.0, 0.0, 0.0],
            "RWristYaw": [0.05595, 0.0, 0.0],
            #left leg
            "LHipYawPitch": [0,0.05,-0.085],
            "LHipRoll":[0,0,0],
            "LHipPitch":[0,0,0],
            "LKneePitch":[0,0,-0.1],
            "LAnklePitch":[0,0,-0.1029],
            "LAnkleRoll":[0,0,0],
            #right leg
            "RHipYawPitch": [0,-0.05,-0.085],
            "RHipRoll":[0,0,0],
            "RHipPitch":[0,0,0],
            "RKneePitch":[0,0,-0.1],
            "RAnklePitch":[0,0,-0.1029],
            "RAnkleRoll":[0,0,0]
             }

    def think(self, perception):
        self.forward_kinematics(perception.joint)
        return super(ForwardKinematicsAgent, self).think(perception)

    def local_translation(self, joint_name, joint_angle):
        '''calculate local transformation of one joint

        :param str joint_name: the name of joint
        :param float joint_angle: the angle of joint in radians
        :return: transformation
        :rtype: 4x4 matrix
        '''


        # identity matrix 
        T = identity(4)

        joint_cos = cos(joint_angle)
        joint_sin = sin(joint_angle)

        rotations = [
            # x axis
            array([[1, 0, 0, 0],
                    [0, joint_cos, -joint_sin, 0],
                    [0, joint_sin,  joint_cos, 0],
                    [0, 0, 0, 1]]),
            # y axis
            array([[joint_cos, 0, joint_sin, 0],
                    [0, 1, 0, 0],
                    [-joint_sin, 0, joint_cos, 0],
                    [0, 0, 0, 1]]),  
            # z axis
            array([[joint_cos, -joint_sin, 0, 0],
                    [joint_sin, joint_cos, 0, 0],
                    [0, 0, 1, 0],
                    [0, 0, 0, 1]])
        ]


        if joint_name.endswith("Pitch"):
            T = rotations[1] # rotation around y axis
        elif joint_name.endswith("Roll"):
            T = rotations[0] # rotation around x axis
        elif joint_name.endswith("Yaw"):
            T = rotations[2] # rotation around z axis
        else:
            print("Joint name error: " + joint_name + "\nDoes not end with Pitch, Roll, or Yaw" )
            return identity(4)

        T[0][3] = self.translation[joint_name][0]
        T[1][3] = self.translation[joint_name][1]
        T[2][3] = self.translation[joint_name][2]

        return T

    def forward_kinematics(self, joints):
        '''forward kinematics

        :param joints: {joint_name: joint_angle}
        '''
        for chain_joints in self.chains.values():
            T = identity(4)
            for joint in chain_joints:
                angle = joints.get(joint, 0.0)
                Tl = self.local_translation(joint, angle) # local transformation

                T = T @ Tl # multply transformation by fk

                self.transforms[joint] = T

if __name__ == '__main__':
    agent = ForwardKinematicsAgent()
    # test angles
    test_joints = {
        "HeadYaw": 0.5,
        "HeadPitch": 0.3,
        "LShoulderPitch": 1.0,
        "LShoulderRoll": 0.2,
        "LElbowYaw": 0.5,
        "LElbowRoll": -1.0,
        "LWristYaw": 0.0,
        "RShoulderPitch": 1.0,
        "RShoulderRoll": -0.2,
        "RElbowYaw": 0.5,
        "RElbowRoll": 1.0,
        "RWristYaw": 0.0,
        "LHipYawPitch": 0.0,
        "LHipRoll": 0.0,
        "LHipPitch": -0.5,
        "LKneePitch": 1.0,
        "LAnklePitch": -0.5,
        "LAnkleRoll": 0.0,
        "RHipYawPitch": 0.0,
        "RHipRoll": 0.0,
        "RHipPitch": -0.5,
        "RKneePitch": 1.0,
        "RAnklePitch": -0.5,
        "RAnkleRoll": 0.0
    }
    
    # calc Forward Kinematics 
    agent.forward_kinematics(test_joints)
    
    print("Forward Kinematics Test Results:")
    print("=" * 50)
    
    for chain_name, chain_joints in agent.chains.items():
        print(f"\n{chain_name} Chain:")
        for joint in chain_joints:
            T = agent.transforms[joint]
            position = T[0:3, 3]  # Extract position as a 1D array
            print(f"  {joint:20s}: Position = [{position[0]:7.4f}, {position[1]:7.4f}, {position[2]:7.4f}]")
    
    
    print(f"\nLWristYaw position: {agent.transforms['LWristYaw'][0:3, 3].A1}")
    print(f"RWristYaw position: {agent.transforms['RWristYaw'][0:3, 3].A1}")
    print(f"LAnkleRoll position: {agent.transforms['LAnkleRoll'][0:3, 3].A1}")
    print(f"RAnkleRoll position: {agent.transforms['RAnkleRoll'][0:3, 3].A1}")
    #agent.run()
