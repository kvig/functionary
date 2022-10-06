""" Build serializers """
from rest_framework import serializers

from builder.models import Build
from core.models import Package, User


class SimplePackageSerializer(serializers.ModelSerializer):
    """Serializer that returns the ID and a name field for the object."""

    class Meta:
        model = Package
        fields = ["id", "name"]


class SimpleUserSerializer(serializers.ModelSerializer):
    """Serializer that returns the ID and a name field for the object."""

    class Meta:
        model = User
        fields = ["id", "username"]


class BuildSerializer(serializers.ModelSerializer):
    """Basic serializer for the Build model"""

    creator = SimpleUserSerializer(many=False, read_only=True)
    package = SimplePackageSerializer(many=False, read_only=True)

    class Meta:
        model = Build
        fields = "__all__"
