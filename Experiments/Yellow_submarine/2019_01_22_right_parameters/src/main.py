from yellow_submarine.maxcut_solver_tf import MaxCutSolver, ParametrizedGate
from strawberryfields.ops import *
import tensorflow as tf
from scipy.stats import rv_discrete
import pdb
from collections import Counter
import sys

def number_to_base(n, b, length):
    # Source: https://stackoverflow.com/questions/2267362/how-to-convert-an-integer-in-any-base-to-a-string
    digits = [0] * length
    if n == 0:
        return digits
    i = 0
    while n:
        digits[i] = int(n % b)
        i += 1
        n //= b
    return digits[::-1]

def list_to_number(l, b):
    number = 0
    for power, el in enumerate(l[::-1]):
        number += el*b**power
    return number

def run_single_test(learner_params, training_params, matrices, gates_structure):
    log = {'Trace': 'trace'}
    max_cut_solver = MaxCutSolver(learner_params, training_params, matrices, gates_structure, log=log)

    final_cost, all_probs = max_cut_solver.train_and_evaluate_circuit(verbose=False)
    return final_cost, all_probs

def assess_cost_based_on_output(outputs, A):
    cost = 0
    for encoding in outputs:
        cost += calculate_cost_for_encoding(A, encoding) 
    return cost / len(outputs)

def calculate_cost_for_encoding(A, encoding):
    cost_value = 0
    for i in range(len(encoding)):
        for j in range(len(encoding)):
            cost_value += 0.5 * A[i][j] * (encoding[i] - encoding[j])**2
    return cost_value

def main(run_id=0, learning_rate=0.1, regularization=1e-3):
    matrix_divisor = 3
    c = 0
    A = np.array([[c, 1, 1, 0],
        [1, c, 1, 1],
        [1, 1, c, 1],
        [0, 1, 1, c]])
    A = A / matrix_divisor

    interferometer_matrix = \
        np.array(
            [[1, -1, 1, -1],
            [1, 1, 1, 1],
            [-1, -1, 1, 1],
            [1, -1, -1, 1]
            ]) / 2

    matrices = [A, interferometer_matrix]

    learner_params = {
        'task': 'optimization',
        'regularization_strength': regularization,
        'optimizer': 'SGD',
        'init_learning_rate': learning_rate,
        'log_every': 1,
        'print_log': False
        }


    steps = 500

    training_params = {
        'steps': steps,
        'cutoff_dim': 17
        }

    gates_structure = []
    gates_structure.append([Sgate, 0, {"constant": np.random.random() - 0.5, "name": 's_magnitude_0', 'regularize': True, 'monitor': True},
        {"constant": np.random.random()*2*np.pi, "name": 's_phase_0', 'regularize': True, 'monitor': True}])
    gates_structure.append([Sgate, 1, {"constant": np.random.random() - 0.5, "name": 's_magnitude_1', 'regularize': True, 'monitor': True},
        {"constant": np.random.random()*2*np.pi, "name": 's_phase_1', 'regularize': True, 'monitor': True}])
    gates_structure.append([Sgate, 2, {"constant": np.random.random() - 0.5, "name": 's_magnitude_2', 'regularize': True, 'monitor': True},
        {"constant": np.random.random()*2*np.pi, "name": 's_phase_2', 'regularize': True, 'monitor': True}])
    gates_structure.append([Sgate, 3, {"constant": np.random.random() - 0.5, "name": 's_magnitude_3', 'regularize': True, 'monitor': True},
        {"constant": np.random.random()*2*np.pi, "name": 's_phase_3', 'regularize': True, 'monitor': True}])

    gates_structure.append([Dgate, 0, {"constant": np.random.random() - 0.5, "name": 'd_magnitude_0', 'regularize': True, 'monitor': True},
        {"constant": np.random.random()*2*np.pi, "name": 'd_phase_0', 'regularize': True, 'monitor': True}])
    gates_structure.append([Dgate, 1, {"constant": np.random.random() - 0.5, "name": 'd_magnitude_1', 'regularize': True, 'monitor': True},
        {"constant": np.random.random()*2*np.pi, "name": 'd_phase_1', 'regularize': True, 'monitor': True}])
    gates_structure.append([Dgate, 2, {"constant": np.random.random() - 0.5, "name": 'd_magnitude_2', 'regularize': True, 'monitor': True},
        {"constant": np.random.random()*2*np.pi, "name": 'd_phase_2', 'regularize': True, 'monitor': True}])
    gates_structure.append([Dgate, 3, {"constant": np.random.random() - 0.5, "name": 'd_magnitude_3', 'regularize': True, 'monitor': True},
        {"constant": np.random.random()*2*np.pi, "name": 'd_phase_3', 'regularize': True, 'monitor': True}])

    gates_structure.append([Kgate, 0, {"constant": np.random.random() - 0.5, "name": 'kerr_0', 'regularize': True, 'monitor': True}])
    gates_structure.append([Kgate, 1, {"constant": np.random.random() - 0.5, "name": 'kerr_1', 'regularize': True, 'monitor': True}])
    gates_structure.append([Kgate, 2, {"constant": np.random.random() - 0.5, "name": 'kerr_2', 'regularize': True, 'monitor': True}])
    gates_structure.append([Kgate, 3, {"constant": np.random.random() - 0.5, "name": 'kerr_3', 'regularize': True, 'monitor': True}])
    

    model_dir = "logsAuto_lr_" + str(learning_rate) + "_" + str(regularization) + "_" + str(run_id)  
    training_params['model_dir'] = model_dir
    cost, all_probs = run_single_test(learner_params, training_params, matrices, gates_structure)
    total_prob = np.sum(all_probs)
    all_probs = all_probs / total_prob
    cutoff_dim = training_params['cutoff_dim']
    values_flat = [list_to_number(i, cutoff_dim) for i in np.ndindex(all_probs.shape)]
    indices_array = np.reshape(values_flat, all_probs.shape)
    final_distribution = rv_discrete(values=(indices_array, all_probs))
    circuit_outputs_raw = final_distribution.rvs(size=1000)
    circuit_outputs_num = [number_to_base(i, cutoff_dim, len(A)) for i in circuit_outputs_raw]
    circuit_outputs_clipped = [np.clip(i, 0, 1) for i in circuit_outputs_num]
    circuit_outputs_str = [str(i) for i in circuit_outputs_clipped]
    output_counter = Counter(circuit_outputs_str)
    print("cost:", cost)
    print("total prob:", total_prob)
    for el in output_counter.most_common()[:10]:
        print(el)
    cost_from_output = assess_cost_based_on_output(circuit_outputs_clipped, A)
    print("cost from output:", cost_from_output)


if __name__ == '__main__':
    main(int(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3]))