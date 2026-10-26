import itertools
import random

def counterbalance(trials_needed,shapes):

    # Define shapes
    # shapes = [1, 2, 3]

    # Generate all possible orders of shapes
    counterbalanced_orders = list(itertools.permutations(shapes))

    # Repeat the counterbalanced orders to meet the number of trials
    # Calculate how many repetitions are needed
    # trials_needed = 10
    repeats = trials_needed // len(counterbalanced_orders)
    extra = trials_needed % len(counterbalanced_orders)

    # Generate the trial list
    trials = counterbalanced_orders * repeats
    if extra > 0:
        trials += random.sample(counterbalanced_orders, extra)

    # Shuffle the trial list to randomize the order of repetitions
    random.shuffle(trials)

    # Print the trials
    print("Generated Trials:")
    for i, trial in enumerate(trials):
        print(f"Trial {i + 1}: {trial}")

    # Making a single list from 10 tuples
    Order=[]
    for i in range (0,len(trials)):
        a=trials[i]
        for j in a:
            Order.append(j)

    print (Order)
    print(len(Order))
    return Order

# Order=counterbalance(5,[1,2,3])
# print (Order)
# print(len(Order))