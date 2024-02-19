import torch.nn as nn

# Define the DNN
class DnnGenNet(nn.Module):
    def __init__(self):
        super(DnnGenNet, self).__init__()
        self.conv1 = nn.Conv3d(1, 32, kernel_size=3, stride=1, padding=1)
        self.fc1 = nn.Linear(32 * 50 * 50 * 25, 128)
        self.fc2 = nn.Linear(128, 50 * 50 * 25 * 3)

    def forward(self, x):
        x = self.conv1(x)
        x = x.view(-1, 32 * 50 * 50 * 25)  # Flatten layer
        x = self.fc1(x)
        x = self.fc2(x)
        return x