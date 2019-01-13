
import numpy as np
import random as rand

class QLearner(object):

    def __init__(self, \
        num_states=100, \
        num_actions = 4, \
        alpha = 0.2, \
        gamma = 0.9, \
        rar = 0.5, \
        radr = 0.99, \
        dyna = 200, \
        verbose = False):

        self.verbose = verbose
        self.num_actions = num_actions
        self.s = 0
        self.a = 0

        self.rar = rar
        self.radr = radr
        self.alpha = alpha
        self.gamma = gamma
       
        #Set the current Q table and Reward table to zeros
        self.Q = np.zeros((num_states, num_actions))
        self.r = np.zeros((num_states, num_actions))

        # Transition table, state, action, new state
        self.t = np.zeros((num_states, num_actions, num_states))
        self.t_count = self.t.copy()

        self.dyna = dyna
        self.num_states = num_states
        self.num_actions = num_actions


    def bestMove(self,s):
        retval = self.Q[s,:].argmax()
        return retval

    def querysetstate(self, s):
        """
        @summary: Update the state without updating the Q-table
        @param s: The new state
        @returns: The selected action
        """
        #Pick highest reward
        max_Q = self.Q[s, :].argmax()
       
        # If random action rate is higher than random distribution, Pick a random action
        if np.random.uniform() < self.rar:
            action = rand.randint(0, self.num_actions-1)
        # Pick the action with the highest reward.
        else:
            action = max_Q

        #Update self but not Q table.
        self.s = s
        self.a = action

        if self.verbose: print "s =", s,"a =",action
        return action

    def query(self,s_prime,r):
        """
        @summary: Update the Q table and return an action
        @param s_prime: The new state
        @param r: The ne state
        @returns: The selected action
        """
        
        max_Q = self.Q[s_prime, :].argmax()
        if np.random.uniform() < self.rar:
            action = rand.randint(0,self.num_actions-1)
        else:
            action = max_Q
        # Old Value is the qTable location where we were
        old_value = self.Q[self.s, self.a]
        # New Value is qTable location of next action
        new_value = self.Q[s_prime, action]
        
        # Sets Q table using learning rate
        self.Q[self.s, self.a] = (1.0 - self.alpha) * old_value + self.alpha * (r + self.gamma * new_value)

        # Update rar as stated in prompt
        self.rar = self.rar * self.radr

        # Dyna Mode
        if (self.dyna != 0):
            self.t_count[self.s, self.a, s_prime] = (self.t_count[self.s, self.a, s_prime] + 1)
            self.t = self.t_count / self.t_count.sum(axis=2, keepdims=True)
            self.r[self.s,self.a] = ((1 - self.alpha) * self.r[self.s, self.a]) + (self.alpha * r)

            self.simulate()

        self.s = s_prime
        self.a = action

        if self.verbose: print "s =", s_prime,"a =",action,"r =",r
        return action

    # Experience random simulations of the world.
    def simulate(self):
        for i in range(self.dyna):
            # Randomly Select S
            random_state = rand.randint(0, self.num_states-1)
            # Randomly Select A
            random_action = rand.randint(0, self.num_actions -1)
            # Consult T to find S_Prime
            t_temp = self.t[random_state, random_action, :]
            new_state = np.random.multinomial(100, t_temp).argmax()
            r_temp = self.r[random_state, random_action]
            
            max_Q = self.Q[new_state, :].argmax()
            
            old_value = (1- self.alpha) * self.Q[random_state, random_action]
            new_value = self.alpha * (r_temp + (self.gamma * self.Q[new_state, max_Q]))

            self.Q[random_state, random_action] = old_value + new_value

if __name__=="__main__":
    print "Remember Q from Star Trek? Well, this isn't him"
