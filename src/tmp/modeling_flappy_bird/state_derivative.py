from typing import Any, NamedTuple

class StateDerivative(NamedTuple):
    delta_x_pos: Any
    delta_y_pos: Any
    delta_y_vel: Any
    delta_pressed: Any

