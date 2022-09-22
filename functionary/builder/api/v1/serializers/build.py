""" Build serializers """
from rest_framework import serializers

from builder.models import Build


class BuildSerializer(serializers.ModelSerializer):
    """Basic serializer for the Build model"""

    creator = serializers.SlugRelatedField(
        many=False, read_only=True, slug_field="username"
    )
    package = serializers.SlugRelatedField(
        many=False, read_only=True, slug_field="name"
    )

    class Meta:
        model = Build
        fields = ["id", "created_at", "updated_at", "package", "creator", "status"]
