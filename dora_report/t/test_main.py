from dora_report.main import main

def test_main(script_runner):
    script_runner.run("dora_report/main.py", check=True, shell=True)