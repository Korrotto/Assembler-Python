from os import makedirs
from os.path import dirname, join, abspath
import sys
from json import load
from typing import Any
from re import match, IGNORECASE


if getattr(sys, 'frozen', False):
    scriptDirectory: str = dirname(sys.executable)
else:
    scriptDirectory: str = dirname(abspath(__file__))

ARCHITECTURE_DIRECTORY: str = join(scriptDirectory, 'Architecture')
PROGRAMS_DIRECTORY: str = join(scriptDirectory, 'Programs')
MACHINE_CODE_OUTPUT_DIRECTORY: str = join(scriptDirectory, 'Machine Code')
ERRORS_DIRECTORY: str = join(scriptDirectory, 'Errors')
ANNOTATED_LISTING_DIRECTORY: str = join(scriptDirectory, 'Annoted List')

class SourceLine:
    def __init__(self, lineNumber: int, rawLine: str):
        self.lineNumber: int = lineNumber
        self.rawLine: str = rawLine.rstrip('\r\n') 

    def getRawLine(self) -> str:
        return self.rawLine.strip()
    
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

class ValidationError(Exception):
    pass

class ArchitectureFileNotFoundError(FileNotFoundError):
    pass

class SourceFileNotFoundError(FileNotFoundError):
    pass

# Lecture de l'architecture

def readArchitectureFile(architectureName: str) -> dict[str, Any]:
    architectureFilePath: str = join(ARCHITECTURE_DIRECTORY, f'{architectureName}.json')

    try:
        with open(architectureFilePath, 'r') as file:
            architectureData: dict[str, Any] = load(file)

        return architectureData
    except FileNotFoundError:
        raise ArchitectureFileNotFoundError(f'JSON file not found : {architectureFilePath}')

# Lecture du fichier

def readSourceFile(programName: str, fileExtension: str) -> list[SourceLine]:
    sourceFilePath: str = join(PROGRAMS_DIRECTORY, f'{programName}{fileExtension}')

    try:
        with open(sourceFilePath, 'r') as file:
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
        normalizedLine: str = sourceLine.getRawLine().strip().upper()

        if normalizedLine.startswith('//') or not normalizedLine:
            continue
        elif normalizedLine.startswith('DEFINE '):
            tokenizedLines.append(TokenizedLine(sourceLine.getLineNumber(), sourceLine.getRawLine(), normalizedLine.split(), 'directive'))
        elif normalizedLine.endswith(':'):
            tokenizedLines.append(TokenizedLine(sourceLine.getLineNumber(), sourceLine.getRawLine(), [normalizedLine[:-1]], 'label'))
        else:
            tokenizedLines.append(TokenizedLine(sourceLine.getLineNumber(), sourceLine.getRawLine(), normalizedLine.split(), 'instruction'))

    return tokenizedLines

# Detection des define et label

def detectAliases(tokenizedLines: list[TokenizedLine], aliasTable: dict[str, str | int]) -> tuple[list[TokenizedLine], dict[str, str | int], list[str]]:
    instructionLines: list[TokenizedLine] = []
    currentAddress: int= 0
    errorMessages: list[str] = []

    for tokenizedLine in tokenizedLines:
        lineType: str = tokenizedLine.getLineType()

        if lineType == 'directive':
            result: tuple[dict[str, str | int], list[str]] = detectDefineDirective(tokenizedLine, aliasTable)
            aliasTable, errorMessages = result[0], errorMessages + result[1]
        elif lineType == 'label':
            result: tuple[dict[str, str | int], list[str]] = detectLabel(tokenizedLine, aliasTable, currentAddress)
            aliasTable, errorMessages = result[0], errorMessages + result[1]
        else:
            currentAddress += 1
            instructionLines.append(tokenizedLine)

    return instructionLines, aliasTable, errorMessages

def detectDefineDirective(tokenizedLine: TokenizedLine, aliasTable: dict[str, str | int]) -> tuple[dict[str, str | int], list[str]]:
    tokens: list[str] = tokenizedLine.getTokens()

    if not len(tokens) == 4 or not tokens[2] == 'AS':
        return aliasTable, [f'Format error for define : (line {tokenizedLine.getLineNumber()} : {tokenizedLine.getRawLine()})']

    aliasName: str = tokens[1]
    aliasValue: str = tokens[3]

    if not bool(match(r'^[A-Z_][A-Z0-9_]*$', aliasName)):
        return aliasTable, [f"Invalid alias name '{aliasName}' : (line {tokenizedLine.getLineNumber()} : {tokenizedLine.getRawLine()})"]
    
    if aliasName in aliasTable:
        return aliasTable, [f'Alias already exists : {aliasName} (line {tokenizedLine.getLineNumber()} : {tokenizedLine.getRawLine()})']
    
    if isIntegerLiteral(aliasValue):
        aliasTable[aliasName] = convertToInteger(aliasValue)
        return aliasTable, []
    
    if aliasValue not in aliasTable:
        return aliasTable, [f'Unrecognised alias : {aliasValue} (line {tokenizedLine.getLineNumber()} : {tokenizedLine.getRawLine()})']
    
    aliasTable[aliasName] = aliasValue
    return aliasTable, []

