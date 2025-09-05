"""
Simple Parameter Sweeper for ComfyUI Automation

A lightweight utility for testing methods with different parameter combinations.
"""

from logging_utils import logger
import itertools
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional, Union, Type


@dataclass
class SweepResult:
    """Result of a parameter sweep test."""

    object_name: str
    method_name: str
    parameters: Dict[str, Any]
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0

    def __str__(self) -> str:
        status = "✓" if self.success else "✗"
        return f"{status} {self.object_name}.{self.method_name}({self.parameters}) -> {self.result if self.success else self.error}"


class ComfyUIParameterSweeper:
    """
    Simple parameter sweeper for testing methods with different parameter combinations.

    Usage:
        sweeper = ParameterSweeper()
        results = sweeper.sweep(my_object, "my_method", [
            {"param1": value1, "param2": value2},
            {"param1": value3, "param2": value4}
        ])
    """

    def sweep(
        self,
        obj: Union[Type, object],
        method_name: str,
        parameter_sets: List[Dict[str, Any]],
    ) -> List[SweepResult]:
        """
        Test a method with multiple parameter combinations.

        Args:
            obj: Class or instance to test
            method_name: Name of method to call
            parameter_sets: List of parameter dictionaries to test

        Returns:
            List of SweepResult objects
        """
        # Create instance if needed
        if isinstance(obj, type):
            try:
                instance = obj()
                obj_name = obj.__name__
            except (TypeError, ValueError, AttributeError) as e:
                logger.error(f"Failed to create instance of {obj.__name__}: {e}")
                return []
        else:
            instance = obj
            obj_name = obj.__class__.__name__

        # Get method
        method = getattr(instance, method_name, None)
        if not method or not callable(method):
            logger.error(
                f"Method '{method_name}' not found or not callable in {obj_name}"
            )
            return []

        # Execute parameter combinations
        results = []
        for params in parameter_sets:
            start_time = time.time()
            result = SweepResult(
                object_name=obj_name,
                method_name=method_name,
                parameters=params,
                success=False,
            )

            try:
                result.result = method(**params)
                result.success = True
                logger.info(f"✓ {obj_name}.{method_name}({params})")
            except (TypeError, ValueError, AttributeError) as e:
                result.error = str(e)
                logger.error(f"✗ {obj_name}.{method_name}({params}) -> {e}")

            result.execution_time = time.time() - start_time
            results.append(result)

        return results

    def grid_sweep(
        self, obj: Union[Type, object], method_name: str, **parameter_ranges
    ) -> List[SweepResult]:
        """
        Test a method with all combinations of parameter ranges.

        Args:
            obj: Class or instance to test
            method_name: Name of method to call
            **parameter_ranges: Parameter names with lists of values

        Returns:
            List of SweepResult objects
        """
        # Generate all parameter combinations
        param_names = list(parameter_ranges.keys())
        param_values = list(parameter_ranges.values())
        parameter_sets = [
            dict(zip(param_names, combination))
            for combination in itertools.product(*param_values)
        ]

        return self.sweep(obj, method_name, parameter_sets)

    def stream_sweep(
        self,
        obj: Union[Type, object],
        method_name: str,
        parameter_sets: List[Dict[str, Any]],
    ) -> Iterator[SweepResult]:
        """
        Stream results as they are generated (memory efficient for large sweeps).
        """
        for result in self.sweep(obj, method_name, parameter_sets):
            yield result

    def get_summary(self, results: List[SweepResult]) -> Dict[str, Any]:
        """Get summary statistics for sweep results."""
        if not results:
            return {"total": 0, "successful": 0, "failed": 0, "success_rate": 0.0}

        successful = sum(1 for r in results if r.success)
        total = len(results)

        return {
            "total": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": successful / total if total > 0 else 0.0,
            "avg_execution_time": sum(r.execution_time for r in results) / total,
            "total_execution_time": sum(r.execution_time for r in results),
        }
