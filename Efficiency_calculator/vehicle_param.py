
car_mass = 46.8
driver_mass = 50.0
SCx = 0.04
crr = 0.008


class Vehicle:
    def __init__(self):
        self.car_mass = car_mass
        self.driver_mass = driver_mass
        self.SCx = SCx
        self.crr = crr

    @property
    def mass(self) -> float:
        return self.car_mass + self.driver_mass

    @property
    def mass_e(self) -> float:
        # Automatically updates when car_mass changes
        return 1.04 * self.car_mass + self.driver_mass
