"""Deep Performance, Algorithmic Complexity, and GPU/Hardware Acceleration Engine.

Analyzes Python ASTs for:
- Time Complexity (O(1), O(N), O(N^2), O(N^3), O(2^N) exponential recursion)
- Space Complexity (generator streaming vs in-memory list allocations)
- Quadratic anti-patterns (linear search in loops, repeated string concatenation)
- GPU & Deep Learning bottlenecks (PyTorch CUDA transfers in loops, GPU sync barriers, missing inference_mode)
"""
from __future__ import annotations

import ast
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


@dataclass
class ComplexityHotspot:
    function_name: str
    file_path: str
    line_start: int
    line_end: int
    cyclomatic_complexity: int
    loop_depth: int
    estimated_time_complexity: str
    estimated_space_complexity: str
    category: str  # "algorithmic", "time_complexity", "space_complexity", "gpu_optimization"
    severity: str  # "high", "medium", "low"
    issue_description: str
    optimization_recommendation: str
    before_code: str = ""
    after_code: str = ""
    hardware_impact: str = ""


@dataclass
class ProjectOptimizationSummary:
    total_files_analyzed: int = 0
    total_functions_analyzed: int = 0
    average_cyclomatic_complexity: float = 1.0
    maintainability_index: float = 100.0
    time_complexity_distribution: Dict[str, int] = field(default_factory=lambda: {
        "O(1)": 0, "O(N)": 0, "O(N^2)": 0, "O(N^3+)": 0, "O(2^N)": 0
    })
    gpu_optimization_count: int = 0
    hotspots: List[ComplexityHotspot] = field(default_factory=list)