def detectLabel(tokenizedLine: TokenizedLine, aliasTable: dict[str, str | int], currentAddress: int) -> tuple[dict[str, str | int], list[str]]:
    labelName: str = tokenizedLine.getTokens()[0]

    if not bool(match(r'^[A-Z_][A-Z0-9_]*$', labelName)):
        return aliasTable, [f"Invalid alias name '{labelName}' : (line {tokenizedLine.getLineNumber()} : {tokenizedLine.getRawLine()})"]
    elif labelName in aliasTable:
        return aliasTable, [f'Alias already exists : {labelName} (line {tokenizedLine.getLineNumber()} : {tokenizedLine.getRawLine()})']
    else:
        aliasTable[labelName] = currentAddress
        return aliasTable, []

def checkAlias(instructionLines: list[TokenizedLine], aliasTable: dict[str, str | int], defaultAlias: dict[str, int]):
    warningMessages: list[str] = []

    usedAlias: set[str] = set(defaultAlias)

    for instructionLine in instructionLines:
        tokens: list[str] = instructionLine.getTokens()[1:]

        for token in tokens:
            if token not in usedAlias:
                usedAlias.add(token)

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
            result: tuple[str | None, list[str]] = resolveSingleAlias(token, line, aliasTable)
            token, errorMessages = result[0], errorMessages + result[1]

            if token is not None:
                resolvedTokens.append(str(token))
       
        resolvedLines.append(ResolvedLine(line.getLineNumber(), line.getRawLine(), resolvedTokens, line.getLineType()))
    
    return resolvedLines, errorMessages

def resolveSingleAlias(token: str, tokenizedLine: TokenizedLine, aliasTable: dict[str, str | int]) -> tuple[str | None, list[str]]:
    if token in aliasTable:
        resolvedValue: int | None
        errorMessages: list[str]
        resolvedValue, errorMessages = resolveAliasChain(token, tokenizedLine, aliasTable)

        if resolvedValue is None: 
            errorMessages.append(f"Value unknown for alias '{token}' : (line {tokenizedLine.getLineNumber()} : {tokenizedLine.getRawLine()})")
            return None, errorMessages
        return str(resolvedValue), errorMessages
    
    elif isIntegerLiteral(token):
        return str(convertToInteger(token)), []
    
    return None, [f"Unrecognised alias '{token}' : (line {tokenizedLine.getLineNumber()} : {tokenizedLine.getRawLine()})"]

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
    return bool(match(r'^-?(?:[0-9]+|0b[01]+|0o[0-7]+|0d[0-9]+|0x[0-9a-fA-F]+)$', literal, IGNORECASE))

def convertToInteger(literal: str) -> int:
    if literal[0] == '-':
        return -convertToBase10(literal[1:])
    return convertToBase10(literal)

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
            errorMessages.append(f"Unsupported instruction '{instructionName}' : (ligne {line.getLineNumber()} : {line.getRawLine()})")
            continue

        operandBitSizes: list[int] = extractOperandBitSizes(instructionSet.get(instructionName, []))

        if len(tokens) - 1 != len(operandBitSizes):
            errorMessages.append(f"Format error for instruction : '{instructionName}' (ligne {line.getLineNumber()} : {line.getRawLine()})")
            continue
        
        result: tuple[list[str], list[str]] = validateOperandValues(line, operandBitSizes, tokens[1:], instructionName)

        errorMessages += result[0]
        warningMessages += result[1]
    
    return errorMessages, warningMessages

def extractOperandBitSizes(instructionFormat: list[str | int]) -> list[int]:
    operandBitSizes: list[int] = []

    for formatElement in instructionFormat:
        if not isinstance(formatElement, str):
            operandBitSizes.append(formatElement)

    return operandBitSizes

def validateOperandValues(resolvedLine: ResolvedLine, operandBitSizes: list[int], operandValues: list[str], instructionName: str) -> tuple[list[str], list[str]]:
    warningMessages: list[str] = []
    errorMessages: list[str] = []

    for exceptedBits, operandValue in zip(operandBitSizes, operandValues):
        try :
            warningMessages += validateSingleOperandSize(operandValue, resolvedLine, exceptedBits)
        except TypeError:
            errorMessages.append(f"Unable to convert the operand to an integer '{instructionName}' : '{operandValue}' (line {resolvedLine.getLineNumber()} : {resolvedLine.getRawLine()})")

    return errorMessages, warningMessages

def validateSingleOperandSize(operandValue: str, resolvedLine: ResolvedLine, bitWidth: int) -> list[str]:
    if int(operandValue) > (2 ** bitWidth - 1) or int(operandValue) < -(2 ** (bitWidth - 1)):
        return [f"Out-of-range value : {operandValue} (line {resolvedLine.getLineNumber()} : {resolvedLine.getRawLine()})"]
    return []

# Génération du code machine

