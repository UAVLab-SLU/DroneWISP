import numpy as np
import pandas
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.autograd as autograd
import torch.optim as optim
import time

# input: 3D array 100*100*100 mesh + 1 scalar wind speed
# output: 3D array 100*100*100 wind speed on one direction
# loss: MSE + PDE loss
# Domain bounds
lb = np.array([-1, -1])  # lower bound
ub = np.array([1, 1])  # upper bound

a_1 = 1
a_2 = 1
k = 1

# Set default dtype to float32
torch.set_default_dtype(torch.float)

# PyTorch random number generator
torch.manual_seed(1234)

# Random number generators in other libraries
np.random.seed(1234)

# Device configuration
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

print(device)

if device == 'cuda': print(torch.cuda.get_device_name())


class GeneratorPINN(nn.Module):
    def __init__(self, layers):
        super(GeneratorPINN, self).__init__()
        self.input_size = 50 * 50 * 25
        self.output_size = 50 * 50 * 25

        self.activation = nn.ReLU()
        self.loss_fn = nn.MSELoss(reduction='mean')

        self.linears = nn.ModuleList([nn.Linear(layers[i], layers[i + 1]) for i in range(len(layers) - 1)])

    def forward(self, x):
        # x: 3D array 100*100*100 mesh + 1 scalar wind speed
        if torch.is_tensor(x) != True:
            x = torch.from_numpy(x)

        u_b = torch.from_numpy(ub).float().to(device)
        l_b = torch.from_numpy(lb).float().to(device)

        print(x.shape) # [1001, 1001, 51]
        print(l_b.shape) # [2]
        print(u_b.shape) # [2]

        # preprocessing input
        x = (x - l_b) / (u_b - l_b)  # normalize input


        # convert to float
        a = x.float()

        for i in range(len(layers) - 2):
            z = self.linears[i](a)

            a = self.activation(z)

        a = self.linears[-1](a)

        return a


    def loss_BC(self, x, y):
        loss_u = self.loss_fn(self.forward(x), y)

        return loss_u

    def loss_PDE(self, x_to_train_f):
        x_1_f = x_to_train_f[:, [0]]
        x_2_f = x_to_train_f[:, [1]]

        g = x_to_train_f.clone()

        g.requires_grad = True

        u = self.forward(g)

        u_x = \
            autograd.grad(u, g, torch.ones([x_to_train_f.shape[0], 1]).to(device), retain_graph=True,
                          create_graph=True)[0]

        u_xx = autograd.grad(u_x, g, torch.ones(x_to_train_f.shape).to(device), create_graph=True)[0]

        u_xx_1 = u_xx[:, [0]]

        u_xx_2 = u_xx[:, [1]]

        q = (-(a_1 * np.pi) ** 2 - (a_2 * np.pi) ** 2 + k ** 2) * torch.sin(a_1 * np.pi * x_1_f) * torch.sin(
            a_2 * np.pi * x_2_f)

        f = u_xx_1 + u_xx_2 + k ** 2 * u - q

        loss_f = self.loss_function(f, f_hat)

        return loss_f

    def loss(self, x, y, x_to_train_f):
        loss_u = self.loss_BC(x, y)
        loss_f = self.loss_PDE(x_to_train_f)

        loss_val = loss_u + loss_f

        return loss_val

    def closure(self):

        optimizer.zero_grad()

        loss_val = self.loss(x, y, x_to_train_f)

        error_vec, _ = PINN.test()

        print(loss, error_vec)

        loss_val.backward()

        return loss_val

    def test(self):

        u_pred = self.forward(x)

        error_vec = torch.linalg.norm((u_pred - y), 2) / torch.linalg.norm(y, 2)

        u_pred = np.reshape(u_pred.cpu().detach().numpy(), (256, 256), order='F')

        return error_vec, u_pred


if __name__ == "__main__":
    N_u = 400  # Total number of data points for 'u'
    N_f = 10000  # Total number of collocation points

    # Training data
    train_input = np.load('../csv/train/500/chicago_binary_array.npy')
    train_true = pandas.read_csv('../csv/train/500/10ms_49.csv').to_numpy()
    'Convert to tensor and send to GPU'

    x = torch.from_numpy(train_input).float().to(device)
    y = torch.from_numpy(train_true).float().to(device)

    print(x.shape) # 50*50*25
    print(y.shape) # 50*50*25



    x_to_train_f = torch.from_numpy(train_input).float().to(device)

    f_hat = torch.zeros([N_f, 1]).to(device)

    layers = np.array([50 * 50 * 25, 100, 100, 100, 100, 100, 100, 100, 100, 100, 50 * 50 * 25])

    PINN = GeneratorPINN(layers)

    PINN.to(device)

    'Neural Network Summary'

    print(PINN)

    params = list(PINN.parameters())

    '''Optimization'''

    'L-BFGS Optimizer'

    # optimizer = torch.optim.LBFGS(PINN.parameters(), lr=0.1,
    #                               max_iter = 1000,
    #                               max_eval = None,
    #                               tolerance_grad = 1e-06,
    #                               tolerance_change = 1e-09,
    #                               history_size = 100,
    #                               line_search_fn = 'strong_wolfe')

    # start_time = time.time()

    # optimizer.zero_grad()     # zeroes the gradient buffers of all parameters

    # optimizer.step(PINN.closure)

    'Adam Optimizer'

    optimizer = optim.Adam(PINN.parameters(), lr=0.001, betas=(0.9, 0.999), eps=1e-08, weight_decay=0, amsgrad=False)

    max_iter = 1000

    start_time = time.time()

    for i in range(max_iter):

        loss = PINN.loss(x, y, x_to_train_f)

        optimizer.zero_grad()  # zeroes the gradient buffers of all parameters

        loss.backward()  # backprop

        optimizer.step()

        if i % (max_iter / 10) == 0:
            error_vec, _ = PINN.test()

            print(loss, error_vec)

    elapsed = time.time() - start_time
    print('Training time: %.2f' % (elapsed))

    ''' Model Accuracy '''
    error_vec, u_pred = PINN.test()

    print('Test Error: %.5f' % (error_vec))

    ''' Solution Plot '''
    # solutionplot(u_pred,X_u_train,u_train)
