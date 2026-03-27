# Petit assembleur Python

Un assembleur écrit en Python pour tester des architectures faites maison.

Le fichier principal est assembler.py.
Le reste (interface, architectures, programmes) sert surtout d’exemple et de test.

## Organisation  
├── assembler.py  
├── userInterface.py  
├── Architecture/  
│   ├── garnetCoreV2.json  
│   └── garnetCoreV3.json  
├── Programs/  
│   ├── hello_world.grt3  
│   └── division.grt3  
├── Machine Code/  
├── Errors/  
├── Annoted List/  

## Fonctionnement

On donne :

une architecture (JSON)
un programme assembleur

Le script :

analyse le code  
résout les alias et labels  
vérifie les instructions  
génère le code machine  
## Utilisation  
Avec l’interface (Pour l'architecture Garnet Core V3)
``` bash
python userInterface.py  
```

Ou directement  

``` python
import assembler 

machine_code, _ = assembler.assembleProgram("hello_world", "garnetCoreV3")
assembler.writeMachineCode("hello_world", machine_code)
```

Changez hello_world par le nom du programme et garnetCoreV3 par le nom de l'architecture

## Langage assembleur

### Commentaires

```
// commentaire
```

### Alias

```
DEFINE TMP AS R1  
DEFINE BASE AS R0
```

### Labels

```
START:
    JMP START
```


### Programmes fournis

hello_world.grt3

Affiche "HELLO WORLD" en écrivant caractère par caractère.

```
DEFINE BASE AS R0
DEFINE TMP  AS R1

START:
    LDI TMP 'H'
    STR TMP 0 BASE
    OUT 0 BASE

    HLT
```

division.grt3

Division entière simple par soustraction répétée.

```
DEFINE OUTRESTE    AS R0
DEFINE OUTQUOTIENT AS R5
DEFINE DIVIDENDE   AS R1
DEFINE DIVISEUR    AS R2
DEFINE QUOTIENT    AS R3
DEFINE TMP         AS R4

START:
    LDI DIVIDENDE 50
    LDI DIVISEUR  7
    LDI QUOTIENT  0
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
  "word_size": 16,
  "instructions": { ... },
  "default_alias": { ... },
  "file_extension": ".ext"
}
```
### Instructions (instructions)

Chaque instruction est une liste :

strings → bits fixes  
nombres → taille des opérandes (en bits)  
Exemple  
"ADD": ["0001", 4, 4, 4]

→ opcode + 3 opérandes

"LDI": ["0110", "00", 4, 8]

→ opcode + bits fixes + registre + valeur

### Alias (default_alias)

Permet de mettre des noms sur des valeurs.

Exemple  
"R0": 0,  
"R1": 1,  
"ZERO": 0  

Donc :

ADD R1 R2 R3

devient :

ADD 1 2 3

### Extension (file_extension)

``` json
"file_extension": ".grt3"
```

Définit le type de fichier attendu.

À retenir  
l’ordre dans les instructions = ordre des bits  
les nombres définissent la taille des champs  
les strings sont ajoutées telles quelles  
les alias simplifient l’écriture du code

## Erreurs et warnings  

Les logs sont générés ici :

Errors/nom_du_programme.log  

Erreurs (bloquantes)  
instruction inconnue  
mauvais nombre d’arguments  
alias invalide  
alias inconnu  
alias circulaire  

Warnings (non bloquants)  
valeur hors limite pour le nombre de bits  
(la valeur est tronquée pour rentrer dans la taille)  
alias défini mais jamais utilisé  

## Sorties
code machine :  
Machine Code/nom.mc  
liste annotée :  
Annoted List/nom.lst  


## Notes
assembler.py contient toute la logique  
le projet est fait pour expérimenter des architectures  
tout est modifiable facilement si tu veux créer ta propre ISA
