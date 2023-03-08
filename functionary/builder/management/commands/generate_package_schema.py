import json
import pathlib

from django.core.management.base import BaseCommand
from drf_jsonschema_serializer import to_jsonschema

from builder.api.v1.serializers.package_definition import (
    PackageDefinitionWithVersionSerializer,
)


class Command(BaseCommand):
    help = "Generates the schema.json used to validate the package.yaml"

    def add_arguments(self, parser):
        parser.add_argument(
            "-o",
            "--output",
            action="store",
            dest="schema_file",
            type=pathlib.Path,
            nargs=1,
            help="Output file to write the schema to",
        )

    def handle(self, *args, **options):
        json_schema = to_jsonschema(PackageDefinitionWithVersionSerializer())
        json_schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        json_schema["$id"] = "https://functionary/package.yaml"
        schema_string = json.dumps(json_schema, indent=4)

        if not options["schema_file"]:
            print(schema_string)
        else:
            schema_file = options["schema_file"]
            print(f"Saving to: {schema_file}")
            try:
                schema_file.parent.mkdir(parents=True, exist_ok=True)
                with schema_file.open("w") as sf:
                    sf.write(schema_string)
            except Exception as e:
                print(f"Unable to write to {schema_file}: {e}")
