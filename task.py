import numpy as np
from physics_sim import PhysicsSim

class Task():
    """Task (environment) that defines the goal and provides feedback to the agent."""
    def __init__(self, init_pose=None, init_velocities=None,
                 init_angle_velocities=None, runtime=5., target_pos=None):
        """Initialize a Task object.
        Params
        ======
            init_pose: initial position of the quadcopter in (x,y,z) dimensions and the Euler angles
            init_velocities: initial velocity of the quadcopter in (x,y,z) dimensions
            init_angle_velocities: initial radians/second for each of the three Euler angles
            runtime: time limit for each episode
            target_pos: target/goal (x,y,z) position for the agent
        """
        # Simulation
        self.sim = PhysicsSim(init_pose, init_velocities, init_angle_velocities, runtime) 
        self.action_repeat = 3

        self.init_pose = init_pose
        self.init_velocities = init_velocities
        self.init_angle_velcities = init_angle_velocities


        self.state_size = self.action_repeat * 7
        self.action_low = 0
        self.action_high = 900
        self.action_size = 4

        self.init_pose = np.array(init_pose if init_pose is not None else np.array([25., 25., 120., 0, 0, 0]))

        # Goal
        self.target_pos = np.array(target_pos if target_pos is not None else np.array([0., 0., 10.]))

        self.dist = abs(self.init_pose[:3] - self.target_pos).sum()
        self.last_dist = self.dist

        self.init_dist = abs(self.init_pose[:3] - self.target_pos).sum()
        self.init_vdist = abs(self.sim.pose[2] - self.target_pos[2])
        self.init_hdist = abs(self.sim.pose[:2] - self.target_pos[:2]).sum()
        self.last_vdist = self.init_vdist
        self.last_hdist = self.init_hdist
        self.last_pos = np.array(self.init_pose[:3])
        self.speed = 0
        self.proximity = 0

        self.speed_limit = 0.1

    def get_reward(self):
        """Uses current pose of sim to return reward."""

        self.dist = abs(self.sim.pose[:3] - self.target_pos).sum()
        self.vdist = abs(self.sim.pose[2] - self.target_pos[2])
        self.hdist = abs(self.sim.pose[:2] - self.target_pos[:2]).sum()
        self.speed = abs(self.last_vdist - self.vdist)

        if not self.proximity:
            if self.vdist < 20:
                self.proximity = 1

        # GENTLE LANDING
        # return 1 - (self.vdist/self.init_vdist) * 1.5
        proximity_reward = 1 - (self.vdist/self.init_vdist)


        speed_penalty = (1 - max(self.speed, 0.05)/1) ** (1 - (self.vdist / self.init_vdist))
        if np.isnan(speed_penalty):
            speed_penalty = 0.01



        #if self.vdist > 20:
        #    speed_penalty = 0.5

        #axis_adjust = 1
        #for axis in self.sim.pose[3:]:
            #if axis > 2:
                #axis_adjust = 0.5 / axis

        self.last_dist = self.dist
        self.last_vdist = self.vdist
        self.last_hdist = self.hdist
        #print(proximity_reward * speed_penalty)

        return proximity_reward * speed_penalty / self.action_repeat

        ''' Working Snapshot 
        proximity_reward = 1 - (self.vdist/self.init_vdist)

        speed_penalty = (1 - max(self.speed, 0.05)/1) ** (1 - (self.vdist / self.init_vdist))
        if np.isnan(speed_penalty):
            speed_penalty = 0.01

        return proximity_reward * speed_penalty #* axis_adjust
'''



    def step(self, rotor_speeds):
        self.rotor_speeds = self.clip(rotor_speeds)

        reward = 0
        pose_all = []
        for _ in range(self.action_repeat):
            done = self.sim.next_timestep(rotor_speeds) # update the sim pose and velocities
            reward += self.get_reward()
            state = list(self.sim.pose)
            state.append(self.speed)
            pose_all.append(state)
        next_state = np.concatenate(pose_all)
        """Uses action to obtain next state, reward, done."""

        #done = self.sim.next_timestep(self.rotor_speeds) # update the sim pose and velocities
        #reward = self.get_reward()
        #next_state = self.sim.pose

        #next_state.append(self.vdist)

        return next_state, reward, done

    def reset(self):
        """Reset the sim to start a new episode."""
        self.sim.reset()
        self.dist = abs(self.init_pose[:3] - self.target_pos).sum()
        self.last_dist = self.dist
        self.init_dist = self.dist
        self.init_vdist = abs(self.sim.pose[2] - self.target_pos[2])
        self.init_hdist = abs(self.sim.pose[:2] - self.target_pos[:2]).sum()
        self.last_vdist = self.init_vdist
        self.last_hdist = self.init_hdist
        self.last_pos = np.array(self.init_pose[:3])
        self.speed = 0
        self.state = list(self.sim.pose)
        self.state.append(self.speed)
        self.state = np.concatenate([self.state] * 3)

        return self.state

    def new_target(self, target_pose):
        self.target_pos = target_pose
        print('Destination updated.')

    def clip(self, action):
        return np.clip(np.array(action), self.action_low, self.action_high)