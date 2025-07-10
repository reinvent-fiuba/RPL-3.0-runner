import json
import subprocess
import sys
import tarfile
import tempfile
import os

from python_runner import PythonRunner
from c_runner import CRunner
from go_runner import GoRunner
from rust_runner import RustRunner
from runner import RunnerError, TimeOutError
from logger import get_logger

LOG = get_logger("RPL-2.0-worker-init")

custom_runners = {
    "c_std11": CRunner,
    "python_3.7": PythonRunner,  # Needed for backwards compatibility with older submissions
    "python_3.10": PythonRunner,
    "go_1.16": GoRunner,  # Just to have support for test submissions
    "go_1.19": GoRunner,
    "rust_1.88.0": RustRunner,
}

STUDENT_OUTPUT_START_DELIMITER = "start_RUN"
STUDENT_OUTPUT_END_DELIMITER = "end_RUN"
SKIPPABLE_OUTPUTS_FROM_MAKEFILE_EXECUTION = ["assignment_main.py", "custom_IO_main.pyc", "./main", "./target/release/"]

def parse_args():
    import argparse

    parser = argparse.ArgumentParser(prog="RPL Submission Runner")
    parser.add_argument("--lang", help="Language of the assignment")
    parser.add_argument(
        "--test-mode", help='Type of test ("IO" or "unit_test")', dest="mode"
    )

    return parser.parse_args()


def main():
    """
    Punto de entrada del runner, el proceso corriendo dentro de un
    contenedor docker para correr los scripts de los alumnes
    """
    args = parse_args()
    lang = args.lang
    test_mode = args.mode

    # Usamos sys.stdin.buffer para leer en binario (sys.stdin es texto).
    # Asimismo, el modo ‘r|’ (en lugar de ‘r’) indica que fileobj no es
    # seekable.

    # Todavia no descubro como evitar tener que escribir y luego leer...
    # Por ahora es un buen workarround
    with open("assignment.tar.gx", "wb") as assignment:
        assignment.write(sys.stdin.buffer.read())

    process(lang, test_mode, "assignment.tar.gx")


def process(lang, test_mode, filename, cflags=""):
    os.environ["CFLAGS"] = cflags
    if "-l" in cflags:
        os.environ["CFLAGS"] = " ".join([x if "-l" not in x else "" for x in cflags.split()])
        os.environ["LDFLAGS"] = " ".join([x if "-l" in x else "" for x in cflags.split()])

    with tempfile.TemporaryDirectory(prefix="corrector.") as tmpdir:
        LOG.info(f"Extracting tarfile submission from {filename}")
        with tarfile.open(filename) as tar:
            tar.extractall(tmpdir)

        # Escribimos los logs, stdout y stderr en archivos temporarios para despues poder devolverlo
        # y que el usuario vea que paso en su corrida
        with tempfile.TemporaryFile(
            dir=tmpdir, prefix="stdout.", mode="w+", encoding="utf-8"
        ) as my_stdout, tempfile.TemporaryFile(
            dir=tmpdir, prefix="stderr.", mode="w+", encoding="utf-8"
        ) as my_stderr:
            # Obtenemos el runner del lenguaje y modo seleccionado
            LOG.info("Running custom runner")
            test_runner = custom_runners[lang](tmpdir, test_mode, my_stdout, my_stderr)
            LOG.info("Custom runner ran succesfully")
            result = {}
            try:
                # Comenzamos la corrida
                test_runner.process()  # writes stuff to my_stdout and my_stderr
                result["tests_execution_result_status"] = "OK"
                result["tests_execution_stage"] = "COMPLETE"
                result["tests_execution_exit_message"] = "Completed all stages"
            except TimeOutError as e:
                result["tests_execution_result_status"] = "TIME_OUT"
                result["tests_execution_stage"] = e.stage
                result["tests_execution_exit_message"] = e.message
            except RunnerError as e:
                result["tests_execution_result_status"] = "ERROR"
                result["tests_execution_stage"] = e.stage
                result["tests_execution_exit_message"] = e.message
                LOG.error("HUBO ERRORES: {message} en la etapa de {stage}".format(message=e.message, stage=e.stage))
            except Exception as e:
                result["tests_execution_result_status"] = "UNKNOWN_ERROR"
                result["tests_execution_stage"] = "unknown"
                result["tests_execution_exit_message"] = str(e)
                raise e
            # Get criterion unit tests results
            if test_mode == "unit_test" and result["tests_execution_stage"] == "COMPLETE":
                result["unit_test_suite_result_summary"] = get_unit_test_results(
                    tmpdir, lang
                )
            else:
                result["unit_test_suite_result_summary"] = None  # Nice To have for debbuging
            my_stdout.seek(0)
            my_stderr.seek(0)
            result["tests_execution_stdout"] = my_stdout.read(9999)  # we can only store up to 10k chars in the column
            result["tests_execution_stderr"] = my_stderr.read(9999)
            sanitize_rust_stderr(lang, result)
            result["all_student_only_outputs_from_iotests_runs"] = parse_student_only_outputs_from_runs(result["tests_execution_stdout"])
            LOG.info(json.dumps(result, indent=4))
            return result



