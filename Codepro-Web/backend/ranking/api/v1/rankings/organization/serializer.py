from rest_framework import serializers

class OrganizationRankingItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    short_name = serializers.CharField()
    members_count = serializers.IntegerField()
    total_solved = serializers.IntegerField()
    avg_rating = serializers.FloatField()
    top_member = serializers.CharField(allow_null=True)