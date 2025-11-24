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
        response = self.stub.Hello(request)
        return response.hello_answer


    def get_angle(self, joint_name):
        '''get sensor value of given joint'''
        # YOUR CODE HERE
    
    def set_angle(self, joint_name, angle):
        '''set target angle of joint for PID controller
        '''
        # YOUR CODE HERE

    def get_posture(self):
        '''return current posture of robot'''
        # YOUR CODE HERE

    def execute_keyframes(self, keyframes):
        '''excute keyframes, note this function is blocking call,
        e.g. return until keyframes are executed
        '''
        # YOUR CODE HERE

    def get_transform(self, name):
        '''get transform with given name
        '''
        # YOUR CODE HERE

    def set_transform(self, effector_name, transform):
        '''solve the inverse kinematics and control joints use the results
        '''
        # YOUR CODE HERE


if __name__ == '__main__':
    #agent = ClientAgent()
    client = ClientAgent()
    client.connect()
    print(client.hello("World"))


