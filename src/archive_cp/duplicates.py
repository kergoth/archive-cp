

def filter_duplicates(groups: Iterable[Sequence[Path]], deduplicate) -> Tuple[Sequence[Path], Sequence[Path]]:
    """Filter out duplicates which are not preferred."""
    file_times: Dict[Path, datetime.datetime] = {}

    def timefunc(f: Path) -> datetime.datetime:
        return file_times[f]

    files, unselected = [], []
    for group in groups:
        for f in group:
            file_times[f] = mtime(f)

        if len(group) > 1:
            selected, group_unselected = deduplicate(group)
            files.append(selected)
            unselected.extend(group_unselected)
        else:
            files.append(group[0])

    return files, unselected
