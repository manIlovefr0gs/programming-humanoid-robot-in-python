'''In this exercise you need to use the learned classifier to recognize current posture of robot

* Tasks:
    1. load learned classifier in `PostureRecognitionAgent.__init__`
    2. recognize current posture in `PostureRecognitionAgent.recognize_posture`

* Hints:
    Let the robot execute different keyframes, and recognize these postures.

'''


from angle_interpolation import AngleInterpolationAgent
from keyframes import *
import numpy as np
import pickle
from sklearn import svm


class PostureRecognitionAgent(AngleInterpolationAgent):
    def __init__(self, simspark_ip='localhost',
                 simspark_port=3100,
                 teamname='DAInamite',
                 player_id=0,
                 sync_mode=True):
        super(PostureRecognitionAgent, self).__init__(simspark_ip, simspark_port, teamname, player_id, sync_mode)
        self.posture = 'unknown'
        with open('robot_pose.pkl', 'rb') as f:
            self.posture_classifier = pickle.load(f)
        
        if isinstance(self.posture_classifier, svm.SVC):
            print("Classifier loaded successfully.")
        else:
            print("Error loading the classifier!")


    def think(self, perception):
        #print("Attributes of perception object:", dir(perception))
        #print("Current values in perception object:", perception.__dict__)
        print("Posture:", self.posture)
        self.posture = self.recognize_posture(perception)
        return super(PostureRecognitionAgent, self).think(perception)



    def recognize_posture(self, perception):
        posture = 'unknown'

        features = perception_to_features(perception).reshape(1, -1)  
        predicted_class = self.posture_classifier.predict(features)[0]
        return str(predicted_class)
        return posture


def perception_to_features(perception):

    features = [
        perception.joint['LHipYawPitch'],
        perception.joint['LHipRoll'],
        perception.joint['LHipPitch'],
        perception.joint['LKneePitch'],
        perception.joint['RHipYawPitch'],
        perception.joint['RHipRoll'],
        perception.joint['RHipPitch'],
        perception.joint['RKneePitch'],
        perception.imu[0],  
        perception.imu[1]   
        ]
    return np.array(features)

if __name__ == '__main__':
    agent = PostureRecognitionAgent()
    agent.keyframes = hello()  # CHANGE DIFFERENT KEYFRAMES
    agent.run()
