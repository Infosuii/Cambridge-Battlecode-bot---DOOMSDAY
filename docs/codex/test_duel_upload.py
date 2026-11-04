"""Exercise upload attribution through the pipeline with an entirely offline CLI."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

PIPELINE = Path(__file__).resolve().parents[2] / "tools/replay/duel_pipeline.py"


class UploadAttributionTest(unittest.TestCase):
    def simulate(self, scenario):
        commands = []
        published = []
        sent_note = None

        def record(version, note):
            return {"version": version, "note": note, "status": "inactive",
                    "fileName": "candidate.zip"}

        def cli(argv, **kwargs):
            nonlocal sent_note
            args = argv[1:]
            if args[:2] == ["submissions", "list"]:
                if sent_note:
                    published[:] = [record(103, "teammate upload")]
                    if scenario in ("unique", "compiling"):
                        candidate = record(102, sent_note)
                        if scenario == "compiling":
                            candidate["status"] = "compiling"
                        published.append(candidate)
                    elif scenario == "duplicate":
                        published.extend([record(102, sent_note), record(104, sent_note)])
                data = {"submissions": [record(80, None), *published]}
                return subprocess.CompletedProcess(argv, 0, json.dumps(data).encode(), b"")
            if args[0] == "submit":
                sent_note = args[args.index("--note") + 1]
                commands.append(("submit", sent_note))
                return subprocess.CompletedProcess(argv, 0, b"", b"")
            action = args[1]
            version = args[args.index("--version") + 1] if "--version" in args else None
            commands.append((action, version))
            if action == "run":
                data = json.loads(plan.read_text())
                data["arms"]["candidate"] = {}
                plan.write_text(json.dumps(data), encoding="utf8")
            return subprocess.CompletedProcess(argv, 0)

        stub = types.ModuleType("ladder_duel")
        stub.required_pin_sources = lambda *_: None
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            plan = root / "plan.json"
            plan.write_text('{"arms":{"v92":{}}}', encoding="utf8")
            fake_pipeline = root / "tools/replay/duel_pipeline.py"
            argv = [str(fake_pipeline), "--plan", str(plan), "--base", "80",
                    "--cands", "candidate"]
            source = compile(PIPELINE.read_text(encoding="utf8"), str(PIPELINE), "exec")
            with patch.dict(sys.modules, {"ladder_duel": stub}), patch.object(sys, "argv", argv), \
                    patch("subprocess.run", side_effect=cli), patch("time.sleep"), \
                    contextlib.redirect_stdout(io.StringIO()):
                try:
                    exec(source, {"__name__": "__main__", "__file__": str(fake_pipeline)})
                except SystemExit as error:
                    commands.append(("abort", str(error)))
        return commands

    def test_larger_unrelated_upload_cannot_be_selected(self):
        commands = self.simulate("unique")
        self.assertEqual(commands[1:], [("run", "102"), ("report", None), ("restore", "80")])

    def test_uncertain_receipt_or_compile_aborts_and_restores(self):
        for scenario in ("missing", "duplicate", "compiling"):
            with self.subTest(scenario=scenario):
                commands = self.simulate(scenario)
                self.assertEqual([action for action, _ in commands], ["submit", "restore", "abort"])
                self.assertEqual(commands[1], ("restore", "80"))


if __name__ == "__main__":
    unittest.main()
