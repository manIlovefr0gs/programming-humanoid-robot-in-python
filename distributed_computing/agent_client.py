'''In this file you need to implement remote procedure call (RPC) client

* The agent_server.py has to be implemented first (at least one function is implemented and exported)
* Please implement functions in ClientAgent first, which should request remote call directly
* The PostHandler can be implement in the last step, it provides non-blocking functions, e.g. agent.post.execute_keyframes
 * Hints: [threading](https://docs.python.org/2/library/threading.html) may be needed for monitoring if the task is done
'''

import weakref
import grpc
import communication_pb2 as robot_pb2
import communication_pb2_grpc as robot_pb2_grpc
import time
import numpy as np
import json
import os
import sys

sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'joint_control'))
from keyframes import *

class PostHandler(object):
    '''the post hander wraps function to be excuted in paralle
    '''
    def __init__(self, obj):
        self.proxy = weakref.proxy(obj)

    def execute_keyframes(self, keyframes):
        '''non-blocking call of ClientAgent.execute_keyframes'''
        # YOUR CODE HERE

    def set_transform(self, effector_name, transform):
        '''non-blocking call of ClientAgent.set_transform'''
        # YOUR CODE HERE


class ClientAgent(object):
    '''ClientAgent request RPC service from remote server
    '''
    def __init__(self):
        self.post = PostHandler(self)
        self.address = "localhost:50051"
        self.channel = None
        self.stub = None
    
    def connect(self):
        """connects to server"""
        self.channel = grpc.insecure_channel(self.address)
        self.stub = robot_pb2_grpc.AgentServiceStub(self.channel)

    
    def hello(self, name):
        """check if connection is established"""
        request = robot_pb2.HelloRequest(name=name)
        response = self.stub.hello(request)
        return response.hello_answer


    def get_angle(self, joint_name):
        '''get sensor value of given joint'''
        request = robot_pb2.AngleRequest(joint_name=joint_name)
        response = self.stub.get_angle(request)
        return response.angle


    def set_angle(self, joint_name, angle):
        '''set target angle of joint for PID controller
        '''
        request = robot_pb2.SetAngleRequest(
        joint_name=joint_name,
        angle=angle
    )
        self.stub.set_angle(request)


    def get_posture(self):
        '''return current posture of robot'''
        request = robot_pb2.GetPostureRequest()
        response = self.stub.get_posture(request)
        return response.posture

    def execute_keyframes(self, keyframes):
        '''excute keyframes, note this function is blocking call,
        e.g. return until keyframes are executed
        '''
        # convert keyframes to json string
        keyframes_json = json.dumps(keyframes)
    
        request = robot_pb2.ExecuteKeyframesRequest(keyframes=keyframes_json)
        
        self.stub.execute_keyframes(request)



    def get_transform(self, name):
        '''get transform with given name
        '''
        request = robot_pb2.TransformRequest(name=name)
        response = self.stub.get_transform(request)

        transform_data = np.array(response.transform.data)
        transform_matrix = transform_data.reshape(
            response.transform.rows, 
            response.transform.cols
        )
        return transform_matrix

    def set_transform(self, effector_name, transform):
        '''solve the inverse kinematics and control joints use the results
        '''
        T = np.array(transform)
    
        # convert to flat list -> data_list for transform msg
        flat_data = T.flatten()
        data_list = [float(x) for x in flat_data]

        # create Transform message
        transform_msg = robot_pb2.Transform()
        transform_msg.rows = int(T.shape[0])
        transform_msg.cols = int(T.shape[1])
        transform_msg.data.extend(data_list)

        request = robot_pb2.SetTransformRequest(
            effector_name=effector_name,
            transform=transform_msg
        )

        response = self.stub.set_transform(request)

        return {
            'joint_names': list(response.joint_names),
            'joint_angles': list(response.joint_angles)
        }


if __name__ == '__main__':
    #agent = ClientAgent()
    client = ClientAgent()
    client.connect()
    print(client.hello("World"))
    print("Angle of HeadYaw:", client.get_angle("HeadYaw"))
    print("--------------------------------")
    angle = -1
    client.set_angle("HeadYaw", angle)
    print(f"New angle set to {angle}")
    time.sleep(3)
    print("Target angle:", client.get_angle("HeadYaw"))
    print("--------------------------------")
    print("Current posture:", client.get_posture())
    print("--------------------------------")
    keyframes = leftBellyToStand()
    print("Executing keyframes:")
    client.execute_keyframes(keyframes)
    print("Keyframes executed.")

    print("---------------------------------")
    joint = "HeadYaw"
    transform = client.get_transform(joint)
    print(f"Transform for {joint}:")
    print(transform)
    target_transform = np.array([
        [1, 0, 0, 0.0],
        [0, 1, 0, 0.05],  
        [0, 0, 1, -0.3],   
        [0, 0, 0, 1]
        ])
      
    result = client.set_transform("LLeg", target_transform)
    print("Set transform result:")
    print(f"  Joints: {result['joint_names']}")
    print(f"  Angles: {result['joint_angles']}")

 
    



