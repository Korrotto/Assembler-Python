from os import listdir, makedirs
from os.path import dirname, join, abspath
import sys
from typing import TypedDict, cast
from json import JSONDecodeError, load
from re import match, IGNORECASE
from jsonschema import validate, ValidationError


if getattr(sys, 'frozen', False):
    scriptDirectory: str = dirname(sys.executable)
else:
    scriptDirectory: str = dirname(abspath(__file__))

ARCHITECTURE_DIRECTORY: str = join(scriptDirectory, 'Architecture')
PROGRAMS_DIRECTORY: str = join(scriptDirectory, 'Programs')
MACHINE_CODE_OUTPUT_DIRECTORY: str = join(scriptDirectory, 'Machine Code')
LOGS_DIRECTORY: str = join(scriptDirectory, 'Logs')
ANNOTATED_LISTING_DIRECTORY: str = join(scriptDirectory, 'Annotated List')

DIRECTIVE = 'directive'
USED_DIRECTIVE = 'used_directive'
LABEL = 'label'
INSTRUCTION = 'instruction'

JSON_SCHEMA: dict[str, object] = {
    "type": "object",
    "required": [
        "architecture_name",
        "instructions",
        "default_alias",
        "file_extension"
    ],
    "additionalProperties": False,
    "properties": {
        "architecture_name": {
            "type": "string",
            "minLength": 1
        },
        "instructions": {
            "type": "object",
            "minProperties": 1,
            "propertyNames": {
                "type": "string",
                "minLength": 1
            },
            "additionalProperties": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "anyOf": [
                        {
                            "type": "string",
                            "pattern": "^[01]+$"
                        },
                        {
                            "type": "integer",
                            "minimum": 1
                        }
                    ]
                }
            }
        },
        "default_alias": {
            "type": "object",
            "propertyNames": {
                "type": "string",
                "minLength": 1
            },
            "additionalProperties": {
                "type": "integer"
            }
        },
        "file_extension": {
            "type": "string",
            "pattern": "^\\..+$"
        }
    }
}

class ArchitectureData(TypedDict):
    architecture_name: str
    instructions: dict[str, list[str | int]]
    default_alias: dict[str, int]
    file_extension: str

class SourceLine:
    def __init__(self, lineNumber: int, rawLine: str):
        self.lineNumber: int = lineNumber
        self.rawLine: str = rawLine.rstrip('\r\n') 

    def getCleanLine(self) -> str:
        return self.rawLine.split('//', 1)[0].strip()
    
    def getLineNumber(self) -> int:
        return self.lineNumber

class TokenizedLine(SourceLine):
    def __init__(self, lineNumber: int , line: str, tokens: list[str], lineType: str):
        super().__init__(lineNumber, line)
        self.tokens: list[str] = tokens
        self.lineType: str = lineType

    def getTokens(self) -> list[str]:
        return self.tokens
    
    def getLineType(self) -> str:
        return self.lineType

class ResolvedLine(TokenizedLine):
    pass

class ProgramValidationError(Exception):
    pass

class ArchitectureFileNotFoundError(FileNotFoundError):
    pass

class SourceFileNotFoundError(FileNotFoundError):
    pass

# Validation de l'architecture

def listValidArchitectures() -> dict[str, str]:
    validsArchitectures: dict[str, str] = {}

    try:
        files: list[str] = [file for file in listdir(ARCHITECTURE_DIRECTORY) if file.endswith('.json')]

        for file in files:
            isValid: bool
            architectureName: str
            isValid, architectureName = isValidArchitecture(file)
            if isValid and architectureName:
                validsArchitectures[file[:-5]] = architectureName

    except FileNotFoundError:
        return {}
    
    return validsArchitectures

def isValidArchitecture(file: str) -> tuple[bool, str]:
    try:
        with open(join(ARCHITECTURE_DIRECTORY, file), 'r', encoding='utf-8') as architectureFile:
            rawData: dict[str, object] = load(architectureFile)
            validate(rawData, JSON_SCHEMA)
            architectureData = cast(ArchitectureData, rawData)
            return True, architectureData['architecture_name']
    except (FileNotFoundError, ValidationError, JSONDecodeError):
        return False, ''

# Lecture de l'architecture

