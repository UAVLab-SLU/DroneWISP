
class CFDManager:
    """
    This class is responsible for
    - managing CFD runs
    - report state
    - change openfoam case
    - setup mesh using binary mask
    """
    def __init__(self):
        self.state = "idle"

    def get_state(self):
        return self.state
