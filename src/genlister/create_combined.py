from pathlib import Path

from genlister.core import TYPE2COMBINED, CombinedCSV, TypeOfListEnum


def get_total_departments(dir: Path) -> int:
    """Counts the number of subdirectories in the specified directory.

    Args:
        dir (Path): The directory to count subdirectories in.

    Returns:
        int: The total number of subdirectories in the specified directory.
    """
    return sum(1 for d in dir.iterdir() if d.is_dir())


def is_duplicate(genes: list[CombinedCSV], candidate: CombinedCSV) -> bool:
    """Check if a candidate gene is a duplicate of any gene in the list.

    Args:
        genes (list[CombinedCSV]): List of existing genes.
        candidate (CombinedCSV): Candidate gene to check.

    Returns:
        bool: True if the candidate gene is a duplicate, False otherwise.
    """
    return any(gene.hugo_name == candidate.hugo_name for gene in genes)


def combine_files(dir: Path) -> None:
    """Combines CSV files from a specified directory into a single CSV file.

    Args:
        dir (Path): The directory containing the CSV files to be combined.

    Returns:
        None

    This function performs the following steps:
    1. Retrieves the total number of departments from the directory.
    2. Determines the type of combinator to use based on the type of list.
    3. Defines the CSV header for the output file.
    4. Initializes an empty dictionary to store gene information.
    5. Iterates through each CSV file in the directory, reading and processing each row.
    6. Combines the information from each row into the gene dictionary.
    7. Writes the combined gene information to an output CSV file.

    The output CSV file is sorted by the number of departments (in descending order) and then by the gene name.
    If no gene information is found, the function returns without creating an output file.
    """
    total_departments = get_total_departments(dir)
    combinator = TYPE2COMBINED[type_of_list]
    csv_header = combinator.csv_header()
    output = dir / "combined.csv"
    genes: dict[int, CombinedCSV] = dict()
    default = {"total": total_departments, "departments": set()}
    for fname in dir.glob("*/*.csv"):
        with open(fname, "r") as f:
            header = f.readline().strip().split(",")
            for row in f:
                values = {k: v for k, v in zip(header, row.strip().split(","))}
                candidate = combinator.model_validate(values | default)
                if gene_row := genes.get(candidate.hgnc_id):
                    gene_row.add_info(candidate, fname.parent.name)
                else:
                    if is_duplicate(list(genes.values()), candidate):
                        raise ValueError(
                            f'Gene "{candidate.hugo_name}" with HGNC_ID "{candidate.hgnc_id}" is in another department with another HGNC_ID. This is not allowed.'
                        )
                    candidate.add_info(candidate, fname.parent.name)
                    genes[candidate.hgnc_id] = candidate
    if not genes:
        return

    with open(output, "w") as fh:
        fh.writelines(
            [csv_header + "\n"]
            + [
                str(gene) + "\n"
                for gene in sorted(
                    genes.values(),
                    key=lambda g: (-len(g.departments), g.hugo_name),
                )
            ]
        )


if __name__ == "__main__":
    for type_of_list in TypeOfListEnum:
        dir = Path(type_of_list.value)
        if not dir.exists():
            continue
        combine_files(dir)
