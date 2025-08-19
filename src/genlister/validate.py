from pathlib import Path

from pydantic import ValidationError

from genlister.core import TYPE2VALIDATOR, CSVBase, TypeOfListEnum


def clean_error(e: ValidationError) -> str:
    """Cleans a ValidationError object and returns a formatted string.

    Args:
        e (ValidationError): The ValidationError object to be cleaned.

    Returns:
        str: A formatted string with cleaned error messages.
    """
    res: list[str] = []
    for index, line in enumerate(str(e).split("\n")):
        match index % 3:
            case 1:
                res.append(f"* **{line}**: ")
            case 2:
                res[-1] += line[2 : line.index("[") - 1]
            case _:
                pass
    return "\n".join(res)


def is_duplicate(genes: list[CSVBase], gene_row: CSVBase) -> bool:
    """Checks if a gene row is a duplicate based on HUGO name or HGNC ID.

    Args:
        genes (list[CSVBase]): A list of CSVBase objects representing existing genes.
        gene_row (CSVBase): The CSVBase object representing the gene row to check for duplication.

    Returns:
        bool: True if the gene row is a duplicate, False otherwise.
    """
    return any(gene.hugo_name == gene_row.hugo_name for gene in genes) or any(
        gene.hgnc_id == gene_row.hgnc_id for gene in genes
    )


def validate_file(type_of_list: TypeOfListEnum, fname: Path):
    """Validates a CSV file based on the specified type of list.

    This function reads a CSV file, validates each row against a specified validator,
    and checks for duplicates based on HUGO name or HGNC ID. If any validation errors
    or duplicates are found, it prints relevant error messages.

    Args:
        type_of_list (TypeOfListEnum): The type of list to validate against.
        fname (Path): The path to the CSV file to be validated.

    Raises:
        IOError: If the specified file does not exist.

    Returns:
        None
    """
    if not fname.exists():
        raise IOError(f"File not found: {fname}")
    validator = TYPE2VALIDATOR[type_of_list]
    genes: list[CSVBase] = []
    has_printed_fname = False
    with open(fname, "r") as f:
        header = f.readline().strip().split(",")
        for row in f:
            values = {k: v for k, v in zip(header, row.strip().split(","))}
            try:
                gene_row = validator.model_validate(values)
            except ValidationError as e:
                if not has_printed_fname:
                    print(f"**{fname}**")
                    has_printed_fname = True
                print(f"Noget er galt med rækken:\n**{row.strip()}**", end="\n")
                print(f"{clean_error(e)}\n")
                continue
            if is_duplicate(genes, gene_row):
                if not has_printed_fname:
                    print(f"**{fname}**")
                    has_printed_fname = True
                print(f"Noget er galt med rækken:\n**{row.strip()}**", end="\n")
                print("Der er tale om en duplikat")
            else:
                genes.append(gene_row)


if __name__ == "__main__":
    for type_of_list in TypeOfListEnum:
        dir = Path(type_of_list.value)
        if not dir.exists():
            continue
        for file in dir.glob("*/*.csv"):
            validate_file(type_of_list, file)