def generateMachineCode(resolvedLines: list[ResolvedLine], instructionSet: dict[str, list[str | int]]):
    machineCode: list[str] = []

    for line in resolvedLines:
        tokens: list[str] = line.getTokens()
        instructionName: str = tokens[0]
        instructionFormat: list[str | int] = instructionSet.get(instructionName, [])
        
        machineCode.append(generateMachineInstruction(instructionFormat, tokens))
    
    return machineCode

def generateMachineInstruction(instructionFormat: list[str | int], tokens: list[str]) -> str:
    machineCodeLine: str = ''
    operandIndex: int = 1

    for i in range(len(instructionFormat)):
        formatElement: str | int = instructionFormat[i]

        if not isinstance(formatElement, str):
            machineCodeLine += bin(int(tokens[operandIndex]) & (2 ** formatElement - 1))[2:].zfill(formatElement)
            operandIndex += 1
            continue

        machineCodeLine += formatElement
    return machineCodeLine

# Exportation du code machine

def writeMachineCode(programName: str, machineCode: list[str]):
    makedirs(MACHINE_CODE_OUTPUT_DIRECTORY, exist_ok=True)
    machineCodeFilePath: str = join(MACHINE_CODE_OUTPUT_DIRECTORY, f'{programName}.mc')

    with open(machineCodeFilePath, 'w') as outputFile:
        for machineCodeLine in machineCode:
            outputFile.write(machineCodeLine + '\n')

# Exportation des erreurs et des warnings

def writeErrorsAndWarnings(errorMessages: list[str], warningMesages: list[str], programName: str):
    makedirs(ERRORS_DIRECTORY, exist_ok=True)
    errorsMessagesFilePath: str = join(ERRORS_DIRECTORY, f'{programName}.log')

    with open(errorsMessagesFilePath, 'w') as outputFile:
        for error in errorMessages:
            outputFile.write('Error : ' + error + '\n')
        for warning in warningMesages:
            outputFile.write('Warning : ' + warning + '\n')

# Assemblage d'un programme

def assembleProgram(programName: str, architectureName: str) -> tuple[list[str], list[ResolvedLine]]:
    architectureData: dict[str, Any] = readArchitectureFile(architectureName)
    
    instructionSet: dict[str, list[str | int]] = dict(architectureData.get('instructions', {}))
    defaultAliasTable: dict[str, int] = dict(architectureData.get('default_alias', {}))
    fileExtension: str = architectureData.get('file_extension', '')

    aliasTable: dict[str, str | int] = dict(defaultAliasTable)

    sourceLines: list[SourceLine] = readSourceFile(programName, fileExtension)
    
    tokenizedLines: list[TokenizedLine] = tokenizeSourceLines(sourceLines)

    instructionLines: list[TokenizedLine]
    resolvedLines: list[ResolvedLine]

    instructionLines, aliasTable, errorMessages = detectAliases(tokenizedLines, aliasTable)
    resolvedLines, errorMessages = resolveAliases(instructionLines, aliasTable, errorMessages)

    warningMessages: list[str] = checkAlias(instructionLines, aliasTable, defaultAliasTable)

    result = validateInstructions(resolvedLines, instructionSet)
    errorMessages += result[0]
    warningMessages += result[1]

    writeErrorsAndWarnings(errorMessages, warningMessages, programName)

    if errorMessages:
        raise ValidationError
    
    return generateMachineCode(resolvedLines, instructionSet), resolvedLines

# Création de liste annotée

def generateAnnotatedListing(programName: str, architectureName: str):
    columnHeaders: list[str] = ['Address', 'Machine Code', 'Source']

    machineCode: list[str]
    resolvedLines: list[ResolvedLine]
    machineCode, resolvedLines = assembleProgram(programName, architectureName)

    addresses: list[str] = []
    currentAddress: int = 0
    for _ in machineCode:
        addresses.append(f'0x{hex(currentAddress)[2:].upper().zfill(4)}')
        currentAddress += 1

    sourceRawLines: list[str] = [line.getRawLine() for line in resolvedLines]

    addressColumnWidth: int = max(len(columnHeaders[0]), max(len(address) for address in addresses))
    machineCodeColumnWidth: int = max(len(columnHeaders[1]), max(len(machineCodeLine) for machineCodeLine in machineCode))

    headerLine: str = (f'{columnHeaders[0].ljust(addressColumnWidth)}    {columnHeaders[1].ljust(machineCodeColumnWidth)}    {columnHeaders[2]}')
    separatorLine: str = '-' * len(headerLine)

    makedirs(ANNOTATED_LISTING_DIRECTORY, exist_ok=True)
    listingFilePath: str = join(ANNOTATED_LISTING_DIRECTORY, f'{programName}.lst')

    with open(listingFilePath, 'w') as file:
        file.write(headerLine + '\n')
        file.write(separatorLine + '\n')

        for address, machineCodeLine, sourceRawLine in zip(addresses, machineCode, sourceRawLines):
            line: str = (f'{address.ljust(addressColumnWidth)}    {machineCodeLine.ljust(machineCodeColumnWidth)}    {sourceRawLine}')
            file.write(line + '\n')
