from pathlib import Path

from genlister.core import TYPE2COMBINED, CombinedCSV, TypeOfListEnum


def get_total_departments(dir: Path) -> int:
    s = 0
    for candidate in dir.iterdir():
        if candidate.is_dir():
            s += 1
    return s


def combine_files(dir: Path) -> None:
    total_departments = get_total_departments(dir)
    combinator = TYPE2COMBINED[type_of_list]
    csv_header = combinator.csv_header()
    output = dir / "combined.csv"
    genes: dict[str, CombinedCSV] = dict()
    default = {"total": total_departments, "departments": set()}
    for fname in dir.glob("*/*.csv"):
        with open(fname, "r") as f:
            header = f.readline().strip().split(",")
            for row in f:
                values = {k: v for k, v in zip(header, row.strip().split(","))}
                candidate = combinator.model_validate(values | default)
                if gene_row := genes.get(candidate.hugo_name):
                    gene_row.add_department(fname.parent.name)
                else:
                    candidate.add_department(fname.parent.name)
                    genes[candidate.hugo_name] = candidate
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