class ASTComplexityVisitor(ast.NodeVisitor):
    """Deep AST inspector for time complexity, space complexity, and GPU patterns."""

    def __init__(self, file_path: str, source_code: str, relative_path: str):
        self.file_path = file_path
        self.relative_path = relative_path
        self.source_code = source_code
        self.source_lines = source_code.splitlines()
        self.hotspots: List[ComplexityHotspot] = []
        self.functions_analyzed = 0
        self.total_cc = 0
        self.time_dist: Dict[str, int] = {"O(1)": 0, "O(N)": 0, "O(N^2)": 0, "O(N^3+)": 0, "O(2^N)": 0}

    def _get_snippet(self, start_line: int, end_line: int) -> str:
        s = max(0, start_line - 1)
        e = min(len(self.source_lines), end_line)
        return "\n".join(self.source_lines[s:e])

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._analyze_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._analyze_function(node)
        self.generic_visit(node)

    def _analyze_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        self.functions_analyzed += 1
        fn_name = node.name
        start_line = node.lineno
        end_line = getattr(node, "end_lineno", start_line + 5)
        snippet = self._get_snippet(start_line, end_line)

        # 1. Cyclomatic Complexity
        cc = self._calculate_cyclomatic(node)
        self.total_cc += cc

        # 2. Loop Nesting Depth
        max_loop_depth = self._max_loop_depth(node)

        # 3. Recursive Calls Detection
        rec_calls = self._count_recursive_calls(node, fn_name)
        has_lru_cache = any(
            isinstance(d, ast.Name) and "cache" in d.id.lower()
            or isinstance(d, ast.Call) and isinstance(d.func, ast.Name) and "cache" in d.func.id.lower()
            for d in node.decorator_list
        )

        # 4. Big-O Time Complexity Estimation
        if rec_calls >= 2 and not has_lru_cache:
            time_comp = "O(2^N)"
            space_comp = "O(N) [call stack]"
            self.time_dist["O(2^N)"] += 1
            self.hotspots.append(ComplexityHotspot(
                function_name=f"{fn_name}()",
                file_path=self.relative_path,
                line_start=start_line,
                line_end=end_line,
                cyclomatic_complexity=cc,
                loop_depth=max_loop_depth,
                estimated_time_complexity=time_comp,
                estimated_space_complexity=space_comp,
                category="time_complexity",
                severity="high",
                issue_description=f"Exponential recursion detected in '{fn_name}'. Function branches recursively without memoization.",
                optimization_recommendation="Add '@functools.lru_cache(maxsize=None)' decorator or refactor to bottom-up DP to drop from O(2^N) to O(N).",
                before_code=snippet[:400],
                after_code="@functools.lru_cache(maxsize=1024)\n" + snippet[:350],
                hardware_impact="Reduces execution time by millions of operations on deep inputs; prevents call-stack overflow.",
            ))
        elif max_loop_depth >= 3:
            time_comp = "O(N^3+)"
            space_comp = "O(1)"
            self.time_dist["O(N^3+)"] += 1
            self.hotspots.append(ComplexityHotspot(
                function_name=f"{fn_name}()",
                file_path=self.relative_path,
                line_start=start_line,
                line_end=end_line,
                cyclomatic_complexity=cc,
                loop_depth=max_loop_depth,
                estimated_time_complexity=time_comp,
                estimated_space_complexity=space_comp,
                category="time_complexity",
                severity="high",
                issue_description=f"Triple-nested loop structure (depth={max_loop_depth}) detected in '{fn_name}'. Risk of polynomial runtime stall on large data.",
                optimization_recommendation="Extract inner loop computations or use matrix tensor broadcasting (numpy/torch.matmul) to eliminate iteration layers.",
                before_code=snippet[:400],
                after_code="# Use vectorized matrix multiplication:\nresult = np.einsum('ijk,ikl->ijl', A, B)",
                hardware_impact="High CPU utilization bottleneck; prime candidate for GPU SIMD/CUDA tensor core acceleration.",
            ))
        elif max_loop_depth == 2:
            time_comp = "O(N^2)"
            space_comp = "O(1)"
            self.time_dist["O(N^2)"] += 1
            self.hotspots.append(ComplexityHotspot(
                function_name=f"{fn_name}()",
                file_path=self.relative_path,
                line_start=start_line,
                line_end=end_line,
                cyclomatic_complexity=cc,
                loop_depth=2,
                estimated_time_complexity=time_comp,
                estimated_space_complexity=space_comp,
                category="time_complexity",
                severity="medium",
                issue_description=f"Quadratic Time Complexity O(N^2) in '{fn_name}' via nested loops.",
                optimization_recommendation="Evaluate if index lookup or hash map (dict/set) can index the inner collection in O(1), lowering overall time to O(N).",
                before_code=snippet[:400],
                after_code="# Pre-index inner collection into hash map:\nlookup = {item.id: item for item in items}\nfor parent in parents:\n    target = lookup.get(parent.id)",
                hardware_impact="Quadratic slowdown as dataset scales (10x input size = 100x slower runtime).",
            ))
        elif max_loop_depth == 1:
            time_comp = "O(N)"
            space_comp = "O(1)"
            self.time_dist["O(N)"] += 1
        else:
            time_comp = "O(1)"
            space_comp = "O(1)"
            self.time_dist["O(1)"] += 1

        # 5. Anti-Pattern: Linear Search Inside Loop (O(N*M) -> O(N+M))
        self._check_linear_search_in_loop(node, fn_name, start_line)

        # 6. Anti-Pattern: String Concatenation inside Loop (O(N^2) string allocation)
        self._check_string_concat_in_loop(node, fn_name, start_line)

        # 7. Space Complexity: List Comprehension in Aggregate Functions (O(N) memory allocation)
        self._check_unnecessary_list_materialization(node, fn_name, start_line)

        # 8. GPU & Deep Learning Bottlenecks (PyTorch / CUDA / MPS)
        self._check_gpu_cuda_bottlenecks(node, fn_name, start_line)

    def _calculate_cyclomatic(self, node: ast.AST) -> int:
        cc = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.ExceptHandler, ast.With, ast.Assert)):
                cc += 1
            elif isinstance(child, ast.BoolOp):
                cc += len(child.values) - 1
            elif isinstance(child, (ast.IfExp,)):
                cc += 1
        return cc

    def _max_loop_depth(self, node: ast.AST, current_depth: int = 0) -> int:
        max_d = current_depth
        for child in getattr(node, "body", []):
            if isinstance(child, (ast.For, ast.AsyncFor, ast.While)):
                d = self._max_loop_depth(child, current_depth + 1)
                max_d = max(max_d, d)
            elif hasattr(child, "body"):
                d = self._max_loop_depth(child, current_depth)
                max_d = max(max_d, d)
        return max_d

    def _count_recursive_calls(self, node: ast.AST, fn_name: str) -> int:
        count = 0
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name) and child.func.id == fn_name:
                    count += 1
                elif isinstance(child.func, ast.Attribute) and child.func.attr == fn_name:
                    count += 1
        return count

    def _check_linear_search_in_loop(self, node: ast.AST, fn_name: str, start_line: int) -> None:
        """Detect 'if x in my_list' inside a loop."""
        for child in ast.walk(node):
            if isinstance(child, (ast.For, ast.While)):
                for sub in ast.walk(child):
                    if isinstance(sub, ast.Compare):
                        for op in sub.ops:
                            if isinstance(op, (ast.In, ast.NotIn)):
                                line = getattr(sub, "lineno", start_line)
                                snippet = self._get_snippet(line, line + 1)
                                self.hotspots.append(ComplexityHotspot(
                                    function_name=f"{fn_name}()",
                                    file_path=self.relative_path,
                                    line_start=line,
                                    line_end=line,
                                    cyclomatic_complexity=3,
                                    loop_depth=1,
                                    estimated_time_complexity="O(N * M) Quadratic Search",
                                    estimated_space_complexity="O(1)",
                                    category="time_complexity",
                                    severity="high",
                                    issue_description=f"Membership test ('in') inside loop in '{fn_name}'. If target is a list, this causes an O(N*M) quadratic scan.",
                                    optimization_recommendation="Convert target collection to a set() prior to loop to reduce lookup from O(M) to O(1) amortized.",
                                    before_code=snippet,
                                    after_code="# Pre-convert to set for O(1) hash lookup:\nallowed_set = set(target_collection)\nif item in allowed_set:",
                                    hardware_impact="Drastically drops CPU instruction count on large datasets from millions of iterations to hash lookups.",
                                ))
                                return

    def _check_string_concat_in_loop(self, node: ast.AST, fn_name: str, start_line: int) -> None:
        """Detect 'text += chunk' inside a loop."""
        for child in ast.walk(node):
            if isinstance(child, (ast.For, ast.While)):
                for sub in ast.walk(child):
                    if isinstance(sub, ast.AugAssign) and isinstance(sub.op, ast.Add):
                        if isinstance(sub.target, ast.Name):
                            var_name = sub.target.id
                            # Heuristic: names indicating string
                            if any(k in var_name.lower() for k in ["str", "text", "buffer", "msg", "data", "html"]):
                                line = getattr(sub, "lineno", start_line)
                                snippet = self._get_snippet(line, line + 1)
                                self.hotspots.append(ComplexityHotspot(
                                    function_name=f"{fn_name}()",
                                    file_path=self.relative_path,
                                    line_start=line,
                                    line_end=line,
                                    cyclomatic_complexity=2,
                                    loop_depth=1,
                                    estimated_time_complexity="O(N^2) String Copy",
                                    estimated_space_complexity="O(N^2) Reallocations",
                                    category="space_complexity",
                                    severity="medium",
                                    issue_description=f"Repeated string concatenation ('{var_name} += ...') in loop creates immutable string copies on every iteration.",
                                    optimization_recommendation="Append chunks to a list and join at the end: ''.join(chunks). Drops runtime from O(N^2) to O(N).",
                                    before_code=snippet,
                                    after_code=f"chunks = []\nchunks.append(new_content)\n{var_name} = ''.join(chunks)",
                                    hardware_impact="Eliminates memory fragmentation and excessive garbage collection pauses.",
                                ))
                                return

    def _check_unnecessary_list_materialization(self, node: ast.AST, fn_name: str, start_line: int) -> None:
        """Detect sum([x for x in ...]) instead of sum(x for x in ...)."""
        for child in ast.walk(node):
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                if child.func.id in {"sum", "any", "all", "min", "max"}:
                    if child.args and isinstance(child.args[0], ast.ListComp):
                        line = getattr(child, "lineno", start_line)
                        snippet = self._get_snippet(line, line + 1)
                        self.hotspots.append(ComplexityHotspot(
                            function_name=f"{fn_name}()",
                            file_path=self.relative_path,
                            line_start=line,
                            line_end=line,
                            cyclomatic_complexity=2,
                            loop_depth=1,
                            estimated_time_complexity="O(N)",
                            estimated_space_complexity="O(N) Heap Allocation -> O(1) Generator",
                            category="space_complexity",
                            severity="low",
                            issue_description=f"Unnecessary full list allocation in '{child.func.id}([...])' in function '{fn_name}'.",
                            optimization_recommendation=f"Pass a generator expression '{child.func.id}(...)' without brackets. Avoids allocating the entire list in RAM.",
                            before_code=snippet,
                            after_code=snippet.replace("[", "").replace("]", ""),
                            hardware_impact="Reduces peak RAM usage from O(N) to O(1) constant streaming memory.",
                        ))

    def _check_gpu_cuda_bottlenecks(self, node: ast.AST, fn_name: str, start_line: int) -> None:
        """Detect GPU & Deep Learning bottlenecks (CUDA host-to-device transfers in loop, missing inference_mode, etc.)."""
        # 1. Device transfer in loop
        for child in ast.walk(node):
            if isinstance(child, (ast.For, ast.While)):
                for sub in ast.walk(child):
                    if isinstance(sub, ast.Call):
                        # .to("cuda") or .cuda()
                        is_cuda_transfer = False
                        if isinstance(sub.func, ast.Attribute):
                            if sub.func.attr == "cuda":
                                is_cuda_transfer = True
                            elif sub.func.attr == "to":
                                for a in sub.args:
                                    if isinstance(a, ast.Constant) and any(d in str(a.value).lower() for d in ["cuda", "mps", "gpu"]):
                                        is_cuda_transfer = True
                        if is_cuda_transfer:
                            line = getattr(sub, "lineno", start_line)
                            snippet = self._get_snippet(line, line + 1)
                            self.hotspots.append(ComplexityHotspot(
                                function_name=f"{fn_name}()",
                                file_path=self.relative_path,
                                line_start=line,
                                line_end=line,
                                cyclomatic_complexity=2,
                                loop_depth=1,
                                estimated_time_complexity="PCI-e Bottlenecked",
                                estimated_space_complexity="GPU VRAM Thrashing",
                                category="gpu_optimization",
                                severity="high",
                                issue_description=f"Host-to-Device tensor transfer (.to(cuda)) executed inside iteration loop in '{fn_name}'.",
                                optimization_recommendation="Move batch to GPU using non_blocking=True with pin_memory=True in DataLoader, or transfer dataset prior to loop.",
                                before_code=snippet,
                                after_code="# In PyTorch DataLoader set: pin_memory=True\n# Then transfer non-blocking:\nbatch = batch.to(device, non_blocking=True)",
                                hardware_impact="Prevents PCIe bus saturation; allows CUDA stream compute overlap, boosting GPU compute utilization by up to 3x.",
                            ))
                            break

                    # 2. CPU Synchronization barrier (.item() / .numpy() in loop)
                    if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute):
                        if sub.func.attr in {"item", "numpy", "tolist"}:
                            line = getattr(sub, "lineno", start_line)
                            snippet = self._get_snippet(line, line + 1)
                            self.hotspots.append(ComplexityHotspot(
                                function_name=f"{fn_name}()",
                                file_path=self.relative_path,
                                line_start=line,
                                line_end=line,
                                cyclomatic_complexity=2,
                                loop_depth=1,
                                estimated_time_complexity="GPU Pipeline Stall",
                                estimated_space_complexity="O(1)",
                                category="gpu_optimization",
                                severity="high",
                                issue_description=f"GPU Synchronization Barrier: '{sub.func.attr}()' called inside iteration loop in '{fn_name}'. Forces GPU to pause and flush command queue to return host scalar.",
                                optimization_recommendation=f"Accumulate loss/metrics on GPU tensor (e.g. running_loss += loss.detach()) and call .{sub.func.attr}() only at end of epoch.",
                                before_code=snippet,
                                after_code="total_loss += loss.detach()  # Keep on GPU\n# At epoch end:\navg_loss = total_loss.item() / num_batches",
                                hardware_impact="Eliminates CPU-GPU lockstep wait; restores async GPU kernel execution pipeline.",
                            ))
                            break

        # 3. Missing torch.inference_mode() in prediction/eval function
        if any(term in fn_name.lower() for term in ["predict", "evaluate", "infer", "forward", "test_step"]):
            has_no_grad = any(
                "no_grad" in self.source_code[max(0, start_line-200):start_line+400]
                or "inference_mode" in self.source_code[max(0, start_line-200):start_line+400]
                for _ in [1]
            )
            has_model_eval = any("model.eval()" in self.source_code or "model(" in snippet for _ in [1])
            if has_model_eval and not has_no_grad:
                self.hotspots.append(ComplexityHotspot(
                    function_name=f"{fn_name}()",
                    file_path=self.relative_path,
                    line_start=start_line,
                    line_end=start_line + 2,
                    cyclomatic_complexity=1,
                    loop_depth=0,
                    estimated_time_complexity="O(N) Forward Pass",
                    estimated_space_complexity="Excess VRAM (Autograd Overhead)",
                    category="gpu_optimization",
                    severity="medium",
                    issue_description=f"Model evaluation in '{fn_name}' without 'torch.inference_mode()' or 'torch.no_grad()'. Computation graph autograd overhead stored in GPU VRAM.",
                    optimization_recommendation="Wrap evaluation block in 'with torch.inference_mode():'. Disables view tracking and version counters, reducing VRAM by 50%+.",
                    before_code=f"def {fn_name}(...):\n    model.eval()\n    outputs = model(inputs)",
                    after_code=f"def {fn_name}(...):\n    model.eval()\n    with torch.inference_mode():\n        outputs = model(inputs)",
                    hardware_impact="Reduces GPU VRAM consumption by up to 60% and accelerates inference forward pass by 15-25%.",
                ))