def readArchitectureFile(architectureName: str) -> ArchitectureData:
    architectureFilePath: str = join(ARCHITECTURE_DIRECTORY, f'{architectureName}.json')

    try:
        with open(architectureFilePath, 'r', encoding='utf-8') as file:
            architectureData: ArchitectureData = load(file)
            validate(architectureData, JSON_SCHEMA)
        return architectureData

    except FileNotFoundError:
        raise ArchitectureFileNotFoundError(f'JSON file not found : {architectureFilePath}')
    except (JSONDecodeError, ValidationError) as error:
        raise ProgramValidationError(f'Invalid architecture file: {architectureFilePath} ({error})')

def getFileExtension(architectureName: str) -> str:
    architectureData: ArchitectureData = readArchitectureFile(architectureName)
    return architectureData['file_extension']

# Lecture du programme

def readSourceFile(programName: str, fileExtension: str) -> list[SourceLine]:
    sourceFilePath: str = join(PROGRAMS_DIRECTORY, f'{programName}{fileExtension}')

    try:
        with open(sourceFilePath, 'r', encoding='utf-8') as file:
            sourceLines: list[SourceLine] = []
            lineNumber: int = 1

            for line in file:
                sourceLines.append(SourceLine(lineNumber, line))
                lineNumber += 1

        return sourceLines
    except FileNotFoundError:
        raise SourceFileNotFoundError(f'Program file not found : {sourceFilePath}')

# Séparation de tout les éléments en mot-clés

def tokenizeSourceLines(sourceLines: list[SourceLine]) -> list[TokenizedLine]:
    tokenizedLines: list[TokenizedLine] = []

    for sourceLine in sourceLines:
        normalizedLine: str = sourceLine.getCleanLine().upper()

        if not normalizedLine:
            continue

        tokenLine: str = normalizedLine.replace(',', ' ')

        if tokenLine.startswith('DEFINE '):
            tokenizedLines.append(TokenizedLine(sourceLine.getLineNumber(), sourceLine.getCleanLine(), tokenLine.split(), DIRECTIVE))
        elif tokenLine.startswith('USED '):
            tokenizedLines.append(TokenizedLine(sourceLine.getLineNumber(), sourceLine.getCleanLine(), tokenLine.split(), USED_DIRECTIVE))
        elif tokenLine.endswith(':'):
            tokenizedLines.append(TokenizedLine(sourceLine.getLineNumber(), sourceLine.getCleanLine(), [tokenLine[:-1]], LABEL))
        elif tokenLine.startswith('.'):
            tokenizedLines.append(TokenizedLine(sourceLine.getLineNumber(), sourceLine.getCleanLine(), [tokenLine], LABEL))
        else:
            tokenizedLines.append(TokenizedLine(sourceLine.getLineNumber(), sourceLine.getCleanLine(), tokenLine.split(), INSTRUCTION))

    return tokenizedLines

# Detection des define et label

def detectAliases(tokenizedLines: list[TokenizedLine], aliasTable: dict[str, str | int]) -> tuple[list[TokenizedLine], list[str], set[str]]:
    instructionLines: list[TokenizedLine] = []
    currentAddress: int = 0
    errorMessages: list[str] = []
    forcedUsed : set[str] = set()

    for tokenizedLine in tokenizedLines:
        lineType: str = tokenizedLine.getLineType()

        if lineType == DIRECTIVE:
            errorMessages += detectDefineDirective(tokenizedLine, aliasTable)
        elif lineType == USED_DIRECTIVE:
            newErrors, label = detectUsedDirective(tokenizedLine)
            errorMessages += newErrors

            if label is not None:
                forcedUsed.add(label)
        elif lineType == LABEL:
            errorMessages += detectLabel(tokenizedLine, aliasTable, currentAddress)
        else:
            currentAddress += 1
            instructionLines.append(tokenizedLine)

    for label in forcedUsed:
        if label not in aliasTable:
            errorMessages.append(f"Undefined used label '{label}'")

    return instructionLines, errorMessages, forcedUsed

