from ortools.sat.python import cp_model

# Define a class to print intermediate solutions
class VarArraySolutionPrinter(cp_model.CpSolverSolutionCallback):
    """Print intermediate solutions."""

    def __init__(self, variables: list[cp_model.IntVar]):
        # Initialize the base class
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.__variables = variables
        self.__solution_count = 0

    def on_solution_callback(self) -> None:
        # Increment the solution count
        self.__solution_count += 1
        # Print the current solution
        for v in self.__variables:
            print(f"{v}={self.value(v)}", end=" ")
        print()

    @property
    def solution_count(self) -> int:
        # Return the number of solutions found
        return self.__solution_count

# Function to search for all solutions in a sample SAT problem
def search_for_all_solutions_sample_sat():
    """Showcases calling the solver to search for all solutions."""
    # Creates the model
    model = cp_model.CpModel()

    # Creates the variables with domain [0, num_vals - 1]
    num_vals = 3
    x = model.new_int_var(0, num_vals - 1, "x")
    y = model.new_int_var(0, num_vals - 1, "y")
    z = model.new_int_var(0, num_vals - 1, "z")

    # Create the constraints
    model.add(x != y)

    # Create a solver and solve
    solver = cp_model.CpSolver()
    solution_printer = VarArraySolutionPrinter([x, y, z])
    # Enumerate all solutions
    solver.parameters.enumerate_all_solutions = True
    # Solve the model and print solutions
    status = solver.solve(model, solution_printer)

    # Print the status and number of solutions found
    print(f"Status = {solver.status_name(status)}")
    print(f"Number of solutions found: {solution_printer.solution_count}")

# Call the function to search for all solutions
search_for_all_solutions_sample_sat()