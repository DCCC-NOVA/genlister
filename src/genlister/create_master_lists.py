from pathlib import Path

from genlister.core import TYPE2VALIDATOR, CSVBase, TypeOfListEnum


def combine_files(dir: Path) -> None:
    validator = TYPE2VALIDATOR[type_of_list]
    csv_header: str = ",".join((key for key in validator.model_fields))
    output = dir / "combined.csv"
    genes: set[CSVBase] = set()
    for fname in dir.glob("*/*.csv"):
        with open(fname, "r") as f:
            header = f.readline().strip().split(",")
            for row in f:
                values = {k: v for k, v in zip(header, row.strip().split(","))}
                gene_row = validator.model_validate(values)
                genes.add(gene_row)
    if not genes:
        return

    with open(output, "w") as fh:
        fh.writelines(
            [csv_header + "\n"]
            + [
                gene.to_csv() + "\n"
                for gene in sorted(genes, key=lambda g: g.hugo_name)
            ]
        )


if __name__ == "__main__":
    for type_of_list in TypeOfListEnum:
        dir = Path(type_of_list.value)
        if not dir.exists():
            continue
        combine_files(dir)