def detectDefineDirective(tokenizedLine: TokenizedLine, aliasTable: dict[str, str | int]) -> list[str]:
    tokens: list[str] = tokenizedLine.getTokens()

    if not len(tokens) == 4 or not tokens[2] == 'AS':
        return [f'Format error for define : (line {tokenizedLine.getLineNumber()} : {tokenizedLine.getCleanLine()})']

    aliasName: str = tokens[1]
    aliasValue: str = tokens[3]

    if not bool(match(r'^[A-Z_][A-Z0-9_]*$', aliasName)):
        return [f"Invalid alias name '{aliasName}' : (line {tokenizedLine.getLineNumber()} : {tokenizedLine.getCleanLine()})"]
    
    if aliasName in aliasTable:
        return [f'Alias already exists : {aliasName} (line {tokenizedLine.getLineNumber()} : {tokenizedLine.getCleanLine()})']
    
    if isIntegerLiteral(aliasValue):
        aliasTable[aliasName] = convertToInteger(aliasValue)
        return []
    
    if aliasValue not in aliasTable:
        return [f'Unrecognised alias : {aliasValue} (line {tokenizedLine.getLineNumber()} : {tokenizedLine.getCleanLine()})']
    
    aliasTable[aliasName] = aliasValue
    return []

def detectUsedDirective(tokenizedLine: TokenizedLine) -> tuple[list[str], str | None]:
    tokens: list[str] = tokenizedLine.getTokens()

    if len(tokens) != 2:
        return [f'Format error for used directive : (line {tokenizedLine.getLineNumber()} : {tokenizedLine.getCleanLine()})'], None

    label: str = tokens[1]

    if not bool(match(r'^[A-Z_.][A-Z0-9_]*$', label)):
        return [f"Invalid used label name '{label}' : (line {tokenizedLine.getLineNumber()} : {tokenizedLine.getCleanLine()})"], None

    return [], label

def detectLabel(tokenizedLine: TokenizedLine, aliasTable: dict[str, str | int], currentAddress: int) -> list[str]:
    labelName: str = tokenizedLine.getTokens()[0]

    if not bool(match(r'^[A-Z_.][A-Z0-9_]*$', labelName)):
        return [f"Invalid label name '{labelName}' : (line {tokenizedLine.getLineNumber()} : {tokenizedLine.getCleanLine()})"]
    elif labelName in aliasTable:
        return [f'Alias already exists : {labelName} (line {tokenizedLine.getLineNumber()} : {tokenizedLine.getCleanLine()})']
    else:
        aliasTable[labelName] = currentAddress
        return []

def checkAlias(instructionLines: list[TokenizedLine], aliasTable: dict[str, str | int], defaultAlias: dict[str, int], forcedUsed: set[str]) -> list[str]:
    warningMessages: list[str] = []
    usedAlias: set[str] = set(defaultAlias)

    for instructionLine in instructionLines:
        for token in instructionLine.getTokens()[1:]:
            if token in aliasTable:
                usedAlias.add(token)

    usedAlias.update(forcedUsed)

    for alias in aliasTable:
        if alias not in usedAlias:
            warningMessages.append(f'Alias defined but never used: {alias}')

    return warningMessages

# Résolution des define et label

def resolveAliases(instructionLines: list[TokenizedLine], aliasTable: dict[str, str | int], errorMessages: list[str]) -> tuple[list[ResolvedLine], list[str]]:
    resolvedLines: list[ResolvedLine] = []

    for line in instructionLines:
        tokens: list[str] = line.getTokens()
        resolvedTokens: list[str] = [tokens[0]]

        for token in tokens[1:]:
            resolvedToken, newErrors = resolveSingleAlias(token, line, aliasTable)
            errorMessages += newErrors

            if resolvedToken is not None:
                resolvedTokens.append(resolvedToken)
       
        resolvedLines.append(ResolvedLine(line.getLineNumber(), line.getCleanLine(), resolvedTokens, line.getLineType()))
    
    return resolvedLines, errorMessages

def resolveSingleAlias(token: str, tokenizedLine: TokenizedLine, aliasTable: dict[str, str | int]) -> tuple[str | None, list[str]]:
    if token in aliasTable:
        resolvedValue: int | None
        errorMessages: list[str]
        resolvedValue, errorMessages = resolveAliasChain(token, tokenizedLine, aliasTable)

        if resolvedValue is None: 
            errorMessages.append(f"Value unknown for alias '{token}' : (line {tokenizedLine.getLineNumber()} : {tokenizedLine.getCleanLine()})")
            return None, errorMessages
        return str(resolvedValue), errorMessages
    
    elif isIntegerLiteral(token):
        return str(convertToInteger(token)), []
    
    return None, [f"Value unknown for alias '{token}' : (line {tokenizedLine.getLineNumber()} : {tokenizedLine.getCleanLine()})"]

