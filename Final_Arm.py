import sys
import time
import math
from time import sleep
import numpy as np
import hubo_ach as ha
import ach
from ctypes import *
from time import gmtime, strftime

Goal=np.array([0.5,0.15,0.5])
DeltaTheta = 0.06 #in radian
Error = 0.06 #equals 1% of the total length of arm
step = .05 #in meter

pi = 3.141592654
Theta_init=np.array([0.0,0.0,0.0,0.0,0.0,0.0])#represent the angles of the MDS robot, namely the Shoulder pitch, shoulder roll, shoulder yaw, elbow pitch, wrist yaw, wrist roll, respictivily.
Length = np.array([0.24551,0.282575,0.3127375,0.0635])#represent the lengths of the arm components. namely the shoulder, the arm, the forearm and the hand/fingers
l1 = Length[0]#the shoulder
l2 = Length[1]#the arm
l3 = Length[2]#the forearm
l4 = Length[3]#the hand/fingers

ROBOT_TIME_CHAN  = 'state.time'
#t = ach.Channel(ROBOT_TIME_CHAN)
#t.flush()

freq = 10
period = 1/freq
PI = 3.141529
# Open Hubo-Ach feed-forward and feed-back (reference and state) channels
s = ach.Channel(ha.HUBO_CHAN_STATE_NAME)
r = ach.Channel(ha.HUBO_CHAN_REF_NAME)
s.flush()
r.flush()
# feed-forward will now be refered to as "state"
state = ha.HUBO_STATE()
# feed-back will now be refered to as "ref"
ref = ha.HUBO_REF()
# Get the current feed-forward (state) 
[statuss, framesizes] = s.get(state, wait=False, last=False)



def 	GetFK(theta):
	#new identity matrices to initiate the transformation matrices.
	T01=np.identity(4)#for the shoulder pitch and translation
	T12=np.identity(4)#for the shoulder roll
	T23=np.identity(4)#for the shoulder yaw
	T34=np.identity(4)#for the elbow pitch and translation 
	T45=np.identity(4)#for the wrist yaw and translation
	T56=np.identity(4)#for the wrist roll 
	T67=np.identity(4)#for the hand translation

	#for the shoulder pitch and translation
	T01[0,0]=np.cos(theta[0])
	T01[2,2]=T01[0,0]
	T01[0,2]=np.sin(theta[0])
	T01[2,0]=-1*T01[0,2]
	T01[1,3]=l1
	#for the shoulder roll
	T12[1,1]=np.cos(theta[1])
	T12[2,2]=T12[1,1]
	T12[1,2]=-1*np.sin(theta[1])
	T12[2,1]=-1*T12[0,2]
	T12[1,3]=0
	#for the shoulder yaw
	T23[0,0]=np.cos(theta[2])
	T23[1,1]=T23[0,0]
	T23[0,1]=-1*np.sin(theta[2])
	T23[1,0]=-1*T23[0,1]
	T23[1,3]=0
	#for the elbow pitch and translation
	T34[0,0]=np.cos(theta[3])
	T34[2,2]=T34[0,0]
	T34[0,2]=np.sin(theta[3])
	T34[2,0]=-1*T34[0,2]
	T34[2,3]=-1*l2
	#for the wrist yaw and translation
	T45[0,0]=np.cos(theta[4])
	T45[1,1]=T45[0,0]
	T45[0,1]=-1*np.sin(theta[4])
	T45[1,0]=-1*T45[0,1]
	T45[2,3]=-1*l3
	#for the wrist roll
	T56[1,1]=np.cos(theta[5])
	T56[2,2]=T56[1,1]
	T56[1,2]=-1*np.sin(theta[5])
	T56[2,1]=-1*T56[1,2]
	T56[1,3]=0
	#for the hand translation
	T67[2,3]=-1*l4
	#cross multiplying the matrices with each other to get the final transformation matrix
	T=np.dot(T01,T12)
	T=np.dot(T,T23)
	T=np.dot(T,T34)
	T=np.dot(T,T45)
	T=np.dot(T,T56)
	T=np.dot(T,T67)
	#print "T01 is : "
	#print T01
	#print "T12 is : "
	#print T12
	#print "T23 is : "
	#print T23
	#print "T34 is : "
	#print T34
	#print "T45 is : "
	#print T45
	#print "T56 is : "
	#print T56
	#print "T67 is : "
	#print T67
	#print "T is : "
	#print T
	#calculating the x, y and z Angles of endeffector location 
	ThetaX= round(math.atan2(T[2,1],T[2,2]),1)*180/pi
	ThetaY= round(math.atan2(-1*T[2,0],math.pow(T[2,1],2)+math.pow(T[2,2],2)),1)*180/pi
	ThetaZ= round(math.atan2(T[1,0],T[0,0])*180/pi,1)
	Theta=np.array([ThetaX,ThetaY,ThetaZ])
	#multipling the final coordination matrix with the coordinates of the hand effector in the last space to get the location vector T
	T=np.dot(T,np.array([[0],[0],[0],[1]]))
	x=round(T[0],3)#extracting x value of the end effector from the location vector
	y=round(T[1],3)#extracting y value of the end effector from the location vector
	z=round(T[2],3)#extracting z value of the end effector from the location vector
	e=np.array([x,y,z])
	print "E is : +++++++++++++++++++++",e
	return (e,Theta)	


