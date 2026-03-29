# Petit assembleur Python

Un assembleur écrit en Python pour tester des architectures faites maison.

Le fichier principal est assembler.py.  
Le reste (interface, architectures, programmes) sert surtout d’exemple et de test.

## Organisation

```
├── assembler.py
├── userInterface.py
├── Architecture/
│ ├── garnetCoreV2.json
│ └── garnetCoreV3.json
├── Programs/
│ ├── hello_world.grt3
│ ├── error.grt3
│ └── division.grt3
├── Machine Code/
├── Logs/
│ └── error.log
└── Annotated List/
  └── division.lst
```

## Fonctionnement

On donne :

- une architecture (JSON)
- un programme assembleur

Le script :

- analyse le code
- résout les alias et labels
- vérifie les instructions
- génère le code machine

## Utilisation

### Prérequis

- Python 3.10 ou supérieur
- jsonschema

Installation Jsonschema:

``` bash
pip install -r requirements.txt
```

### Avec l’interface

``` bash
python userInterface.py
```

## Langage assembleur

### Instructions

``` asm
ADD R1 R5 R4
ADD R1, R5, R4
```

### Commentaires

``` asm
// commentaire
ADD 1 5 2 // commentaire en fin de ligne
```

### Alias

``` asm
DEFINE TMP AS R1  
DEFINE BASE AS R0
```

Un alias est simplement un nom qui référence une valeur ou un autre alias.

### Labels

``` asm
START:
    JMP START

.main
    JMP .main
```

Un label est un alias particulier qui correspond à une adresse dans le programme.

### Directive USED

``` asm
USED START
USED .main
```

Permet d’indiquer explicitement qu’un label est utilisé, même s’il n’apparaît pas dans les instructions.

Utile pour :

les points d’entrée  
éviter les warnings "alias non utilisé"  

## Programmes fournis

***hello_world.grt3***

Affiche "HELLO WORLD" en écrivant caractère par caractère.

Extrait :

``` asm
DEFINE BASE AS R0
DEFINE TMP  AS R1

USED START

START:
    LDI TMP 'H'
    STR TMP 0 BASE
    OUT 0 BASE

    HLT
```


***division.grt3***

Division entière simple par soustraction répétée.

Extrait :

``` asm
DEFINE OUTRESTE AS R0
DEFINE OUTQUOTIENT AS R5
DEFINE DIVIDENDE AS R1
DEFINE DIVISEUR AS R2
DEFINE QUOTIENT AS R3

USED START

START:
    LDI DIVIDENDE 50
    LDI DIVISEUR 7
    LDI QUOTIENT 0
    LDI OUTQUOTIENT 1

LOOP:
    ARI SUB R0 DIVIDENDE DIVISEUR
    BRH CARRY END

    ARI SUB DIVIDENDE DIVIDENDE DIVISEUR
    UDI ADD QUOTIENT 1
    JMP LOOP

END:
    STR DIVIDENDE 0 R0
    STR QUOTIENT 1 R0
    PRT OUT 0 OUTRESTE
    PRT OUT 1 OUTQUOTIENT
    HLT
```

## Architecture (JSON)

Les fichiers dans Architecture/ définissent comment les instructions sont transformées en code machine.

### Structure

``` json
{
  "architecture_name": "Nom",
  "instructions": { ... },
  "default_alias": { ... },
  "file_extension": ".ext"
}
```

### Instructions (instructions)

Chaque instruction est une liste :

strings → bits fixes  
nombres → taille des opérandes (en bits)

Exemple :

``` json
"ADD": ["0001", 4, 4, 4]
```

→ opcode + 3 opérandes

``` json
"LDI": ["0110", "00", 4, 8]
```

→ opcode + bits fixes + registre + valeur

### Alias (default_alias)

Permet de définir des alias par défaut (Aucune vérification de leur utilisation)

Exemple :

``` json
"R0": 0,
"R1": 1,
"ZERO": 0
```

Donc :

```
ADD R1 R2 R3
```

devient :

```
ADD 1 2 3
```

### Extension (file_extension)

``` json
"file_extension": ".grt3"
```

L'extension des programmes liès à l'architecture

### Erreurs et warnings

Les logs sont générés ici :

Logs/nom_du_programme.log

#### Erreurs (bloquantes)

- instruction inconnue
- mauvais nombre d’arguments
- alias invalide
- alias inconnu
- directive mal formée
- alias circulaire (normalement ne devrait jamais arrivé)

#### Warnings (non bloquants)

- valeur hors limite pour le nombre de bits (la valeur est tronquée)
- alias défini mais jamais utilisé

Exemple de log :

Avec le programme error.grt3 :

``` log
Error : Alias already exists : TMP (line 3 : DEFINE TMP  AS R2)
Error : Unrecognised alias : ERROR (line 4 : DEFINE TEST AS ERROR)
Error : Format error for define : (line 5 : DEFINE A TEST)
Error : Invalid alias name '?' : (line 6 : DEFINE ? AS R0)
Error : Value unknown for alias ''H' : (line 10 : LDI TMP 'H)
Error : Value unknown for alias 'BAS' : (line 11 : STR TMP BAS)
Error : Format error for instruction : 'LDI' (line 10 : LDI TMP 'H)
Error : Format error for instruction : 'STR' (line 11 : STR TMP BAS)
Error : Unsupported instruction 'OIT' : (line 12 : OIT 500000 BASE)
Error : Format error for instruction : 'STR' (line 16 : STR TMP BASE)
Warning : Alias defined but never used: START
```

### Sorties

**Code machine :**  
Machine Code/nom.mc

**Liste annotée :**  
Annotated List/nom.lst

### Notes
assembler.py contient toute la logique  
le projet est fait pour expérimenter des architectures  
tout est modifiable facilement pour créer sa propre ISA 
