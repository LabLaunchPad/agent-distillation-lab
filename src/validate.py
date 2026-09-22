"""Shot 2: stdlib-only v1 schema validation (no jsonschema dep)."""
import json
import os

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(name):
    with open(os.path.join(_HERE, "schemas", name), encoding="utf-8") as f:
        return json.load(f)


def _check(value, schema, path="root"):
    t = schema.get("type")
    if isinstance(t, list):
        if value is None and "null" in t:
            return
        t = next(x for x in t if x != "null")
    if t == "object":
        if not isinstance(value, dict):
            raise ValueError(f"{path}: expected object")
        for k in schema.get("required", []):
            if k not in value:
                raise ValueError(f"{path}: missing required '{k}'")
        for k, sub in schema.get("properties", {}).items():
            if k in value:
                _check(value[k], sub, f"{path}.{k}")
        if schema.get("properties", {}).get("schema_version", {}).get("const") and \
                value.get("schema_version") != "1.0":
            raise ValueError(f"{path}: schema_version must be '1.0'")
    elif t == "array":
        if not isinstance(value, list):
            raise ValueError(f"{path}: expected array")
        for i, v in enumerate(value):
            _check(v, schema.get("items", {}), f"{path}[{i}]")
    elif t == "string":
        if not isinstance(value, str):
            raise ValueError(f"{path}: expected string")
        if schema.get("const") is not None and value != schema["const"]:
            raise ValueError(f"{path}: must equal '{schema['const']}'")
        if schema.get("enum") is not None and value not in schema["enum"]:
            raise ValueError(f"{path}: must be one of {schema['enum']}")
    elif t == "boolean":
        if not isinstance(value, bool):
            raise ValueError(f"{path}: expected boolean")


def validate_trajectory(obj):
    _check(obj, _load("trajectory.v1.json"))
    return True


def validate_artifact(obj):
    _check(obj, _load("artifact.v1.json"))
    return True


def validate_provenance(obj):
    _check(obj, _load("provenance.v1.json"))
    return True


def validate_eval(obj):
    _check(obj, _load("eval.v1.json"))
    return True