#a function to calculate the distance between the end-effector and the origin
def 	GetDist(Endeffector,Goal):
	return np.sqrt((np.power((Endeffector[0]-Goal[0]),2)+np.power((Endeffector[1]-Goal[1]),2)+np.power((Endeffector[2]-Goal[2]),2)))


#Theta = Theta_init
#print "Theta_init is : ",Theta_init
#EndEffector,Theta_endeffector = GetFK(Theta_init)#extracting information from hte FK function
#print "EndEffector  is : ",EndEffector

#Distance=GetDist(EndEffector,(np.array([0,0,0])))
#print "Distance is : ",Distance

#print "FINAL Theta of endeffector ThetaX,  ThetaY, ThetaZ IS :  ", Theta_endeffector


def 	GetNextPointDelta(EndEffector,Goal,Step):
	Slope = Goal - EndEffector
	UnitVector = Slope/GetDist(Slope,np.array([0,0,0]))
	StepVector = 	UnitVector*Step
	return (StepVector)

def 	GetJacobian (DeltaTheta,Theta):
	EndEffector = GetFK(Theta)
	for i in range(0,len(EndEffector)):
		for j in range(0,len(Theta)):
			ThetaNew = Theta 
			ThetaNew[j] = Theta[j] + DeltaTheta
			DeltaEndEffector = GetFK(ThetaNew)[i] - EndEffector[i]
			#x=DeltaEndEffector[i]/DeltaTheta
			Jacobian[i,j]=DeltaEndEffector[i]/DeltaTheta  #DeltaEndEffector/DeltaTheta
	return Jacobian
 

def update_Hand_Location(current_theta):
#	T0_actual = time.time()
#	t.get(tim, wait=False, last=True)
#	T0_sim=tim.sim[0]
	ref.ref[ha.LSP]=current_theta[0]
	ref.ref[ha.LSR]=current_theta[1]
	ref.ref[ha.LSY]=current_theta[2]
	ref.ref[ha.LEB]=current_theta[3]
	ref.ref[ha.LWY]=current_theta[4]
	ref.ref[ha.LWP]=current_theta[5]
	r.put(ref)
#	Delta_t_sim=tim.sim[0]-T0_sim
#	Delta_t_actual=time.time()-T0_actual
#	ratio=Delta_t_sim / Delta_t_actual
#	time.sleep(ratio*max(0,(period-(time.time()-T0_actual))))
	time.sleep(.0)	
	return None	

Theta = Theta_init
print "Theta_init is : ",Theta_init
EndEffector,EndEffector_Theta = GetFK(Theta_init)
print "EndEffector  is : ",EndEffector
print "Goal  is : ",Goal

Jacobian = np.zeros(shape=(3,len(Theta)))
x=GetDist(EndEffector,Goal)
print "Distance is : ",x
print "Error is : ",Error
Theta_now=Theta_init
while np.all(x>Error):
	Jacobian=GetJacobian(DeltaTheta,Theta)
	PseduInvertedJacobian=np.linalg.pinv(Jacobian)
	DeltaEndEffector=GetNextPointDelta(EndEffector,Goal,step)
	DeltaTheta2=np.dot(PseduInvertedJacobian,DeltaEndEffector)
	Theta_now = Theta_now + DeltaTheta2
	update_Hand_Location(Theta_now)
	EndEffector,EndEffector_Theta = GetFK(Theta_now)
	x=GetDist(EndEffector,Goal)
	print "EndEffector is : ",EndEffector, "     Distance is : ",x	
	time.sleep(0.1)

print "FINAL THETA IS :  ", Theta