import json

from splat.model import AuditReport, Dependency, DependencyType


def restructure_audit_reports(
    reports: list[AuditReport], pipenv_graph_output: str, direct_deps: list[Dependency]
) -> list[AuditReport]:
    """
    Restructures the audit reports by associating transitive dependencies with their parent
    dependencies using pipenv graph output.
    """
    direct_deps_dict = {dep.name: dep for dep in direct_deps}
    direct_deps_names = set(direct_deps_dict.keys())
    existing_parent_sets: list[set[str]] = []

    for report in reports:
        if report.dep.type == DependencyType.TRANSITIVE:
            parent_dep_names = get_uppermost_parent_deps(
                pipenv_graph_output,
                report.dep.name,
                direct_deps_names,
            )
            parent_deps = [direct_deps_dict[name] for name in parent_dep_names]
            parent_names_set = set(parent_dep_names)

            if not any(parent_names_set.issubset(existing_set) for existing_set in existing_parent_sets):
                existing_parent_sets.append(parent_names_set)
                report.dep.parent_deps = parent_deps

    return reports


def get_uppermost_parent_deps(
    pipenv_graph_output: str,
    dependency_name: str,
    direct_deps_names: set[str],
) -> list[str]:
    """
    Identifies the uppermost parent dependencies of a given transitive dependency.
    Returns a list of parent dependency names as strings.
    """
    dependencies_graph = json.loads(pipenv_graph_output)
    reverse_dependency_graph = {}

    for dep in dependencies_graph:
        dep_name = dep.get("package", {}).get("key", "").lower()
        for sub_dep in dep.get("dependencies", []):
            sub_dep_name = sub_dep.get("key", "").lower()
            if sub_dep_name not in reverse_dependency_graph:
                reverse_dependency_graph[sub_dep_name] = [dep_name]
            else:
                reverse_dependency_graph[sub_dep_name].append(dep_name)

    def find_uppermost_parents(package: str, seen: set[str]) -> list[str]:
        if package not in reverse_dependency_graph or package in seen:
            return []
        seen.add(package)
        uppermost_parents = []
        for parent in reverse_dependency_graph[package]:
            if parent in direct_deps_names:
                uppermost_parents.append(parent)
            else:
                uppermost_parents.extend(find_uppermost_parents(parent, seen))
        return uppermost_parents

    return find_uppermost_parents(dependency_name, set())