def resolveAliasChain(token: str, tokenizedLine: TokenizedLine, aliasTable: dict[str, str | int]) -> tuple[int | None, list[str]]:
    visitedAliases: set[str] = set()
    resolvedValue: str | int | None = token

    while isinstance(resolvedValue, str):
        if resolvedValue in visitedAliases:
            return None, [f'Circular alias detected : {token} (line {tokenizedLine.getLineNumber()})']

        visitedAliases.add(resolvedValue)
        resolvedValue = aliasTable.get(resolvedValue, None)
    
    return resolvedValue, []

def isIntegerLiteral(literal: str) -> bool:
    return bool(match(r'^[+-]?(?:[0-9]+|0b[01]+|0o[0-7]+|0d[0-9]+|0x[0-9a-fA-F]+)$', literal, IGNORECASE))

def convertToInteger(literal: str) -> int:
    return convertToBase10(literal.lstrip('+')) if not literal.startswith('-') else -convertToBase10(literal[1:])

def convertToBase10(literal: str) -> int:
    match literal[:2].lower():
        case '0b':
            return int(literal[2:], 2)
        case '0o':
            return int(literal[2:], 8)
        case '0d':
            return int(literal[2:])
        case '0x':
            return int(literal[2:], 16)
        case _:
            return int(literal)

# validateInstructions des instructions

def validateInstructions(resolvedLines: list[ResolvedLine], instructionSet: dict[str, list[str | int]]) -> tuple[list[str], list[str]]:
    errorMessages: list[str] = []
    warningMessages: list[str] = []

    for line in resolvedLines:
        tokens: list[str] = line.getTokens()
        instructionName: str = tokens[0]

        if instructionName not in instructionSet:
            errorMessages.append(f"Unsupported instruction '{instructionName}' : (line {line.getLineNumber()} : {line.getCleanLine()})")
            continue

        operandBitSizes: list[int] = extractOperandBitSizes(instructionSet[instructionName])

        if len(tokens) - 1 != len(operandBitSizes):
            errorMessages.append(f"Format error for instruction : '{instructionName}' (line {line.getLineNumber()} : {line.getCleanLine()})")
            continue
        
        result: tuple[list[str], list[str]] = validateOperandValues(line, operandBitSizes, tokens[1:], instructionName)

        errorMessages += result[0]
        warningMessages += result[1]
    
    return errorMessages, warningMessages

def extractOperandBitSizes(instructionFormat: list[str | int]) -> list[int]:
    return [element for element in instructionFormat if isinstance(element, int)]

def validateOperandValues(resolvedLine: ResolvedLine, operandBitSizes: list[int], operandValues: list[str], instructionName: str) -> tuple[list[str], list[str]]:
    warningMessages: list[str] = []
    errorMessages: list[str] = []

    for exceptedBits, operandValue in zip(operandBitSizes, operandValues):
        try :
            warningMessages += validateSingleOperandSize(operandValue, resolvedLine, exceptedBits)
        except (TypeError, ValueError):
            errorMessages.append(f"Unable to convert the operand to an integer '{instructionName}' : '{operandValue}' (line {resolvedLine.getLineNumber()} : {resolvedLine.getCleanLine()})")

    return errorMessages, warningMessages

def validateSingleOperandSize(operandValue: str, resolvedLine: ResolvedLine, bitWidth: int) -> list[str]:
    value: int = int(operandValue)

    if value > (2 ** bitWidth - 1) or value < -(2 ** (bitWidth - 1)):
        return [f"Value truncated to fit in {bitWidth} bits: {operandValue} -> {value & ((1 << bitWidth) - 1)} : (line {resolvedLine.getLineNumber()} : {resolvedLine.getCleanLine()})"]
    return []

# Génération du code machine

def generateMachineCode(resolvedLines: list[ResolvedLine], instructionSet: dict[str, list[str | int]]) -> list[str]:
    machineCode: list[str] = []

    for line in resolvedLines:
        tokens: list[str] = line.getTokens()
        instructionName: str = tokens[0]
        instructionFormat: list[str | int] = instructionSet[instructionName]
        
        machineCode.append(generateMachineInstruction(instructionFormat, tokens))
    
    return machineCode

def generateMachineInstruction(instructionFormat: list[str | int], tokens: list[str]) -> str:
    machineCodeLine: str = ''
    operandIndex: int = 1

    for formatElement in instructionFormat:
        if not isinstance(formatElement, str):
            machineCodeLine += bin(int(tokens[operandIndex]) & ((1 << formatElement) - 1))[2:].zfill(formatElement)
            operandIndex += 1
            continue

        machineCodeLine += formatElement
    return machineCodeLine

