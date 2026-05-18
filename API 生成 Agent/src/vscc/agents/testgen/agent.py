"""Agent 4: 测试生成 —— 生成 Pytest 测试并可选执行验证."""

from pathlib import Path

from ...shared.state import PipelineState
from ..base import BaseAgent
from .generator import generate_pytest_from_spec
from .runner import run_pytest_dir


class AutoTestAgent(BaseAgent):
    name = "test_generator"

    def run(
        self,
        *,
        output_dir: Path | str = "./output/tests",
        run_tests: bool = False,
        **kwargs,
    ) -> PipelineState:
        self.state.mark_agent_start(self.name)

        try:
            spec = self.state.spec
            test_files = generate_pytest_from_spec(spec)

            if test_files:
                # 写入测试文件
                out_dir = Path(output_dir)
                out_dir.mkdir(parents=True, exist_ok=True)
                test_dir = out_dir / "tests"
                test_dir.mkdir(parents=True, exist_ok=True)

                # 确保有 __init__.py
                (test_dir / "__init__.py").touch()

                for filename, content in test_files.items():
                    (test_dir / filename).write_text(content, encoding="utf-8")

                # 写 conftest.py（如果不存在）
                conftest = test_dir / "conftest.py"
                if not conftest.exists():
                    conftest.write_text(
                        'import pytest\n\n\n@pytest.fixture\ndef app(): ...\n',
                        encoding="utf-8",
                    )

                spec.test_files = test_files

                # 执行测试验证
                if run_tests:
                    result = run_pytest_dir(test_dir)
                    spec.test_results = (
                        f"Exit: {result.exit_code}\n"
                        f"Passed: {result.passed}\n"
                        f"Failed: {result.failed}\n"
                        f"Errors: {result.errors}\n"
                        f"---\n{result.stdout[-2000:]}"
                    )
            else:
                spec.test_files = {}
                spec.test_results = "未检测到需测试的端点"

            self.state.mark_agent_done(self.name)

        except Exception as e:
            self.state.mark_agent_failed(self.name, str(e))

        return self.state
