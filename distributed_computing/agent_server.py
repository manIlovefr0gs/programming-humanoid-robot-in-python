'''In this file you need to implement remote procedure call (RPC) server

* There are different RPC libraries for python, such as xmlrpclib, json-rpc. You are free to choose.
* The following functions have to be implemented and exported:
 * get_angle
 * set_angle
 * get_posture
 * execute_keyframes
 * get_transform
 * set_transform
* You can test RPC server with ipython before implementing agent_client.py
'''

# add PYTHONPATH
import os
import sys
import grpc
import numpy as np
import communication_pb2 as robot_pb2
import communication_pb2_grpc as robot_pb2_grpc
import json
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'kinematics'))

from inverse_kinematics import InverseKinematicsAgent
from concurrent import futures
from google.protobuf import empty_pb2


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    agent = ServerAgent()
    agent.start()

    robot_pb2_grpc.add_AgentServiceServicer_to_server(
    agent, 
    server
    )

    server.add_insecure_port("[::]:50051")   
    server.start()
    server.wait_for_termination()


class ServerAgent(InverseKinematicsAgent, robot_pb2_grpc.AgentServiceServicer):
    '''ServerAgent provides RPC service
    '''
    
   
    
    def get_angle(self, request, context):
        '''get sensor value of given joint'''
        joint_name = request.joint_name
        angle = self.perception.joint.get(joint_name)

        return robot_pb2.AngleResponse(angle=angle)

    def set_angle(self, request, context):
        '''set target angle of joint for PID controller
        '''
        joint_name = request.joint_name
        angle = request.angle
        #print(f"Setting {joint_name} to {angle}")
        #print(f"All joint before: {self.target_joints}")

        self.target_joints[joint_name] = angle
        #print(f"All target joints: {self.target_joints}")
        return empty_pb2.Empty()

    def get_posture(self, request, context):
        '''return current posture of robot'''
        result = self.recognize_posture(self.perception)
        return robot_pb2.GetPostureResponse(posture=result)

    def execute_keyframes(self, request, context):
        '''excute keyframes, note this function is blocking call,
        e.g. return until keyframes are executed
        '''
        keyframes_json = request.keyframes
        keyframes = json.loads(keyframes_json)

        print(f"Executing keyframes: {keyframes}")


        self.keyframes = keyframes 



        return empty_pb2.Empty()

    def get_transform(self, request, context):
        '''get transform with given name
        '''
        name = request.name
        T = self.transforms.get(name)
        
        if T is None:
            print(f"ERROR: Transform '{name}' not found")
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Transform '{name}' not found")
            return robot_pb2.TransformResponse()
                
        flat_data = np.array(T).flatten()
        data_list = [float(x) for x in flat_data]
        

        transform = robot_pb2.Transform()
        #print("Empty Transform created")
        
        transform.rows = int(T.shape[0])
        #print(f"rows set to {transform.rows}")
        
        transform.cols = int(T.shape[1])
        #print(f"cols set to {transform.cols}")
        
        #print("Set data...")
        transform.data.extend(data_list)  
        #print("data set successfully")
           

        response = robot_pb2.TransformResponse(
            name=name,
            transform=transform
        )

        #print(f"Transform: , {response}")

        return response

    
        
    

    def set_transform(self, request, context):
        '''solve the inverse kinematics and control joints use the results
        '''
        effector_name = request.effector_name
        transform = request.transform
        
        print(f"=== DEBUG set_transform ===")
        print(f"Effector name: {effector_name}")
        
        transform_data = np.array(transform.data)
        T = transform_data.reshape(transform.rows, transform.cols)
        
        print(f"Target transform shape: {T.shape}")
        print(f"Target transform:\n{T}")
        
        joint_angles = self.inverse_kinematics(effector_name, T)
        
        print(f"Calculated joint_angles: {joint_angles}")
        
        chain_joints = self.chains.get(effector_name, [])
        print(f"Chain joints for {effector_name}: {chain_joints}")

        angles = [float(a) for a in joint_angles]

        for joint_name, angle in zip(chain_joints, angles):
            self.target_joints[joint_name] = angle
            print(f"  Set {joint_name} = {angle}")
        
        print(f"Updated target_joints: {self.target_joints}")
        
        response = robot_pb2.SetTransformResponse(
            joint_names=chain_joints,
            joint_angles=angles
        )
        return response




    def hello(self, request, context):
        return robot_pb2.HelloResponse(hello_answer=f"Hello {request.name}")


if __name__ == '__main__':
   
    serve()
    print("Starting server...")
    
    

