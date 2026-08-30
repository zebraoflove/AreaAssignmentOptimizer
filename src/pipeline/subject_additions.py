from src.config.subjects import MANUAL_SUBJECTS


def apply_manual_subject_additions(subjects):
    """Добавляет субъекты, отсутствующие в источнике Росстата."""

    existing_names = {
        subject["name"].strip()
        for subject in subjects
    }

    result = list(subjects)

    for subject in MANUAL_SUBJECTS:
        name = subject["name"].strip()

        if name in existing_names:
            continue

        result.append(subject.copy())

    return result