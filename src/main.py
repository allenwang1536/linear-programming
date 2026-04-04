import json
from argparse import ArgumentParser
from pathlib import Path
from ortools.linear_solver.python import model_builder
from lpinstance import LPInstance
from timer import Timer

if __name__ == "__main__":

    parser = ArgumentParser()
    parser.add_argument("input_file", type=str)
    args = parser.parse_args()

    input_file = args.input_file
    path = Path(input_file)
    filename = path.name

    timer = Timer()
    timer.start()

    instance = LPInstance(str(input_file))
    instance.solve()

    timer.stop()

    solve_status = "OPT" if instance.solution == model_builder.SolveStatus.OPTIMAL else str(instance.solution)

    output_dict = {"Instance": filename,
                   "Time": round(timer.getTime(), 2),
                   "Result": instance.objective_value,
                   "Solution": solve_status}

    print(json.dumps(output_dict))