class PerformanceEngine:
    """Project-wide analyzer for code complexity, algorithmic efficiency, and GPU acceleration."""

    @classmethod
    def analyze_project(cls, project_path: Path) -> ProjectOptimizationSummary:
        summary = ProjectOptimizationSummary()
        if not project_path.exists():
            return summary

        py_files = [
            f for f in project_path.rglob("*.py")
            if not any(p in {"venv", ".venv", "__pycache__", ".git", "node_modules", "dist", "build"} for p in f.parts)
        ]
        summary.total_files_analyzed = len(py_files)

        total_cc_sum = 0
        total_functions_count = 0
        total_loc = 0

        for fpath in py_files:
            try:
                content = fpath.read_text(encoding="utf-8", errors="replace")
                total_loc += len(content.splitlines())
                rel_path = str(fpath.relative_to(project_path))
                tree = ast.parse(content)
                visitor = ASTComplexityVisitor(str(fpath), content, rel_path)
                visitor.visit(tree)

                summary.hotspots.extend(visitor.hotspots)
                total_functions_count += visitor.functions_analyzed
                total_cc_sum += visitor.total_cc
                for k, v in visitor.time_dist.items():
                    summary.time_complexity_distribution[k] += v

            except Exception:
                continue

        summary.total_functions_analyzed = total_functions_count
        if total_functions_count > 0:
            summary.average_cyclomatic_complexity = round(total_cc_sum / total_functions_count, 1)
        else:
            summary.average_cyclomatic_complexity = 1.0

        # Calculate Maintainability Index
        # MI = max(0, (171 - 5.2 * ln(V) - 0.23 * CC - 16.2 * ln(LOC)) * 100 / 171)
        loc = max(1, total_loc)
        cc = max(1, summary.average_cyclomatic_complexity)
        try:
            raw_mi = (171 - 5.2 * math.log(max(10, loc * 5)) - 0.23 * cc - 16.2 * math.log(loc)) * 100 / 171
            summary.maintainability_index = max(10.0, min(100.0, round(raw_mi, 1)))
        except Exception:
            summary.maintainability_index = 85.0

        summary.gpu_optimization_count = sum(1 for h in summary.hotspots if h.category == "gpu_optimization")

        return summary
