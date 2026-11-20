import csv
from pathlib import Path
from itertools import combinations


PROJECT_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_DATASET = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "ddinter2_consolidated.csv"
)


def normalize_drug_name(name):
    return " ".join(name.strip().casefold().split())


class MedicationInteractionEngine:

    def __init__(self, dataset_path=None):
        self.dataset_path = Path(dataset_path or DEFAULT_DATASET)
        self.interactions = {}
        self.known_drugs = set()

        self._load_dataset()

    def _load_dataset(self):
        if not self.dataset_path.is_file():
            raise FileNotFoundError(
                f"Interaction dataset not found: {self.dataset_path}"
            )

        with self.dataset_path.open(
            encoding="utf-8",
            newline=""
        ) as file:

            reader = csv.DictReader(file)

            required = {
                "DDInterID_A",
                "Drug_A",
                "DDInterID_B",
                "Drug_B",
                "Level",
                "Occurrence_Count",
                "Source_Files"
            }

            if not required.issubset(reader.fieldnames or []):
                raise ValueError("Invalid DDInter dataset columns")

            for row in reader:
                drug_a = normalize_drug_name(row["Drug_A"])
                drug_b = normalize_drug_name(row["Drug_B"])

                if not drug_a or not drug_b:
                    continue

                pair = tuple(sorted((drug_a, drug_b)))

                self.known_drugs.update(pair)
                self.interactions[pair] = {
                    "drug_a": row["Drug_A"],
                    "drug_b": row["Drug_B"],
                    "severity": row["Level"],
                    "ddinter_id_a": row["DDInterID_A"],
                    "ddinter_id_b": row["DDInterID_B"],
                    "occurrence_count": int(row["Occurrence_Count"]),
                    "source_files": row["Source_Files"],
                    "evidence_source": "DDInter 2.0"
                }

    def check_interactions(self, medications):
        if not isinstance(medications, (list, tuple)):
            raise TypeError("Medications must be a list or tuple")

        cleaned = {}

        for name in medications:
            if not isinstance(name, str) or not name.strip():
                raise ValueError("Every medication must have a valid name")

            normalized = normalize_drug_name(name)
            cleaned.setdefault(normalized, name.strip())

        names = list(cleaned.keys())
        results = []

        for drug_a, drug_b in combinations(names, 2):
            pair = tuple(sorted((drug_a, drug_b)))
            evidence = self.interactions.get(pair)

            if evidence:
                results.append({
                    "status": "interaction_found",
                    **evidence
                })
            else:
                results.append({
                    "status": "no_recorded_interaction",
                    "drug_a": cleaned[drug_a],
                    "drug_b": cleaned[drug_b],
                    "severity": None,
                    "evidence_source": "DDInter 2.0"
                })

        unmatched = [
            cleaned[name]
            for name in names
            if name not in self.known_drugs
        ]

        return {
            "input_medications": list(cleaned.values()),
            "total_medications": len(names),
            "total_pairs_checked": len(results),
            "interactions": results,
            "unmatched_medications": unmatched,
            "disclaimer": (
                "No recorded interaction does not establish safety. "
                "This result is not a clinical clearance or prescription."
            )
        }
