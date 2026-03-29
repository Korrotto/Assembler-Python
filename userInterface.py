from os import name
from subprocess import run
from jsonschema import ValidationError
import assembler

TITLE = r"""
 █████╗ ███████╗███████╗███████╗███╗   ███╗██████╗ ██╗     ███████╗██████╗ 
██╔══██╗██╔════╝██╔════╝██╔════╝████╗ ████║██╔══██╗██║     ██╔════╝██╔══██╗
███████║███████╗███████╗█████╗  ██╔████╔██║██████╔╝██║     █████╗  ██████╔╝
██╔══██║╚════██║╚════██║██╔══╝  ██║╚██╔╝██║██╔══██╗██║     ██╔══╝  ██╔══██╗
██║  ██║███████║███████║███████╗██║ ╚═╝ ██║██████╔╝███████╗███████╗██║  ██║
╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝╚═╝     ╚═╝╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═╝
"""

class InvalidArchitectureError(Exception):
    pass


def clearConsole() -> None:
    command = "cls" if name == "nt" else "clear"
    run(command, shell=True, check=False)

def getProgram() -> str:
    print(
        "\nDo not include the file extension or the program will not work.\n"
        "1. No spaces in the file name.\n"
        "2. Be careful not to use the same name twice."
    )

    return input("\n>>> Program name: ").strip()

def showTitle() -> None:
    print(TITLE)

def pause() -> None:
    input("Press Enter to continue...")

def getChoice() -> str:
    while True:
        choice = input(
            "1. Assemble program\n"
            "2. Create annotated listing\n"
            "3. Quit\n"
            "Choice: "
        ).strip()

        if choice in {"1", "2", "3"}:
            return choice

        print("Select one of the 3 options.")

def getArchitecture() -> str:
    architectures = assembler.listValidArchitectures()

    if not architectures:
        raise InvalidArchitectureError

    print("\nAvailable architectures:")
    for index, architectureName in enumerate(architectures.values(), start=1):
        print(f"{index}. {architectureName}")

    while True:
        choice = input("Architecture choice: ").strip()

        if choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(architectures):
                return list(architectures.keys())[index]

        print("Select a valid architecture.")

def build() -> tuple[bool, list[str], list[assembler.ResolvedLine], str]:
    try:
        architectureName = getArchitecture()
        programName = getProgram()
    except InvalidArchitectureError:
        print(f"No valid architecture found. Please add a valid architecture JSON file in the {assembler.ARCHITECTURE_DIRECTORY}\\ directory.")
        return False, [], [], ''

    try:
        machineCode: list[str]
        resolvedLines: list[assembler.ResolvedLine]
        machineCode, resolvedLines = assembler.assembleProgram(programName, architectureName)

        return True, machineCode, resolvedLines, programName
    except assembler.ProgramValidationError:
        print(f"Program could not be assembled because of errors.\nError log: {assembler.LOGS_DIRECTORY}\\{programName}.log")
    except assembler.ArchitectureFileNotFoundError:
        print(f"Architecture JSON file not found: {assembler.ARCHITECTURE_DIRECTORY}\\{architectureName}.json")
    except assembler.SourceFileNotFoundError:
        print(f"Program file not found: {assembler.PROGRAMS_DIRECTORY}\\{programName}{assembler.getFileExtension(architectureName)}")
    except ValidationError:
        print(f"Architecture JSON file is not valid: {assembler.ARCHITECTURE_DIRECTORY}\\{architectureName}.json")

    return False, [], [], ''

def buildProgram() -> None:
    success, machineCode, _, programName = build()

    if success:
        assembler.writeMachineCode(programName, machineCode)
        print(f"Program assembled successfully.\nAvailable in: {assembler.MACHINE_CODE_OUTPUT_DIRECTORY}\\{programName}.mc")

def buildListing() -> None:
    success, machineCode, resolvedLines, programName = build()

    if success:
        assembler.generateAnnotatedListing(programName, machineCode, resolvedLines)
        print(f"Annotated listing created successfully.\nAvailable in: {assembler.ANNOTATED_LISTING_DIRECTORY}\\{programName}.lst")

def runChoice(choice: str) -> bool:
    match choice:
        case "1":
            buildProgram()
            return True
        case "2":
            buildListing()
            return True
        case "3":
            return False
        case _:
            return True

def main() -> None:
    while True:
        showTitle()

        choice = getChoice()
        shouldContinue = runChoice(choice)

        if not shouldContinue:
            break

        pause()
        clearConsole()

if __name__ == "__main__":
    main()