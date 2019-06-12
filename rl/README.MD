# Reinforcement learning using MAB


## Requisites

The MAB module uses numpy

```
sudo python3 -m pip install numpy
```

## Running the agent

To use the program you must implement at least the _run_action()_ function of the __MABAgent__ class.
This function is in the _agent.py_ file.
It should map the selected action (passed as a parameter), and which is an integer, to the actual action to be taken by the agent in the environment.
The action must be performed.
If it succeeds, the function should seek reward from the environment.
The function then returns with the reward value and a boolean informing whether the action was successful or not.

You can use one of three policies:
* RandomAbstract: select random actions
* EpsilonGreedyAbstract: select action using an epsilon-greedy policy
* UCBAbstract: selects actions based on the UCB policy

To select which one will be used, just define it as superclass of the class __MABAgent__.

I also suggest that you change the default value in the line "parser.add_argument('--n-actions'....".
This way, you only need to call

```
    python3 agent.py
```

to run the agent.