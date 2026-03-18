from __future__ import annotations

from typing import Optional

import numpy as np
import math
from ortools.linear_solver.python import model_builder


class LPInstance:
    # Problem parameters
    numCustomers: int  # the number of customers
    numFacilities: int  # the number of facilities
    allocCostCF: np.ndarray  # allocCostCF[c][f] is the service cost paid each time customer c is served by facility f
    demandC: np.ndarray  # demandC[c] is the demand of customer c
    openingCostF: np.ndarray  # openingCostF[f] is the opening cost of facility f
    capacityF: np.ndarray  # capacityF[f] is the capacity of facility f
    numMaxVehiclePerFacility: int  # maximum number of vehicles to use at an open facility
    truckDistLimit: float  # total driving distance limit for trucks
    truckUsageCost: float  # fixed usage cost paid if a truck is used
    distanceCF: np.ndarray  # distanceCF[c][f] is the roundtrip distance between customer c and facility f

    def __init__(self, filename: str):
        self.load_from_file(filename)
        self.solver: model_builder.Solver = model_builder.Solver('SCIP')
        self.model = model_builder.Model()
        self.solution = None
        self.objective_value = None

    def solve(self):
        """
            Supply Chain Model
        """

        # TODO: your model goes here
        model = self.model
        solver = self.solver

        numCustomers = self.numCustomers
        numFacilities = self.numFacilities

        # Variables
        openOfFacility = [ model.new_num_var(0, 1.0, f"open:{f}") for f in range(numFacilities) ]
        
        numVehiclesOfFacility = [ model.new_num_var(0, self.numMaxVehiclePerFacility, f"vehicles:{f}") for f in range(numFacilities)]
        
        assignmentOfCustomerFacility = [
                                        [ model.new_num_var(0, 1.0, f"assignment:{c}:{f}") for f in range(numFacilities)]
                                        for c in range(numCustomers)
                                        ]

        # Constraints
        # customer fulfilled requirement
        for c in range(numCustomers):
            model.add(
                sum(assignmentOfCustomerFacility[c][f] for f in range(numFacilities)) == 1.0
            )

        # facility capacity limit
        for f in range(numFacilities):
            totalDemand = sum(assignmentOfCustomerFacility[c][f] * self.demandC[c] for c in range(numCustomers))
            model.add(
                totalDemand <= self.capacityF[f] * openOfFacility[f]
            )

        # vehicle limit
        for f in range(numFacilities):
            model.add(
                numVehiclesOfFacility[f] <= self.numMaxVehiclePerFacility * openOfFacility[f]
            )

        # driving limit
        for f in range(numFacilities):
            totalDist = sum(self.distanceCF[c][f] * assignmentOfCustomerFacility[c][f] for c in range(numCustomers))
            model.add(
                totalDist <= numVehiclesOfFacility[f] * self.truckDistLimit
            )
        
        # optional: customer can only be assigned to an open facility

        # Cost Function
        model.minimize(
            # opening cost
            sum(openOfFacility[f] * self.openingCostF[f] for f in range(numFacilities))

            # customer demand fulfillment cost 
            + sum(
                assignmentOfCustomerFacility[c][f] * self.allocCostCF[c][f]
                for c in range(numCustomers)
                for f in range(numFacilities)
            )
            
            # vehicle cost
            + sum(numVehiclesOfFacility[f] * self.truckUsageCost for f in range(numFacilities))
        )

        # Solve 
        self.solution = solver.solve(model)
        if self.solution == model_builder.SolveStatus.OPTIMAL:
            self.objective_value = math.ceil(solver.objective_value)
        else:
            self.objective_value = None

    def load_from_file(self, filename: str):
        try:
            with open(filename, "r") as fl:
                numCustomers, numFacilities = [int(i) for i in fl.readline().split()]
                numMaxVehiclePerFacility = numCustomers
                print(
                    f"numCustomers: {numCustomers} numFacilities: {numFacilities} numVehicle: {numMaxVehiclePerFacility}")
                allocCostCF = np.zeros((numCustomers, numFacilities))

                allocCostraw = [float(i) for i in fl.readline().split()]
                index = 0
                for i in range(numCustomers):
                    for j in range(numFacilities):
                        allocCostCF[i, j] = allocCostraw[index]
                        index += 1

                demandC = np.array([float(i) for i in fl.readline().split()])
                openingCostF = np.array([float(i) for i in fl.readline().split()])
                capacityF = np.array([float(i) for i in fl.readline().split()])
                truckDistLimit, truckUsageCost = [float(i) for i in fl.readline().split()]

                distanceCF = np.zeros((numCustomers, numFacilities))
                distanceCFraw = [float(i) for i in fl.readline().split()]
                index = 0
                for i in range(numCustomers):
                    for j in range(numFacilities):
                        distanceCF[i, j] = distanceCFraw[index]
                        index += 1

                self.numCustomers = numCustomers
                self.numFacilities = numFacilities
                self.allocCostCF = allocCostCF
                self.demandC = demandC
                self.openingCostF = openingCostF
                self.capacityF = capacityF
                self.numMaxVehiclePerFacility = numMaxVehiclePerFacility
                self.truckDistLimit = truckDistLimit
                self.truckUsageCost = truckUsageCost
                self.distanceCF = distanceCF
        except Exception as e:
            print(f"Could not read problem instance file due to error: {e}")
            return None