def parse_student_only_outputs_from_runs(log_stdout) -> list[str]:
    """
    Devuelve una lista de todas las salidas de las corridas SIN EL LOGGING. Es decir, puramente el stdout de ejecución del alumno, dividido por cada run.
    Se identifica como salida del programa a todo el stdout entre el log start_RUN y end_RUN
    """
    all_student_only_outputs_from_runs = []
    current_output_lines = ""
    for line in log_stdout.split("\n"):
        if STUDENT_OUTPUT_END_DELIMITER in line:
            if current_output_lines.endswith("\n"):
                current_output_lines = current_output_lines[:-1]
            all_student_only_outputs_from_runs.append(current_output_lines)
        elif STUDENT_OUTPUT_START_DELIMITER in line:
            current_output_lines = ""
        elif any(skippable in line for skippable in SKIPPABLE_OUTPUTS_FROM_MAKEFILE_EXECUTION):
            continue
        else:
            current_output_lines += line + "\n"

    return all_student_only_outputs_from_runs


def get_unit_test_results(tmpdir, lang):
    cat = subprocess.run(
        ["cat", "unit_test_results_output.json"],
        cwd=tmpdir,
        capture_output=True,
        text=True,
        errors="ignore",
    )
    if not cat.stdout:
        return None

    try:
        output = "".join(
            c for c in cat.stdout if ord(c) >= 32
        )  # sanitizing string as criterion output can add weird characters
        if lang == "c_std11":
            return get_custom_unit_test_results_json(output)
        return json.loads(output)
    except json.decoder.JSONDecodeError as e:
        LOG.exception(str(output).replace("\x03", ""))
        return None


# Check out util_files/salida_criterion.json to see raw format
def get_custom_unit_test_results_json(criterion_json):
    parsed_json = json.loads(str(criterion_json))
    result = {}
    if parsed_json["test_suites"] and len(parsed_json["test_suites"]) > 0:
        result["amount_passed"] = parsed_json["passed"]
        result["amount_failed"] = parsed_json["failed"]
        result["amount_errored"] = parsed_json["errored"]
        result["single_test_reports"] = parsed_json["test_suites"][0]["tests"]

    for i in range(len(result["single_test_reports"])):
        if result["single_test_reports"][i]["status"] in ["FAILED", "ERRORED"]:
            result["single_test_reports"][i]["messages"] = ";    ".join(
                result["single_test_reports"][i]["messages"]
            )
    return result

def sanitize_rust_stderr(lang, result):
    if "rust" in lang:
        cargo_exit_status_for_normal_student_failure = "make: [Makefile:27: run_unit_test] Error 100 (ignored)"
        if cargo_exit_status_for_normal_student_failure in result["tests_execution_stderr"]:
            result["tests_execution_stderr"] = result["tests_execution_stderr"].replace(
                cargo_exit_status_for_normal_student_failure, ""
            )

# Funciones para probar


def pwd(dir):
    pwd = subprocess.run(["pwd"], cwd=dir, capture_output=True, text=True)
    print(pwd.stdout, file=sys.stderr)


def ls(dir):
    ls = subprocess.run(["ls", "-l"], cwd=dir, capture_output=True, text=True)
    print(ls.stdout, file=sys.stderr)


# main()
