[![Validate CSV Files](https://github.com/DCCC-NOVA/genlister/actions/workflows/validation.yml/badge.svg)](https://github.com/DCCC-NOVA/genlister/actions/workflows/validation.yml)

# Genlister
## For fortolkere og klinikere
Her finder man genlister for kategorierne `germline`, `fusion`, `SNV` og `CNV`
for de forskellige afdelinger. Disse genlister ligger i mapperne du ser i
toppen af denne side.

For hver kategori findes der ligeledes en `combined.csv` fil der indeholder
alle gener på tværs af afdelingerne. Denne opdateres automatisk, når der sker
ændringer til de lokale genlister.

## For bioinformatikere
En ændring skal ske ved at lave et pull request. Derved vil der først
automatisk laves en validering af genlisten man forsøger at ændre. Hvis der er
fejl, vil disse vises som en kommentar i pull requestet. Hvis der ikke er fejl
(eller man har fikset dem), bliver der lavet en ny `combined.csv` fil for den
pågældende kategori. Man kan derefter blot merge sit pull request.

## FAQ
### Vi har ikke en bioinformatiker i vores afdeling. Hvordan gør vi?
I er meget velkommen til at kontakte MOMAs bioinformatiker for hjælp til dette,
da det er forventet der er få ændringer om året.
