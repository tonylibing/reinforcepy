from reinforcepy.environments.ALE import ALEEnvironment
from reinforcepy.learners.dqn import DQNLearner
import time

EPOCH_DEF = 50000  # an epoch is defined as 50,000 steps in the NIPS paper


def load_config():
    # load config from json
    from reinforcepy.handlers import Parameters
    parameters = Parameters.fromJSON('dqn_cfg.json')
    return [parameters['network_parameters'], parameters['training_parameters'], parameters['learner_parameters'],
            parameters['experiment_parameters']]


def main(experiment_parameters):
    experiment_parameters.required(['epochs', 'save_interval', 'rom'])

    # load parameters
    network_parameters, training_parameters, learner_parameters, _ = load_config()

    # decide which network to import based on backend parameter
    if network_parameters.get('backend') == 'tensorflow':
        from reinforcepy.networks.dqn.tflow.dqn_nips import DQN_NIPS
        network = DQN_NIPS(network_parameters, training_parameters, log_dir='./runs/', log_steps=2500)
    else:
        from reinforcepy.networks.dqn.theanolasagne.dqn_nips import DQN_NIPS
        network = DQN_NIPS(network_parameters, training_parameters)

    # initialize environment and network/learner
    environment = ALEEnvironment(experiment_parameters.get('rom'), skip_frame=learner_parameters.get('skip_frame'))
    learner = DQNLearner(learner_parameters, network)
    learner.set_action_num(environment.get_num_actions())

    # main loop to run episodes until enough epochs have been reached
    # saves every save_interval
    ep_count = 0
    reward_list = list()
    st = time.time()
    # train until max epochs or keyboard interrupt
    try:
        while learner.step_count < experiment_parameters.get('epochs') * EPOCH_DEF:
            reward = learner.run_episode(environment)
            reward_list.append([reward, learner.step_count])
            print("Episode finished", "Reward:", reward, "SPS:", learner.step_count/(time.time() - st), learner.get_status())
            if experiment_parameters.get('save_interval') is not None:
                if learner.step_count > ep_count * EPOCH_DEF:
                    # save parameters
                    learner.save("./runs/dqn_{0:.2f}".format(ep_count))
                    ep_count += experiment_parameters.get('save_interval')

        print("Done, Total Time:", time.time()-st)
    except KeyboardInterrupt:
        print("KeyboardInterrupt total time:", time.time()-st)

    return reward_list, learner, ep_count

if __name__ == '__main__':
    _, _, _, experiment_parameters = load_config()
    reward_list, learner, epoch_count = main(experiment_parameters)

    # save learner
    learner.save("./runs/dqn_{0:.2f}".format(epoch_count))

    print('Max score {0}. Epochs: {1:.2f}'.format(max(reward_list), epoch_count))
    import matplotlib.pyplot as plt
    plt.plot([x[1] / EPOCH_DEF for x in reward_list], [x[0] for x in reward_list])
    plt.show()
