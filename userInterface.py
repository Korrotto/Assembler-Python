import assembler
from os import system, name
from re import match

ARCHITECTURE: str = 'garnetCoreV3'

def clearConsole():
    system('cls' if name == 'nt' else 'clear')

def getProgram() -> str:
    print("\nNe pas indiquer l'extensions du fichier sinon le programme ne fonctionnera pas.")
    print("1. Pas d'espaces dans le nom du fichier.")
    print('2. Attention à ne pas utiliser deux fois le même nom.')

    return input('\n>>> Nom du programme : ').strip()

while True:
    print(r'''
     ██████╗  █████╗ ██████╗ ███╗   ██╗███████╗████████╗     ██████╗ ██████╗ ██████╗ ███████╗    ██╗   ██╗██████╗ 
    ██╔════╝ ██╔══██╗██╔══██╗████╗  ██║██╔════╝╚══██╔══╝    ██╔════╝██╔═══██╗██╔══██╗██╔════╝    ██║   ██║╚════██╗
    ██║  ███╗███████║██████╔╝██╔██╗ ██║█████╗     ██║       ██║     ██║   ██║██████╔╝█████╗      ██║   ██║ █████╔╝
    ██║   ██║██╔══██║██╔══██╗██║╚██╗██║██╔══╝     ██║       ██║     ██║   ██║██╔══██╗██╔══╝      ╚██╗ ██╔╝ ╚═══██╗
    ╚██████╔╝██║  ██║██║  ██║██║ ╚████║███████╗   ██║       ╚██████╗╚██████╔╝██║  ██║███████╗     ╚████╔╝ ██████╔╝
     ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝   ╚═╝        ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝      ╚═══╝  ╚═════╝ 
    ''')

    menu : str = input('1. Assembler le programme\n2. Créer une liste anotée\n3. Quittez\nChoix : ').strip()

    while not bool(match(r'^[123]$', menu)):
        menu : str = input('Sélectionner une des 3 options : ')

    match menu:
        case '1':
            programName: str = getProgram()

            try:
                machineCode: list[str] = assembler.assembleProgram(programName, ARCHITECTURE)[0]
                assembler.writeMachineCode(programName, machineCode)

                print(fr'Le programme à été assemblé avec succée.\nIl est disponible dans : {assembler.MACHINE_CODE_OUTPUT_DIRECTORY}\{programName}.grt3')
            except assembler.ValidationError:
                print(fr"Le programme n'a pas pu être assemblé suite à des erreurs.\nLa liste de ces erreurs est présente dans : {assembler.ERRORS_DIRECTORY}\{programName}.log")
            except assembler.ArchitectureFileNotFoundError:
                print(fr"Le fichier JSON de l'architecture est introuvable : {assembler.ARCHITECTURE_DIRECTORY}\{ARCHITECTURE}.json")
            except assembler.SourceFileNotFoundError:
                print(fr'Le programme est introuvable : {assembler.PROGRAMS_DIRECTORY}\{programName}.grt3')
        case '2':
            programName: str = getProgram()

            try:
                assembler.generateAnnotatedListing(programName, ARCHITECTURE)
            except assembler.ValidationError:
                print(fr"La liste annotée n'a pas pu être créée suite à des erreurs\nLa liste de ces erreurs est présente dans : {assembler.ERRORS_DIRECTORY}\{programName}.log")
            except assembler.ArchitectureFileNotFoundError:
                print(fr"Le fichier JSON de l'architecture est introuvable : {assembler.ARCHITECTURE_DIRECTORY}\{ARCHITECTURE}.json")
            except assembler.SourceFileNotFoundError:
                print(fr'Le programme est introuvable : {assembler.PROGRAMS_DIRECTORY}\{programName}.grt3')
        case '3':
            break

    input('Appuyez sur Entrée pour continuer...')
    clearConsole()