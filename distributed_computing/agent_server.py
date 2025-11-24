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
import communication_pb2 as robot_pb2
import communication_pb2_grpc as robot_pb2_grpc
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
        return empty_pb2.Empty()

    def execute_keyframes(self, request, context):
        '''excute keyframes, note this function is blocking call,
        e.g. return until keyframes are executed
        '''
        return empty_pb2.Empty()

    def get_transform(self, request, context):
        '''get transform with given name
        '''
        return robot_pb2.TransformResponse(name=request.name)

    def set_transform(self, request, context):
        '''solve the inverse kinematics and control joints use the results
        '''
        return robot_pb2.SetTransformResponse()

    def hello(self, request, context):
        return robot_pb2.HelloResponse(hello_answer=f"Hello {request.name}")


if __name__ == '__main__':
   
    serve()
    print("Starting server...")
    
    

