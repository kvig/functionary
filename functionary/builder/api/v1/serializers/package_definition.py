""" Serializers for defining a package """
from rest_framework import serializers

from core.utils.parameter import PARAMETER_TYPE_CHOICES

LANGUAGES = [("python", "Python"), ("javascript", "JavaScript")]
RETURN_TYPE_CHOICES = PARAMETER_TYPE_CHOICES[:]


class ParameterOptionSerializer(serializers.Serializer):
    name = serializers.CharField()

    # TODO: This should probably preserve numeric values rather than convert
    #       them to a string
    value = serializers.CharField()


class ParameterSerializer(serializers.Serializer):
    """Serializer for parameter description"""

    name = serializers.CharField()
    display_name = serializers.CharField(required=False)
    description = serializers.CharField(required=False)

    type = serializers.ChoiceField(choices=PARAMETER_TYPE_CHOICES, required=True)

    required = serializers.BooleanField(default=False)
    options = ParameterOptionSerializer(many=True, required=False)

    # TODO: This should probably preserve numeric values rather than convert
    #       them to a string
    default = serializers.CharField(required=False)


class FunctionSerializer(serializers.Serializer):
    """Serializer for function description"""

    name = serializers.CharField()
    display_name = serializers.CharField(required=False)
    summary = serializers.CharField(max_length=128, required=False)
    description = serializers.CharField(required=False)
    variables = serializers.ListField(
        child=serializers.CharField(max_length=256, required=False), required=False
    )
    parameters = ParameterSerializer(many=True)
    return_type = serializers.ChoiceField(choices=RETURN_TYPE_CHOICES, required=False)


class PackageDefinitionSerializer(serializers.Serializer):
    """Serializer for package description"""

    name = serializers.CharField()
    display_name = serializers.CharField(required=False)
    summary = serializers.CharField(max_length=128, required=False)
    description = serializers.CharField(required=False)
    language = serializers.ChoiceField(choices=LANGUAGES, required=False)
    filename = serializers.CharField(required=False, read_only=True)
    environment = serializers.DictField(
        child=serializers.CharField(), required=False, read_only=True
    )
    functions = FunctionSerializer(many=True)


class PackageDefinitionWithVersionSerializer(serializers.Serializer):
    """Serializer for full package.yaml"""

    version = serializers.CharField()
    package = PackageDefinitionSerializer()