# Exportation du code machine

def writeMachineCode(programName: str, machineCode: list[str]) -> None:
    makedirs(MACHINE_CODE_OUTPUT_DIRECTORY, exist_ok=True)
    machineCodeFilePath: str = join(MACHINE_CODE_OUTPUT_DIRECTORY, f'{programName}.mc')

    with open(machineCodeFilePath, 'w', encoding='utf-8') as outputFile:
        for machineCodeLine in machineCode:
            outputFile.write(machineCodeLine + '\n')

# Exportation des erreurs et des warnings

def writeErrorsAndWarnings(errorMessages: list[str], warningMessages: list[str], programName: str) -> None:
    makedirs(LOGS_DIRECTORY, exist_ok=True)
    errorsMessagesFilePath: str = join(LOGS_DIRECTORY, f'{programName}.log')

    if not errorMessages and not warningMessages:
        return None

    with open(errorsMessagesFilePath, 'w', encoding='utf-8') as outputFile:
        for error in errorMessages:
            outputFile.write('Error : ' + error + '\n')
        for warning in warningMessages:
            outputFile.write('Warning : ' + warning + '\n')

# Assemblage d'un programme

def assembleProgram(programName: str, architectureName: str) -> tuple[list[str], list[ResolvedLine]]:
    architectureData: ArchitectureData = readArchitectureFile(architectureName)
    
    instructionSet: dict[str, list[str | int]] = dict(architectureData['instructions'])
    defaultAliasTable: dict[str, int] = dict(architectureData['default_alias'])
    fileExtension: str = architectureData['file_extension']

    aliasTable: dict[str, str | int] = dict(defaultAliasTable)

    sourceLines: list[SourceLine] = readSourceFile(programName, fileExtension)
    
    tokenizedLines: list[TokenizedLine] = tokenizeSourceLines(sourceLines)

    instructionLines, errorMessages, forcedUsed = detectAliases(tokenizedLines, aliasTable)
    resolvedLines, errorMessages = resolveAliases(instructionLines, aliasTable, errorMessages)

    warningMessages: list[str] = checkAlias(instructionLines, aliasTable, defaultAliasTable, forcedUsed)

    result = validateInstructions(resolvedLines, instructionSet)
    errorMessages += result[0]
    warningMessages += result[1]

    writeErrorsAndWarnings(errorMessages, warningMessages, programName)

    if errorMessages:
        raise ProgramValidationError(f"Assembly failed for '{programName}{fileExtension}' with {len(errorMessages)} error(s).")
    
    return generateMachineCode(resolvedLines, instructionSet), resolvedLines

# Création de liste annotée

def generateAnnotatedListing(programName: str, machineCode: list[str], resolvedLines: list[ResolvedLine]) -> None:
    columnHeaders: list[str] = ['Address', 'Machine Code', 'Source']

    addresses: list[str] = [f'0x{i:04X}' for i, _ in enumerate(machineCode)]

    sourceLines: list[str] = [line.getCleanLine() for line in resolvedLines]

    addressColumnWidth: int = max(len(columnHeaders[0]), max(len(address) for address in addresses)) if addresses else len(columnHeaders[0])
    machineCodeColumnWidth: int = max(len(columnHeaders[1]), max(len(line) for line in machineCode)) if machineCode else len(columnHeaders[1])

    headerLine: str = (f'{columnHeaders[0].ljust(addressColumnWidth)}    {columnHeaders[1].ljust(machineCodeColumnWidth)}    {columnHeaders[2]}')
    separatorLine: str = '-' * len(headerLine)

    makedirs(ANNOTATED_LISTING_DIRECTORY, exist_ok=True)
    listingFilePath: str = join(ANNOTATED_LISTING_DIRECTORY, f'{programName}.lst')

    with open(listingFilePath, 'w', encoding='utf-8') as file:
        file.write(headerLine + '\n')
        file.write(separatorLine + '\n')

        for address, machineCodeLine, sourceLine in zip(addresses, machineCode, sourceLines):
            line: str = (f'{address.ljust(addressColumnWidth)}    {machineCodeLine.ljust(machineCodeColumnWidth)}    {sourceLine}')
            file.write(line + '\n')