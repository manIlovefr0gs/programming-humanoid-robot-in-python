'''In this exercise you need to implement inverse kinematics for NAO's legs

* Tasks:
    1. solve inverse kinematics for NAO's legs by using analytical or numerical method.
       You may need documentation of NAO's leg:
       http://doc.aldebaran.com/2-1/family/nao_h21/joints_h21.html
       http://doc.aldebaran.com/2-1/family/nao_h21/links_h21.html
    2. use the results of inverse kinematics to control NAO's legs (in InverseKinematicsAgent.set_transforms)
       and test your inverse kinematics implementation.
'''

from numpy import array, identity, linalg, matmul, zeros, transpose
from numpy.linalg import pinv
from forward_kinematics import ForwardKinematicsAgent
from numpy.matlib import identity
import numpy as np


class InverseKinematicsAgent(ForwardKinematicsAgent):

    def compute_jacobian(self, chain_joints, current_angles):
        '''compute the Jacobian matrix for a given chain and current joint angles
        '''
        n_joints = len(chain_joints)
        jacobian = zeros((6, n_joints))
        
        # Get end effector position with current angles
        self.forward_kinematics(current_angles)
        end_joint = chain_joints[-1]
        T_end = self.transforms[end_joint]
        p_end = T_end[:3, 3]  # End effector position
        
        # Compute Jacobian 
        delta = 1e-6
        
        for i, joint in enumerate(chain_joints):
            # disturbing the angles a bit, bcause apperentlyy numerical m is not as precise as analytical m 
            perturbed_angles = current_angles.copy()
            current_angle = float(current_angles.get(joint, 0.0))
            perturbed_angles[joint] = current_angle + delta
            
            # Compute forward kinematics with perturbed angle
            self.forward_kinematics(perturbed_angles)
            T_perturbed = self.transforms[end_joint]
            p_perturbed = T_perturbed[:3, 3]
            
            # Linear velocity (position derivative)
            dp = (p_perturbed - p_end) / delta
            jacobian[:3, i] = dp.flatten()
            
            # Angular velocity
            jacobian[3:, i] = 0
        
        return jacobian



    def inverse_kinematics(self, effector_name, transform):
        '''solve the inverse kinematics

        :param str effector_name: name of end effector, e.g. LLeg, RLeg
        :param transform: 4x4 transform matrix
        :return: list of joint angles
        '''
        joint_angles = []
        
        max_iterations = 1000
        tolerance = 1e-4
        lambda_damping = 0.001  # Damping factor for numerical stability
        
        # Get the chain joints for this effector
        chain_joints = self.chains.get(effector_name, [])
        if not chain_joints:
            print(f"Unknown effector name: {effector_name}")
            return joint_angles
        
        # Initialize current angles to zero/current perception values
        current_angles = {joint: float(self.perception.joint.get(joint, 0.0)) 
                         for joint in self.joint_names}
        
        target_position = np.array(transform[:3, 3]).flatten()
        
        # Jacobian invrese kinematics it
        for iteration in range(max_iterations):
            #  forward kinematics with current angles
            self.forward_kinematics(current_angles)
            
            # Get current end effector position
            end_joint = chain_joints[-1]
            current_transform = self.transforms[end_joint]
            current_position = np.array(current_transform[:3, 3]).flatten()
            
            # calc pos error
            position_error = target_position - current_position
            error_magnitude = linalg.norm(position_error)
            
        
            J = self.compute_jacobian(chain_joints, current_angles)
            J_pos = J[:3, :]
            
            # Damped least squares inverse
            JJT = matmul(J_pos, transpose(J_pos))
            damping_matrix = lambda_damping * identity(3)
            J_damped_inv = matmul(transpose(J_pos), linalg.inv(JJT + damping_matrix))
            
            # matmul -> nice matrix multiplication
            delta_theta = matmul(J_damped_inv, position_error)
            delta_theta = np.array(delta_theta).flatten()
            
            # Update joint angles with constraints
            for i, joint in enumerate(chain_joints):
                delta_value = float(delta_theta[i])
                new_angle = float(current_angles[joint] + delta_value)
                current_angles[joint] = new_angle
        
        # Extract final joint angles for the chain
        joint_angles = [current_angles[joint] for joint in chain_joints]
        
        return joint_angles

    def set_transforms(self, effector_name, transform):
        '''solve the inverse kinematics and control joints use the results
        '''
        joint_angles = self.inverse_kinematics(effector_name, transform)
        
        # Get the chain joints directly from self.chains
        chain_joints = self.chains.get(effector_name, [])
        
        # keyframe: (time, joint_names, joint_angles)
        if joint_angles and chain_joints:
            times = [0]  
            names = [chain_joints]
            angles = [joint_angles]
            
            self.keyframes = (times, names, angles)
        else:
            # No solution 
            self.keyframes = ([], [], [])

        

if __name__ == '__main__':
    agent = InverseKinematicsAgent()
    # test inverse kinematics
    T = identity(4)
    T[-1, 1] = 0.05
    T[-1, 2] = -0.26
    agent.set_transforms('LLeg', T)
    print("=== DEBUG: angle_interpolation start ===")
    print("keyframes[0] (joint names):", agent.keyframes[0])
    print("keyframes[1] (times):", agent.keyframes[1])
    print("keyframes[2] (angles):", agent.keyframes[2])
#agent.run()
