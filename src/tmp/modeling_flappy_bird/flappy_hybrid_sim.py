from .flappy_level import FlappyLevel
from .system_parameters import SystemParameters
from .state import State
from .state_derivative import StateDerivative
from scipy import integrate

class FlappyHybridSim():
    level: FlappyLevel
    cur_params: None | SystemParameters
    max_step: float
    atol: float
    rtol: float

    def __init__(self, level:FlappyLevel):
        self.level = level
        self.cur_params = None
        self.max_step=0.01
        self.atol=1e-6
        self.rtol=1e-6
    
    

    def _check_collision(self, state:State) -> bool:
        if state[1] <= self.level.floor or state[1] >= self.level.ceiling:
            return True
        
        # we need to actually see if we're inside a death box or not
        # in a real game, we'd want to do a location based query (tell me what's nearby so I only check against nearby
        # things) but our level is so simple right now, we can just test against all the geometry
        for box in self.level.obstacles:
            # I'm like 99% sure there's a way to rephrase this hellish if statement
            # this'll get called within our solver, so state has lost it's nice property names :c
            if state[0] >= box.top_left[0] and \
                state[0] <= box.top_left[0] + box.width and \
                state[1] >= box.top_left[0] and \
                state[1] <= box.top_left[1] + box.height:
                return True
    
    
        return False
    
    

    def _flow(self, time:float, state:State) -> tuple[float, float, float, int]:
        # this little test shows that our extra flexibility-- moving things like
        # horizontal velocity to a passed in parameter-- is not free: we have an extra check
        # to perform now
        if not self.cur_params:
            raise RuntimeError("Unable to get run parameters!")
    
    
        if state[3] == 0:
            return StateDerivative(
                delta_x_pos=self.cur_params.horizontal_velocity,
                delta_y_pos=state[2],
                delta_y_vel=self.cur_params.gravity_acceleration,
                delta_pressed=0
            )
        elif state[3] == 1: #pressed
            return StateDerivative(
                delta_x_pos=self.cur_params.horizontal_velocity, 
                delta_y_pos=self.cur_params.pressed_velocity,
                delta_y_vel=0,
                delta_pressed=0 
            )
        else:
            raise RuntimeError(f"Invalid state! {state}, pressed != 0 or 1")
    
    

    def _flow_check(self, time:float, state:State) -> int:
        return 0
    
    

    def _jump(self, time:float, state:State) -> tuple[float, float, float, int]:
        if not self.cur_params:
            raise RuntimeError("Unable to get runtime parameters!")
    
    
        new_pressed = abs(state[3] - 1)
        if new_pressed == 1:
            return State(
                x_pos=state[0],
                y_pos=state[1],
                y_vel=self.cur_params.pressed_velocity,
                pressed=new_pressed
            )
        else:
            return State(
                x_pos=state[0],
                y_pos=state[1],
                y_vel=state[2],
                pressed=new_pressed
            )
    
    

    def _jump_check(self, time:float, state:State) -> int:
        if self._check_collision(state):
            return 0
    
    
        if time >= 0.5 and \
            time < 0.6 and \
                state[3] != 1:
            return 0
        elif time >= 0.6 and \
            state[3] != 0:
            return 0
        else:
            return 1
    
    

    def solve_system(self, params:SystemParameters, start_state:State) -> list[Any]:
        solution:list[Any] = [] # gradual typing is neat!
        self.cur_params = params
        cur_time = params.start_time
        number_of_jumps = 0
        state = start_state
    
    
        if(self._flow_check(cur_time, state) == 0):
            ode_sol = integrate.solve_ivp(
                self._flow,
                (cur_time, params.end_time),
                state,
                events=[self._jump_check],
                max_step=self.max_step,
                atol=self.atol,
                rtol=self.rtol
            )
            if ode_sol.status == -1:
                print(f"Solver failed with message: {ode_sol.message}")
                return solution
            for time, state in zip(ode_sol.t, ode_sol.y.T):
                solution.append((time, state))
    
    
            cur_time, state = solution[-1]
         
            if self._check_collision(state):
                self.cur_params = None
                return solution
        
            if (self._jump_check(cur_time, state) == 0):
                state = self._jump(cur_time, state)
                number_of_jumps += 1
        self.cur_params = None 
        return solution
    
    

